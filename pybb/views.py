# coding: utf-8
import math
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.expressions import F

from django.shortcuts import get_object_or_404, get_list_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from pybb.util import  paginate
from pybb.models import Category, Forum, Topic, Post, Attachment, TopicReadTracker, ForumReadTracker
from pybb.forms import  PostForm, AdminPostForm, EditProfileForm, UserSearchForm

import settings

from annoying.decorators import render_to, ajax_request

@render_to('pybb/index.html')
def index(request):
    categories = Category.objects.all()
    return {'categories': categories, }

@render_to('pybb/index.html')
def show_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    return {'categories': [category, ]}

@render_to('pybb/forum.html')
def show_forum(request, forum_id):
    forum = get_object_or_404(Forum, pk=forum_id)
    topics = forum.topics.order_by('-sticky', '-updated').select_related()
    page, paginator = paginate(topics, request, settings.PYBB_FORUM_PAGE_SIZE)
    return {'forum': forum,
            'page': page,
    }

@render_to('pybb/topic.html')
def show_topic(request, topic_id):
    try:
        topic = Topic.objects.select_related('forum').get(pk=topic_id)
    except Topic.DoesNotExist:
        raise Http404()

    topic.views += 1
    topic.save()

    form = False
    if request.user.is_authenticated():
        # Do read/unread mark
        try:
            forum_mark = ForumReadTracker.objects.get(forum=topic.forum, user=request.user)
        except ObjectDoesNotExist:
            forum_mark = None
        if (forum_mark is None) or (forum_mark.time_stamp < topic.updated):
            # Mark topic as readed
            topic_mark, new = TopicReadTracker.objects.get_or_create(topic=topic, user=request.user)
            if not new:
                topic_mark.save()
            # Check, if there are any unread topics in forum
            try:
                qs = Topic.objects.filter(
                        topicreadtracker__user=request.user,
                        topicreadtracker__time_stamp__lt=F('updated'),
                        forum=topic.forum,
                        )
                if forum_mark:
                    qs = qs.filter(topicreadtracker__time_stamp__gte=forum_mark.time_stamp)
                qs[0:1].get()
            except Topic.DoesNotExist:
                # Clear all topic marks for this forum, mark forum as readed
                TopicReadTracker.objects.filter(
                        user=request.user,
                        topic__forum=topic.forum
                        ).delete()
                forum_mark, new = ForumReadTracker.objects.get_or_create(forum=topic.forum,user=request.user)
                if new:
                    forum_mark.save()

        # Set is_moderator / is_subscribed properties
        request.user.is_moderator = request.user.is_superuser or (request.user in topic.forum.moderators.all())
        request.user.is_subscribed = request.user in topic.subscribers.all()
        if request.user.is_superuser:
            form = AdminPostForm(initial={'login': request.user.username}, topic=topic)
        else:
            form = PostForm(topic=topic)

    if settings.PYBB_FREEZE_FIRST_POST:
        first_post = topic.head
    else:
        first_post = None

    posts = topic.posts.all().select_related('user', 'user__pybb_profile')
    # TODO: Here could be gotcha
    # If topic.post_count is broken then strange effect could be possible!
    page, paginator = paginate(posts, request, settings.PYBB_TOPIC_PAGE_SIZE,
                               total_count=topic.post_count)

    return {'topic': topic,
            'first_post': first_post,
            'form': form,
            'posts': page.object_list,
            'page': page,
    }


@login_required
@render_to('pybb/add_post.html')
def add_post(request, forum_id, topic_id):
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
        quote = settings.PYBB_QUOTE_ENGINES[request.user.pybb_profile.markup](post.body, post.user.username)

    ip = request.META.get('REMOTE_ADDR', '')
    form_kwargs = dict(topic=topic, forum=forum, user=request.user,
                       ip=ip, initial={'body': quote})
    if request.user.is_superuser:
        AForm = AdminPostForm
        form_kwargs['initial']['login'] = request.user.username
    else:
        AForm = PostForm
    if request.method == 'POST':
        form = AForm(request.POST, request.FILES, **form_kwargs)
    else:
        form = AForm(**form_kwargs)

    if form.is_valid():
        post = form.save()
        return HttpResponseRedirect(post.get_absolute_url())

    return {'form': form,
            'topic': topic,
            'forum': forum,
    }

@render_to('pybb/user.html')
def user(request, username):
    profile = get_object_or_404(User, username=username)
    topic_count = Topic.objects.filter(user=profile).count()
    return {
        'profile': profile,
        'topic_count': topic_count,
    }

