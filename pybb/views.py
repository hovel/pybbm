# coding: utf-8
import math
import re
from datetime import datetime
from markdown import Markdown
from pybb.markups import mypostmarkup
try:
    import pytils
    pytils_enabled = True
except ImportError:
    pytils_enabled = False

from django.shortcuts import get_object_or_404, get_list_or_404
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound, Http404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import connection
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext

from pybb.util import   render_to, paged, build_form, quote_text, paginate,\
                        set_language, ajax, urlize
from pybb.models import Category, Forum, Topic, Post, Profile, \
                        Attachment, MARKUP_CHOICES
from pybb.forms import  AddPostForm, EditPostForm, EditHeadPostForm, \
                        EditProfileForm, UserSearchForm
from pybb import settings as pybb_settings
from pybb.orm import load_related


def index_ctx(request):
    quick = {'posts': Post.objects.count(),
             'topics': Topic.objects.count(),
             'users': User.objects.count(),
             'last_topics': Topic.objects.all().select_related()[:pybb_settings.QUICK_TOPICS_NUMBER],
             'last_posts': Post.objects.order_by('-created').select_related()[:pybb_settings.QUICK_POSTS_NUMBER],
             }

    cats = {}
    forums = {}

    for forum in Forum.objects.all().select_related():
        cat = cats.setdefault(forum.category.id,
            {'cat': forum.category, 'forums': []})
        cat['forums'].append(forum)
        forums[forum.id] = forum

    cmpdef = lambda a, b: cmp(a['cat'].position, b['cat'].position)
    cats = sorted(cats.values(), cmpdef)

    return {'cats': cats,
            'quick': quick,
            }


index = render_to('pybb/index.html')(index_ctx)


