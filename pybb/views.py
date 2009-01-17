import math

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import connection

from pybb.util import render_to, paged, build_form, quote_text
from pybb.models import Category, Forum, Topic, Post, Profile, PrivateMessage
from pybb.forms import AddPostForm, EditProfileForm, EditPostForm, UserSearchForm, CreatePMForm

def index_ctx(request):
    quick = {'posts': Post.objects.count(),
             'topics': Topic.objects.count(),
             'users': User.objects.count(),
             'last_topics': Topic.objects.all().select_related()[:settings.PYBB_QUICK_TOPICS_NUMBER],
             'last_posts': Post.objects.order_by('-created').select_related()[:settings.PYBB_QUICK_POSTS_NUMBER],
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
    category = Category.objects.get(pk=category_id)
    quick = {'posts': category.posts.count(),
             'topics': category.topics.count(),
             'last_topics': category.topics.select_related()[:settings.PYBB_QUICK_TOPICS_NUMBER],
             'last_posts': category.posts.order_by('-created').select_related()[:settings.PYBB_QUICK_POSTS_NUMBER],
             }
    return {'category': category,
            'quick': quick,
            }
show_category = render_to('pybb/category.html')(show_category_ctx)


@paged('topics', settings.PYBB_FORUM_PAGE_SIZE)
def show_forum_ctx(request, forum_id):
    forum = Forum.objects.get(pk=forum_id)
    topics = forum.topics.filter(sticky=False).select_related()
    quick = {'posts': forum.posts.count(),
             'topics': forum.topics.count(),
             'last_topics': forum.topics.all().select_related()[:settings.PYBB_QUICK_TOPICS_NUMBER],
             'last_posts': forum.posts.order_by('-created').select_related()[:settings.PYBB_QUICK_POSTS_NUMBER],
             }

    return {'forum': forum,
            'topics': topics,
            'sticky_topics': forum.topics.filter(sticky=True),
            'quick': quick,
            'paged_qs': topics,
            }
show_forum = render_to('pybb/forum.html')(show_forum_ctx)

    
@paged('posts', settings.PYBB_TOPIC_PAGE_SIZE)
def show_topic_ctx(request, topic_id):
    topic = Topic.objects.select_related().get(pk=topic_id)
    topic.views += 1
    topic.save()


    if request.user.is_authenticated():
        topic.update_read(request.user)

    posts = topic.posts.all().select_related()
    if settings.PYBB_FREEZE_FIRST_POST:
        first_post = topic.posts.order_by('created')[0]
    else:
        first_post = None
    last_post = topic.posts.order_by('-created')[0]

    profiles = Profile.objects.filter(user__pk__in=set(x.user.id for x in posts))
    profiles = dict((x.user_id, x) for x in profiles)
    
    for post in posts:
        post.user.pybb_profile = profiles[post.user.id]

    initial = {}
    if request.user.is_authenticated():
        initial = {'markup': request.user.pybb_profile.markup}
    form = AddPostForm(topic=topic, initial=initial)

    moderator = request.user.is_superuser or\
        request.user in topic.forum.moderators.all()
    if request.user.is_authenticated() and request.user in topic.subscribers.all():
        subscribed = True
    else:
        subscribed = False

    return {'topic': topic,
            'last_post': last_post,
            'first_post': first_post,
            'form': form,
            'moderator': moderator,
            'subscribed': subscribed,
            'paged_qs': posts,
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

    if topic and topic.closed:
        return HttpResponseRedirect(topic.get_absolute_url())

    try:
        quote_id = int(request.GET.get('quote_id'))
    except TypeError:
        quote = ''
    else:
        post = get_object_or_404(Post, pk=quote_id)
        quote = quote_text(post.body_text, request.user.pybb_profile.markup)

    ip = request.META.get('REMOTE_ADDR', '')
    form = build_form(AddPostForm, request, topic=topic, forum=forum,
                      user=request.user, ip=ip,
                      initial={'markup': request.user.pybb_profile.markup, 'body': quote})

    if form.is_valid():
        post = form.save();
        return HttpResponseRedirect(post.get_absolute_url())

    return {'form': form,
            'topic': topic,
            'forum': forum,
            }
add_post = render_to('pybb/add_post.html')(add_post_ctx)


def user_ctx(request, username):
    user = get_object_or_404(User, username=username)
    topic_count = Topic.objects.filter(user=user).count()
    return {'profile': user,
            'topic_count': topic_count,
            }
user = render_to('pybb/user.html')(user_ctx)


def show_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    count = post.topic.posts.filter(created__lt=post.created).count() + 1
    page = math.ceil(count / float(settings.PYBB_TOPIC_PAGE_SIZE))
    url = '%s?page=%d#post-%d' % (reverse('pybb_topic', args=[post.topic.id]), page, post.id)
    return HttpResponseRedirect(url)


@login_required
def edit_profile_ctx(request):
    form = build_form(EditProfileForm, request, instance=request.user.pybb_profile)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('pybb_edit_profile'))
    return {'form': form,
            'profile': request.user.pybb_profile,
            }
edit_profile = render_to('pybb/edit_profile.html')(edit_profile_ctx)

    
@login_required
def edit_post_ctx(request, post_id):
    from pybb.templatetags.pybb_extras import pybb_editable_by

    post = get_object_or_404(Post, pk=post_id)
    if not pybb_editable_by(post, request.user):
        return HttpResponseRedirect(post.get_absolute_url())

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
    topic = post.topic

    allowed = False
    if request.user.is_superuser or\
        request.user in post.topic.forum.moderators.all() or \
        (post.user == request.user and post == last_post):
        allowed = True

    if not allowed:
        return HttpResponseRedirect(post.get_absolute_url())

    topic = post.topic
    forum = post.topic.forum
    post.delete()

    try:
        Topic.objects.get(pk=topic.id)
    except Topic.DoesNotExist:
        return HttpResponseRedirect(forum.get_absolute_url())
    else:
        return HttpResponseRedirect(topic.get_absolute_url())
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


@render_to('pybb/users.html')
@paged('users', settings.PYBB_USERS_PAGE_SIZE)
def users_ctx(request):
    users = User.objects.order_by('username')
    form = UserSearchForm(request.GET)
    users = form.filter(users)
    return {'paged_qs': users,
            'form': form,
            }
users = paged('users', settings.PYBB_USERS_PAGE_SIZE)(users_ctx)


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
def create_pm_ctx(request):
    recipient = request.GET.get('recipient', '')
    form = build_form(CreatePMForm, request, user=request.user,
                      initial={'markup': request.user.pybb_profile.markup,
                               'recipient': recipient})

    if form.is_valid():
        post = form.save();
        return HttpResponseRedirect(reverse('pybb_pm_outbox'))

    return {'form': form,
            }
create_pm = render_to('pybb/pm/create_pm.html')(create_pm_ctx)


@login_required
def pm_outbox_ctx(request):
    messages = PrivateMessage.objects.filter(src_user=request.user)
    return {'messages': messages,
            }
pm_outbox = render_to('pybb/pm/outbox.html')(pm_outbox_ctx)


@login_required
def pm_inbox_ctx(request):
    messages = PrivateMessage.objects.filter(dst_user=request.user)
    return {'messages': messages,
            }
pm_inbox = render_to('pybb/pm/inbox.html')(pm_inbox_ctx)


@login_required
def show_pm_ctx(request, pm_id):
    msg = get_object_or_404(PrivateMessage, pk=pm_id)
    if not request.user in [msg.dst_user, msg.src_user]:
        return HttpRedirectException('/')
    if request.user == msg.dst_user:
        inbox = True
        post_user = msg.src_user
    else:
        inbox = False
        post_user = msg.dst_user
    return {'msg': msg,
            'inbox': inbox,
            'post_user': post_user,
            }
show_pm = render_to('pybb/pm/message.html')(show_pm_ctx)
