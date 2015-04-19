# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.views import generic

from pybb import defaults
from pybb.permissions import perms
from pybb.models import Forum

from .mixins import RedirectToLoginMixin, PaginatorMixin


class ForumView(RedirectToLoginMixin, PaginatorMixin, generic.ListView):

    paginate_by = defaults.PYBB_FORUM_PAGE_SIZE
    context_object_name = 'topic_list'
    template_name = 'pybb/forum.html'

    def get_login_redirect_url(self):
        return reverse('pybb:forum', args=(self.kwargs['pk'],))

    def get_context_data(self, **kwargs):
        ctx = super(ForumView, self).get_context_data(**kwargs)
        ctx['forum'] = self.forum
        ctx['forum'].forums_accessed = perms.filter_forums(self.request.user, self.forum.child_forums.all())
        return ctx

    def get_queryset(self):
        self.forum = get_object_or_404(Forum.objects.all(), pk=self.kwargs['pk'])
        if not perms.may_view_forum(self.request.user, self.forum):
            raise PermissionDenied

        qs = self.forum.topics.order_by('-sticky', '-updated', '-id').select_related()
        qs = perms.filter_topics(self.request.user, qs)
        return qs
