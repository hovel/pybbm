from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from board.util import render_to, build_form
from board.models import Category, Forum, Topic, Post
from board.forms import AddPostForm

@render_to('board/index.html')
def index(request):
    cats = Category.objects.all()
    last_created = Topic.objects.all()[:10]
    last_updated = Topic.objects.all().order_by('-updated')[:10]
    stats = {'posts': Post.objects.all().count(),
             'topics': Topic.objects.all().count(),
             'users': User.objects.all().count(),
             }
    return {'cats': cats,
            'last_created': last_created,
            'last_updated': last_updated,
            'stats': stats,
            }


@render_to('board/category.html')
def show_category(request, category_id):
    category = Category.objects.get(pk=category_id)
    return {'category': category,
            }


@render_to('board/forum.html')
def show_forum(request, forum_id):
    forum = Forum.objects.get(pk=forum_id)
    return {'forum': forum,
            }

    
@render_to('board/topic.html')
def show_topic(request, topic_id):
    topic = Topic.objects.get(pk=topic_id)
    form = AddPostForm(topic=topic)
    return {'topic': topic,
            'form': form,
            }


@login_required
@render_to('board/add_post.html')
def add_post(request, forum_id, topic_id):
    forum = None
    topic = None

    if forum_id:
        forum = get_object_or_404(Forum, pk=forum_id)
    elif topic_id:
        topic = get_object_or_404(Topic, pk=topic_id)

    form = build_form(AddPostForm, request, topic=topic, forum=forum, user=request.user)

    if form.is_valid():
        post = form.save();
        return HttpResponseRedirect(post.topic.get_absolute_url())

    return {'form': form,
            'topic': topic,
            'forum': forum,
            }


@render_to('board/user.html')
def user(request, username):
    user = get_object_or_404(User, username=username)
    return {'profile': user,
            }
