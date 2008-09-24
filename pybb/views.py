import math

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.urlresolvers import reverse

from pybb.util import render_to, paged, build_form
from pybb.models import Category, Forum, Topic, Post
from pybb.forms import AddPostForm, EditProfileForm, EditPostForm

@render_to('pybb/index.html')
def index(request):
    cats = Category.objects.all().select_related()
    quick = {'posts': Post.objects.count(),
             'topics': Topic.objects.count(),
             'users': User.objects.count(),
             'last_topics': Topic.objects.all().select_related()[:settings.PYBB_QUICK_TOPICS_NUMBER],
             'last_posts': Post.objects.order_by('-created').select_related()[:settings.PYBB_QUICK_POSTS_NUMBER],
             }
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
            'quick': quick,
            'paged_qs': topics,
            }

    
@render_to('pybb/topic.html')
@paged('posts', settings.PYBB_TOPIC_PAGE_SIZE)
def show_topic(request, topic_id):
    topic = Topic.objects.select_related().get(pk=topic_id)
    topic.views += 1
    topic.save()

    if request.user.is_authenticated():
        topic.update_read(request.user)

    posts = topic.posts.all().select_related()

    initial = {}
    if request.user.is_authenticated():
        initial = {'markup': request.user.pybb_profile.markup}
    form = AddPostForm(topic=topic, initial=initial)
    return {'topic': topic,
            'form': form,
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

    ip = request.META.get('REMOTE_ADDR', '')
    print 'USER MARKUP', request.user.pybb_profile.markup
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
    post = get_object_or_404(Post, pk=post_id)
    if post.user != request.user:
        return HttpResponseRedirect(post.get_absolute_url())

    form = build_form(EditPostForm, request, instance=post)

    if form.is_valid():
        post = form.save()
        return HttpResponseRedirect(post.get_absolute_url())

    return {'form': form,
            'post': post,
            }
