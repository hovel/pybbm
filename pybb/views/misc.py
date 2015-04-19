# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST

from pybb import compat, util
from pybb.permissions import perms
from pybb.models import (Topic, PollAnswerUser, Forum, ForumReadTracker,
                         TopicReadTracker, Post)

User = compat.get_user_model()
username_field = compat.get_username_field()


@login_required
def topic_cancel_poll_vote(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    PollAnswerUser.objects.filter(user=request.user, poll_answer__topic_id=topic.id).delete()
    return HttpResponseRedirect(topic.get_absolute_url())


@login_required
def delete_subscription(request, topic_id):
    topic = get_object_or_404(perms.filter_topics(request.user, Topic.objects.all()), pk=topic_id)
    topic.subscribers.remove(request.user)
    return HttpResponseRedirect(topic.get_absolute_url())


@login_required
def add_subscription(request, topic_id):
    topic = get_object_or_404(perms.filter_topics(request.user, Topic.objects.all()), pk=topic_id)
    if not perms.may_subscribe_topic(request.user, topic):
        raise PermissionDenied
    topic.subscribers.add(request.user)
    return HttpResponseRedirect(topic.get_absolute_url())


@login_required
def post_ajax_preview(request):
    content = request.POST.get('data')
    html = util._get_markup_formatter()(content)
    return render(request, 'pybb/_markitup_preview.html', {'html': html})


@login_required
def mark_all_as_read(request):
    for forum in perms.filter_forums(request.user, Forum.objects.all()):
        forum_mark, new = ForumReadTracker.objects.get_or_create_tracker(forum=forum, user=request.user)
        forum_mark.save()
    TopicReadTracker.objects.filter(user=request.user).delete()
    msg = _('All forums marked as read')
    messages.success(request, msg, fail_silently=True)
    return redirect(reverse('pybb:index'))


@login_required
@require_POST
def block_user(request, username):
    user = get_object_or_404(User, **{username_field: username})
    if not perms.may_block_user(request.user, user):
        raise PermissionDenied
    user.is_active = False
    user.save()
    if 'block_and_delete_messages' in request.POST:
        # individually delete each post and empty topic to fire method
        # with forum/topic counters recalculation
        posts = Post.objects.filter(user=user)
        topics = posts.values('topic_id').distinct()
        forums = posts.values('topic__forum_id').distinct()
        posts.delete()
        Topic.objects.filter(user=user).delete()
        for t in topics:
            try:
                Topic.objects.get(id=t['topic_id']).update_counters()
            except Topic.DoesNotExist:
                pass
        for f in forums:
            try:
                Forum.objects.get(id=f['topic__forum_id']).update_counters()
            except Forum.DoesNotExist:
                pass

    msg = _('User successfully blocked')
    messages.success(request, msg, fail_silently=True)
    return redirect('pybb:index')


@login_required
@require_POST
def unblock_user(request, username):
    user = get_object_or_404(User, **{username_field: username})
    if not perms.may_block_user(request.user, user):
        raise PermissionDenied
    user.is_active = True
    user.save()
    msg = _('User successfuly unblocked')
    messages.success(request, msg, fail_silently=True)
    return redirect('pybb:index')
