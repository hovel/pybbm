# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models import F, Q
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views import generic
from django.views.decorators.csrf import csrf_protect

from pybb import compat, defaults, util
from pybb.permissions import perms
from pybb.templatetags.pybb_tags import pybb_topic_poll_not_voted
from pybb.models import Topic, TopicReadTracker, ForumReadTracker

from pybb.views.mixins import RedirectToLoginMixin, PaginatorMixin, PybbFormsMixin

username_field = compat.get_username_field()


class TopicView(RedirectToLoginMixin, PaginatorMixin, PybbFormsMixin, generic.ListView):
    paginate_by = defaults.PYBB_TOPIC_PAGE_SIZE
    template_object_name = 'post_list'
    template_name = 'pybb/topic.html'

    def get_login_redirect_url(self):
        return self.topic.get_absolute_url()

    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        self.topic = self.get_topic(**kwargs)

        if request.GET.get('first-unread'):
            if request.user.is_authenticated():
                read_dates = []
                try:
                    read_dates.append(TopicReadTracker.objects.get(user=request.user, topic=self.topic).time_stamp)
                except TopicReadTracker.DoesNotExist:
                    pass
                try:
                    read_dates.append(ForumReadTracker.objects.get(user=request.user, forum=self.topic.forum).time_stamp)
                except ForumReadTracker.DoesNotExist:
                    pass

                read_date = read_dates and max(read_dates)
                if read_date:
                    try:
                        first_unread_topic = self.topic.posts.filter(created__gt=read_date).order_by('created', 'id')[0]
                    except IndexError:
                        first_unread_topic = self.topic.last_post
                else:
                    first_unread_topic = self.topic.head
                return HttpResponseRedirect(reverse('pybb:post', kwargs={'pk': first_unread_topic.id}))

        return super(TopicView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if not perms.may_view_topic(self.request.user, self.topic):
            raise PermissionDenied
        if self.request.user.is_authenticated() or not defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER:
            Topic.objects.filter(id=self.topic.id).update(views=F('views') + 1)
        else:
            cache_key = util.build_cache_key('anonymous_topic_views', topic_id=self.topic.id)
            cache.add(cache_key, 0)
            if cache.incr(cache_key) % defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER == 0:
                Topic.objects.filter(id=self.topic.id).update(views=F('views') +
                                                                defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER)
                cache.set(cache_key, 0)
        qs = self.topic.posts.all().select_related('user')
        if defaults.PYBB_PROFILE_RELATED_NAME:
            qs = qs.select_related('user__%s' % defaults.PYBB_PROFILE_RELATED_NAME)
        if not perms.may_moderate_topic(self.request.user, self.topic):
            qs = perms.filter_posts(self.request.user, qs)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super(TopicView, self).get_context_data(**kwargs)

        if self.request.user.is_authenticated():
            self.request.user.is_moderator = perms.may_moderate_topic(self.request.user, self.topic)
            self.request.user.is_subscribed = self.request.user in self.topic.subscribers.all()
            if perms.may_post_as_admin(self.request.user):
                ctx['form'] = self.get_admin_post_form_class()(
                    initial={'login': getattr(self.request.user, username_field)},
                    topic=self.topic)
            else:
                ctx['form'] = self.get_post_form_class()(topic=self.topic)
            self.mark_read(self.request.user, self.topic)
        elif defaults.PYBB_ENABLE_ANONYMOUS_POST:
            ctx['form'] = self.get_post_form_class()(topic=self.topic)
        else:
            ctx['form'] = None
            ctx['next'] = self.get_login_redirect_url()
        if perms.may_attach_files(self.request.user):
            aformset = self.get_attachment_formset_class()()
            ctx['aformset'] = aformset
        if defaults.PYBB_FREEZE_FIRST_POST:
            ctx['first_post'] = self.topic.head
        else:
            ctx['first_post'] = None
        ctx['topic'] = self.topic

        if perms.may_vote_in_topic(self.request.user, self.topic) and \
                pybb_topic_poll_not_voted(self.topic, self.request.user):
            ctx['poll_form'] = self.get_poll_form_class()(self.topic)

        return ctx

    def mark_read(self, user, topic):
        try:
            forum_mark = ForumReadTracker.objects.get(forum=topic.forum, user=user)
        except ForumReadTracker.DoesNotExist:
            forum_mark = None
        if (forum_mark is None) or (forum_mark.time_stamp < topic.updated):
            # Mark topic as readed
            topic_mark, new = TopicReadTracker.objects.get_or_create_tracker(topic=topic, user=user)
            if not new:
                topic_mark.save()

            # Check, if there are any unread topics in forum
            readed = topic.forum.topics.filter((Q(topicreadtracker__user=user,
                                                  topicreadtracker__time_stamp__gte=F('updated'))) |
                                                Q(forum__forumreadtracker__user=user,
                                                  forum__forumreadtracker__time_stamp__gte=F('updated')))\
                                       .only('id').order_by()

            not_readed = topic.forum.topics.exclude(id__in=readed)
            if not not_readed.exists():
                # Clear all topic marks for this forum, mark forum as readed
                TopicReadTracker.objects.filter(user=user, topic__forum=topic.forum).delete()
                forum_mark, new = ForumReadTracker.objects.get_or_create_tracker(forum=topic.forum, user=user)
                forum_mark.save()

    def get_topic(self, **kwargs):
        if 'pk' in kwargs:
            topic = get_object_or_404(Topic, pk=kwargs['pk'], post_count__gt=0)
        elif ('slug'and 'forum_slug'and 'category_slug') in kwargs:
            topic = get_object_or_404(
                Topic,
                slug=kwargs['slug'],
                forum__slug=kwargs['forum_slug'],
                forum__category__slug=kwargs['category_slug'],
                post_count__gt=0
                )
        else:
            raise Http404(_('This topic does not exists'))
        return topic

    def get(self, *args, **kwargs):
        if defaults.PYBB_NICE_URL and 'pk' in kwargs:
            return redirect(self.topic, permanent=defaults.PYBB_NICE_URL_PERMANENT_REDIRECT)
        return super(TopicView, self).get(*args, **kwargs)


class LatestTopicsView(PaginatorMixin, generic.ListView):

    paginate_by = defaults.PYBB_FORUM_PAGE_SIZE
    context_object_name = 'topic_list'
    template_name = 'pybb/latest_topics.html'

    def get_queryset(self):
        qs = Topic.objects.all().select_related()
        qs = perms.filter_topics(self.request.user, qs)
        return qs.order_by('-updated', '-id')