@render_to('pybb/user_topics.html')
def user_topics(request, username):
    profile = get_object_or_404(User, username=username)
    topics = Topic.objects.filter(user=profile).order_by('-created')
    page, paginator = paginate(topics, request, settings.PYBB_TOPIC_PAGE_SIZE)
    return {
        'profile': profile,
        'page': page,
    }


def show_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    count = post.topic.posts.filter(created__lt=post.created).count() + 1
    page = math.ceil(count / float(settings.PYBB_TOPIC_PAGE_SIZE))
    url = '%s?page=%d#post-%d' % (reverse('pybb_topic', args=[post.topic.id]), page, post.id)
    return HttpResponseRedirect(url)


@login_required
@render_to('pybb/edit_profile.html')
def edit_profile(request):
    form_kwargs = dict(instance=request.user.pybb_profile)
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, **form_kwargs)
    else:
        form = EditProfileForm(**form_kwargs)

    if form.is_valid():
        profile = form.save()
        profile.save()
        return HttpResponseRedirect(reverse('pybb_edit_profile'))

    return {'form': form,
            'profile': request.user.pybb_profile,
    }


@login_required
@render_to('pybb/edit_post.html')
def edit_post(request, post_id):
    from pybb.templatetags.pybb_tags import pybb_editable_by

    post = get_object_or_404(Post, pk=post_id)

    if not pybb_editable_by(post, request.user)\
    or request.user.pybb_profile.is_banned():
        return HttpResponseRedirect(post.get_absolute_url())

    if request.user.is_superuser:
        form_class = AdminPostForm
    else:
        form_class = PostForm

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=post)
    else:
        form = form_class(instance=post)

    if form.is_valid():
        post = form.save()
        return HttpResponseRedirect(post.get_absolute_url())

    return {'form': form,
            'post': post,
    }


@login_required
def stick_topic(request, topic_id):
    from pybb.templatetags.pybb_tags import pybb_topic_moderated_by

    topic = get_object_or_404(Topic, pk=topic_id)
    if pybb_topic_moderated_by(topic, request.user):
        if not topic.sticky:
            topic.sticky = True
            topic.save()
    return HttpResponseRedirect(topic.get_absolute_url())


@login_required
def unstick_topic(request, topic_id):
    from pybb.templatetags.pybb_tags import pybb_topic_moderated_by

    topic = get_object_or_404(Topic, pk=topic_id)
    if pybb_topic_moderated_by(topic, request.user):
        if topic.sticky:
            topic.sticky = False
            topic.save()
    return HttpResponseRedirect(topic.get_absolute_url())


@login_required
@render_to('pybb/delete_post.html')
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    last_post = post.topic.posts.order_by('-created')[0]

    allowed = False
    if request.user.is_superuser or\
       request.user in post.topic.forum.moderators.all() or\
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


@login_required
def close_topic(request, topic_id):
    from pybb.templatetags.pybb_tags import pybb_topic_moderated_by

    topic = get_object_or_404(Topic, pk=topic_id)
    if pybb_topic_moderated_by(topic, request.user):
        if not topic.closed:
            topic.closed = True
            topic.save()
    return HttpResponseRedirect(topic.get_absolute_url())


@login_required
def open_topic(request, topic_id):
    from pybb.templatetags.pybb_tags import pybb_topic_moderated_by

    topic = get_object_or_404(Topic, pk=topic_id)
    if pybb_topic_moderated_by(topic, request.user):
        if topic.closed:
            topic.closed = False
            topic.save()
    return HttpResponseRedirect(topic.get_absolute_url())


@login_required
@render_to('pybb/merge_topics.html')
def merge_topics(request):
    from pybb.templatetags.pybb_tags import pybb_topic_moderated_by

    topics_ids = request.GET.getlist('topic')
    topics = get_list_or_404(Topic, pk__in=topics_ids)

    for topic in topics:
        if not pybb_topic_moderated_by(topic, request.user):
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

    return {'posts': posts,
            'topics': topics,
            'topic': topics[0],
    }

@render_to('pybb/users.html')
def users(request):
    form = UserSearchForm(request.GET)
    all_users = form.filter(User.objects.order_by('username'))

    page, paginator = paginate(all_users, request, settings.PYBB_USERS_PAGE_SIZE)

    return {'page': page,
            'form': form,
    }


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
@ajax_request
def post_ajax_preview(request):
    if request.user.is_authenticated():
        content = request.POST.get('data')
        html = settings.PYBB_MARKUP_ENGINES[request.user.pybb_profile.markup](content)
        return HttpResponse(html)
    return Http404




