import math

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import connection

from pybb.util import render_to, paged, build_form
from pybb.models import Category, Forum, Topic, Post, Profile
from pybb.forms import AddPostForm, EditProfileForm, EditPostForm, UserSearchForm

@render_to('pybb/index.html')
def index(request):
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


@render_to('pybb/category.html')
def show_category(request, category_id):
    category = Category.objects.get(pk=category_id)
    quick = {'posts': category.posts.count(),
             'topics': category.topics.count(),
             'last_topics': category.topics.select_related()[:settings.PYBB_QUICK_TOPICS_NUMBER],
             'last_posts': category.posts.order_by('-created').select_related()[:settings.PYBB_QUICK_POSTS_NUMBER],
             }
    return {'category': category,
            'quick': quick,
            }


@render_to('pybb/forum.html')
@paged('topics', settings.PYBB_FORUM_PAGE_SIZE)
def show_forum(request, forum_id):
    forum = Forum.objects.get(pk=forum_id)
    topics = forum.topics.all().select_related()
    quick = {'posts': forum.posts.count(),
             'topics': forum.topics.count(),
             'last_topics': forum.topics.all().select_related()[:settings.PYBB_QUICK_TOPICS_NUMBER],
             'last_posts': forum.posts.order_by('-created').select_related()[:settings.PYBB_QUICK_POSTS_NUMBER],
             }
    return {'forum': forum,
            'sticky_topics': forum.topics.filter(sticky=True),
            'quick': quick,
            'paged_qs': topics,
            }

    
@render_to('pybb/topic.html')
@paged('posts', settings.PYBB_TOPIC_PAGE_SIZE)
def show_topic(request, topic_id):
    topic = Topic.objects.select_related().get(pk=topic_id)
    topic.views += 1
    topic.save()

    last_post = topic.posts.order_by('-created')[0]

    if request.user.is_authenticated():
        topic.update_read(request.user)

    posts = topic.posts.all().select_related()

    profiles = Profile.objects.filter(user__pk__in=set(x.user.id for x in posts))
    profiles = dict((x.id, x) for x in profiles)
    
    for post in posts:
        post.user.pybb_profile = profiles[post.user.id]

    initial = {}
    if request.user.is_authenticated():
        initial = {'markup': request.user.pybb_profile.markup}
    form = AddPostForm(topic=topic, initial=initial)
    moderator = request.user.is_superuser or\
        user in topic.forum.moderators.all()
    if request.user.is_authenticated() and request.user in topic.subscribers.all():
        subscribed = True
    else:
        subscribed = False
    return {'topic': topic,
            'last_post': last_post,
            'form': form,
            'moderator': moderator,
            'subscribed': subscribed,
            'paged_qs': posts,
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

    if topic and topic.closed:
        return HttpResponseRedirect(topic.get_absolute_url())

    ip = request.META.get('REMOTE_ADDR', '')
    form = build_form(AddPostForm, request, topic=topic, forum=forum,
                      user=request.user, ip=ip,
                      initial={'markup': request.user.pybb_profile.markup})

    if form.is_valid():
        post = form.save();
        return HttpResponseRedirect(post.get_absolute_url())

    return {'form': form,
            'topic': topic,
            'forum': forum,
            }


@render_to('pybb/user.html')
def user(request, username):
    user = get_object_or_404(User, username=username)
    topic_count = Topic.objects.filter(user=user).count()
    return {'profile': user,
            'topic_count': topic_count,
            }


def show_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    count = post.topic.posts.filter(created__lt=post.created).count() + 1
    page = math.ceil(count / float(settings.PYBB_TOPIC_PAGE_SIZE))
    url = '%s?page=%d#post-%d' % (reverse('topic', args=[post.topic.id]), page, post.id)
    return HttpResponseRedirect(url)


@login_required
@render_to('pybb/edit_profile.html')
def edit_profile(request):
    form = build_form(EditProfileForm, request, instance=request.user.pybb_profile)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('edit_profile'))
    return {'form': form,
            'profile': request.user.pybb_profile,
            }

    
@login_required
@render_to('pybb/edit_post.html')
def edit_post(request, post_id):
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
@render_to('pybb/delete_post.html')
def delete_post(request, post_id):
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
def users(request):
    users = User.objects.order_by('username')
    form = UserSearchForm(request.GET)
    users = form.filter(users)
    return {'paged_qs': users,
            'form': form,
            }


@login_required
def delete_subscription(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    topic.subscribers.remove(request.user)
    return HttpResponseRedirect(reverse('edit_profile'))


@login_required
def add_subscription(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    topic.subscribers.add(request.user)
    return HttpResponseRedirect(reverse('topic', args=[topic.id]))