def show_category_ctx(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    quick = {'posts': category.posts.count(),
             'topics': category.topics.count(),
             'last_topics': category.topics.select_related()[:pybb_settings.QUICK_TOPICS_NUMBER],
             'last_posts': category.posts.order_by('-created').select_related()\
                [:pybb_settings.QUICK_POSTS_NUMBER],
             }
    return {'category': category,
            'quick': quick,
            }


show_category = render_to('pybb/category.html')(show_category_ctx)


def show_forum_ctx(request, forum_id):
    forum = get_object_or_404(Forum, pk=forum_id)

    quick = {'posts': forum.post_count,
             'topics': forum.topics.count(),
             'last_topics': forum.topics.all().select_related()[:pybb_settings.QUICK_TOPICS_NUMBER],
             'last_posts': forum.posts.order_by('-created').select_related()\
                [:pybb_settings.QUICK_POSTS_NUMBER],
             }

    topics = forum.topics.order_by('-sticky', '-updated').select_related()
    page, paginator = paginate(topics, request, pybb_settings.FORUM_PAGE_SIZE)

    return {'forum': forum,
            'topics': page.object_list,
            'quick': quick,
            'page': page,
            'paginator': paginator,
            }


show_forum = render_to('pybb/forum.html')(show_forum_ctx)


def show_topic_ctx(request, topic_id):
    try:
        topic = Topic.objects.select_related().get(pk=topic_id)
    except Topic.DoesNotExist:
        raise Http404()
    topic.views += 1
    topic.save()


    if request.user.is_authenticated():
        topic.update_read(request.user)

    if pybb_settings.FREEZE_FIRST_POST:
        first_post = topic.posts.order_by('created')[0]
    else:
        first_post = None
    last_post = topic.posts.order_by('-created')[0]

    initial = {}
    if request.user.is_authenticated():
        current_markup = request.user.pybb_profile.markup
        initial = {'markup': current_markup}
    else:
        current_markup = pybb_settings.DEFAULT_MARKUP
    form = AddPostForm(topic=topic, initial=initial)

    moderator = (request.user.is_superuser or
                 request.user in topic.forum.moderators.all())
    subscribed = (request.user.is_authenticated() and
                  request.user in topic.subscribers.all())

    posts = topic.posts.all().select_related()
    page, paginator = paginate(posts, request, pybb_settings.TOPIC_PAGE_SIZE,
                               total_count=topic.post_count)

    profiles = Profile.objects.filter(user__pk__in=
        set(x.user.id for x in page.object_list))
    profiles = dict((x.user_id, x) for x in profiles)

    for post in page.object_list:
        post.user.pybb_profile = profiles[post.user.id]

    load_related(page.object_list, Attachment.objects.all(), 'post')

    return {'topic': topic,
            'last_post': last_post,
            'first_post': first_post,
            'form': form,
            'moderator': moderator,
            'subscribed': subscribed,
            'posts': page.object_list,
            'page': page,
            'paginator': paginator,
            'form_url': reverse('pybb_add_post', args=[topic.id]),
            'current_markup': current_markup,
            }


show_topic = render_to('pybb/topic.html')(show_topic_ctx)


@login_required
def add_post_ctx(request, forum_id, topic_id):
    forum = None
    topic = None

    if forum_id:
        forum = get_object_or_404(Forum, pk=forum_id)
    elif topic_id:
        topic = get_object_or_404(Topic, pk=topic_id)

    if (topic and topic.closed) or request.user.pybb_profile.is_banned():
        return HttpResponseRedirect(topic.get_absolute_url())

    try:
        quote_id = int(request.GET.get('quote_id'))
    except TypeError:
        quote = ''
    else:
        post = get_object_or_404(Post, pk=quote_id)
        quote = quote_text(post.body_text,
                           request.user.pybb_profile.markup,
                           post.user.username)

    ip = request.META.get('REMOTE_ADDR', '')
    form = build_form(AddPostForm, request, topic=topic, forum=forum,
                      user=request.user, ip=ip, initial={'body': quote})

    if topic and form.is_valid():
        last_post = topic.last_post
        time_diff = (datetime.now() - last_post.created).seconds / 60
        timeout = pybb_settings.POST_AUTOJOIN_TIMEOUT
        if last_post.user == request.user and time_diff < timeout:
            if request.LANGUAGE_CODE.startswith('ru') and pytils_enabled:
                join_message = u"Добавлено спустя %s %s" % (time_diff,
                                    pytils.numeral.choose_plural(time_diff,
                                    (u"минуту", u"минуты", u"минут")))
            else:
                join_message = ungettext(u"Added after %s minute",
                                         u"Added after %s minutes",
                                         time_diff) % time_diff

            if last_post.markup == "bbcode":
                join_message = "[b]%s[/b]" % join_message
            elif last_post.markup == "markdown":
                join_message = "**%s**" % join_message

            last_post.body += u"\n\n%s:\n\n%s" % (join_message,
                                                form.cleaned_data["body"])
            last_post.updated = datetime.now()
            last_post.save()
            return HttpResponseRedirect(last_post.get_absolute_url())

    if form.is_valid():
        post = form.save();
        return HttpResponseRedirect(post.get_absolute_url())

    if topic:
        form_url = reverse('pybb_add_post', args=[topic.id])
    else:
        form_url = reverse('pybb_add_topic', args=[forum.id])

    current_markup = request.user.pybb_profile.markup

    return {'form': form,
            'topic': topic,
            'forum': forum,
            'form_url': form_url,
            'current_markup': current_markup,
            }


add_post = render_to('pybb/add_post.html')(add_post_ctx)


def user_ctx(request, username):
    user = get_object_or_404(User, username=username)
    topic_count = Topic.objects.filter(user=user).count()
    return {'profile': user,
            'topic_count': topic_count,
            }


user = render_to('pybb/user.html')(user_ctx)


def user_topics_ctx(request, username):
    user = get_object_or_404(User, username=username)

    topics = Topic.objects.filter(user=user).order_by('-created')

    page, paginator = paginate(topics, request, pybb_settings.TOPIC_PAGE_SIZE)
    return {'profile': user,
            'page': page,
            'paginator': paginator,
            'list': page.object_list,
            }


user_topics = render_to('pybb/user_topics.html')(user_topics_ctx)


# TODO: create template for that view
# which should be looking like topic template
#
#def user_posts_ctx(request, username):
    #user = get_object_or_404(User, username=username)

    #posts = Post.objects.filter(user=user).order_by('-created')

    #page, paginator = paginate(posts, request, pybb_settings.TOPIC_PAGE_SIZE)
    #return {'profile': user,
            #'page': page,
            #'paginator': paginator,
            #'list': page.object_list,
            #}


#user_posts = render_to('pybb/user_posts.html')(user_posts_ctx)


def show_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    count = post.topic.posts.filter(created__lt=post.created).count() + 1
    page = math.ceil(count / float(pybb_settings.TOPIC_PAGE_SIZE))
    url = '%s?page=%d#post-%d' % (reverse('pybb_topic', args=[post.topic.id]), page, post.id)
    return HttpResponseRedirect(url)


@login_required
def edit_profile_ctx(request):
    form = build_form(EditProfileForm, request, instance=request.user.pybb_profile)
    if form.is_valid():
        profile = form.save()
        set_language(request, profile.language)
        return HttpResponseRedirect(reverse('pybb_edit_profile'))
    return {'form': form,
            'profile': request.user.pybb_profile,
            }


edit_profile = render_to('pybb/edit_profile.html')(edit_profile_ctx)


@login_required
def edit_post_ctx(request, post_id):
    from pybb.templatetags.pybb_extras import pybb_editable_by

    post = get_object_or_404(Post, pk=post_id)

    if not pybb_editable_by(post, request.user) \
    or request.user.pybb_profile.is_banned():
        return HttpResponseRedirect(post.get_absolute_url())

    head_post_id = post.topic.posts.order_by('created')[0].id
    if post.id == head_post_id:
        form = build_form(EditHeadPostForm, request, instance=post,
                          initial={'title': post.topic.name})
    else:
        form = build_form(EditPostForm, request, instance=post)

    if form.is_valid():
        post = form.save()
        return HttpResponseRedirect(post.get_absolute_url())

    return {'form': form,
            'post': post,
            }


edit_post = render_to('pybb/edit_post.html')(edit_post_ctx)


@login_required
def stick_topic(request, topic_id):
    from pybb.templatetags.pybb_extras import pybb_moderated_by

    topic = get_object_or_404(Topic, pk=topic_id)
    if pybb_moderated_by(topic, request.user):
        if not topic.sticky:
            topic.sticky = True
            topic.save()
    return HttpResponseRedirect(topic.get_absolute_url())


@login_required
def unstick_topic(request, topic_id):
    from pybb.templatetags.pybb_extras import pybb_moderated_by

    topic = get_object_or_404(Topic, pk=topic_id)
    if pybb_moderated_by(topic, request.user):
        if topic.sticky:
            topic.sticky = False
            topic.save()
    return HttpResponseRedirect(topic.get_absolute_url())


@login_required
def delete_post_ctx(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    last_post = post.topic.posts.order_by('-created')[0]

    allowed = False
    if request.user.is_superuser or\
        request.user in post.topic.forum.moderators.all() or \
        (post.user == request.user and post == last_post):
        allowed = True

    if not allowed:
        return HttpResponseRedirect(post.get_absolute_url())

    if 'POST' == request.method:
        topic = post.topic
        forum = post.topic.forum
        post.delete()

        try:
            Topic.objects.get(pk=topic.id)
        except Topic.DoesNotExist:
            return HttpResponseRedirect(forum.get_absolute_url())
        else:
            return HttpResponseRedirect(topic.get_absolute_url())
    else:
        return {'post': post,
                }


delete_post = render_to('pybb/delete_post.html')(delete_post_ctx)


@login_required
def close_topic(request, topic_id):
    from pybb.templatetags.pybb_extras import pybb_moderated_by

    topic = get_object_or_404(Topic, pk=topic_id)
    if pybb_moderated_by(topic, request.user):
        if not topic.closed:
            topic.closed = True
            topic.save()
    return HttpResponseRedirect(topic.get_absolute_url())



@login_required
def open_topic(request, topic_id):
    from pybb.templatetags.pybb_extras import pybb_moderated_by

    topic = get_object_or_404(Topic, pk=topic_id)
    if pybb_moderated_by(topic, request.user):
        if topic.closed:
            topic.closed = False
            topic.save()
    return HttpResponseRedirect(topic.get_absolute_url())



@login_required
@render_to('pybb/merge_topics.html')
def merge_topics (request):
    from pybb.templatetags.pybb_extras import pybb_moderated_by

    topics_ids = request.GET.getlist('topic')
    topics = get_list_or_404(Topic, pk__in=topics_ids)

    for topic in topics:
        if not pybb_moderated_by(topic, request.user):
            # TODO: show error message: no permitions for edit this topic
            return HttpResponseRedirect(topic.get_absolute_url())

    if len(topics) < 2:
        return {'topics': topics}

    posts = get_list_or_404(Post, topic__in=topics_ids)
    main = int(request.POST.get("main", 0))

    if main and main in (topic.id for topic in topics):
        for topic in topics:
            if topic.id == main:
                main_topic = topic

        for post in posts:
            if post.topic_id != main_topic.id:
                post.topic = main_topic
                post.save()

        main_topic.update_post_count()
        main_topic.forum.update_post_count()

        for topic in topics:
            if topic.id != main:
                forum = topic.forum
                topic.delete()
                forum.update_post_count()

        return HttpResponseRedirect(main_topic.get_absolute_url())
    return {'posts': posts, 'topics': topics, 'topic': topics[0]}



@render_to('pybb/users.html')
def users_ctx(request):
    users = User.objects.order_by('username')
    form = UserSearchForm(request.GET)
    users = form.filter(users)

    page, paginator = paginate(users, request, pybb_settings.USERS_PAGE_SIZE)

    return {'users': page.object_list,
            'page': page,
            'paginator': paginator,
            'form': form,
            }


users = render_to('pybb/users.html')(users_ctx)


@login_required
def delete_subscription(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    topic.subscribers.remove(request.user)
    if 'from_topic' in request.GET:
        return HttpResponseRedirect(reverse('pybb_topic', args=[topic.id]))
    else:
        return HttpResponseRedirect(reverse('pybb_edit_profile'))


@login_required
def add_subscription(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    topic.subscribers.add(request.user)
    return HttpResponseRedirect(reverse('pybb_topic', args=[topic.id]))


@login_required
def show_attachment(request, hash):
    attachment = get_object_or_404(Attachment, hash=hash)
    file_obj = file(attachment.get_absolute_path())
    # without it mod_python chokes with error that content_type must be string
    return HttpResponse(file_obj, content_type=str(attachment.content_type))


@login_required
@ajax
def post_ajax_preview(request):
    content = request.POST.get('content')
    markup = request.POST.get('markup')

    if not markup in dict(MARKUP_CHOICES).keys():
        return {'error': 'Invalid markup'}

    if not content:
        return {'content': ''}

    if markup == 'bbcode':
        html = mypostmarkup.markup(content, auto_urls=False)
    elif markup == 'markdown':
        instance = Markdown(safe_mode='escape')
        html = unicode(instance.convert(content))

    html = urlize(html)

    return {'content': html,
            }
