# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.views import generic

from pybb import defaults
from pybb.permissions import perms
from pybb.models import Forum

from pybb.views.mixins import RedirectToLoginMixin, PaginatorMixin


class ForumView(RedirectToLoginMixin, PaginatorMixin, generic.ListView):

    paginate_by = defaults.PYBB_FORUM_PAGE_SIZE
    context_object_name = 'topic_list'
    template_name = 'pybb/forum.html'

    def dispatch(self, request, *args, **kwargs):
        self.forum = self.get_forum(**kwargs)
        return super(ForumView, self).dispatch(request, *args, **kwargs)

    def get_login_redirect_url(self):
        return self.forum.get_absolute_url()

    def get_context_data(self, **kwargs):
        ctx = super(ForumView, self).get_context_data(**kwargs)
        ctx['forum'] = self.forum
        ctx['forum'].forums_accessed = perms.filter_forums(self.request.user, self.forum.child_forums.all())
        return ctx

    def get_queryset(self):
        if not perms.may_view_forum(self.request.user, self.forum):
            raise PermissionDenied

        qs = self.forum.topics.order_by('-sticky', '-updated', '-id').select_related()
        qs = perms.filter_topics(self.request.user, qs)
        return qs

    def get_forum(self, **kwargs):
        if 'pk' in kwargs:
            forum = get_object_or_404(Forum.objects.all(), pk=kwargs['pk'])
        elif ('slug' and 'category_slug') in kwargs:
            forum = get_object_or_404(Forum, slug=kwargs['slug'], category__slug=kwargs['category_slug'])
        else:
            raise Http404(_('Forum does not exist'))
        return forum

    def get(self, *args, **kwargs):
        if defaults.PYBB_NICE_URL and 'pk' in kwargs:
            return redirect(self.forum, permanent=defaults.PYBB_NICE_URL_PERMANENT_REDIRECT)
        return super(ForumView, self).get(*args, **kwargs)
