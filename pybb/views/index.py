# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.views import generic

from pybb.permissions import perms
from pybb.models import Category


class IndexView(generic.ListView):

    template_name = 'pybb/index.html'
    context_object_name = 'categories'

    def get_context_data(self, **kwargs):
        ctx = super(IndexView, self).get_context_data(**kwargs)
        categories = ctx['categories']
        for category in categories:
            category.forums_accessed = perms.filter_forums(self.request.user, category.forums.filter(parent=None))
        ctx['categories'] = categories
        return ctx

    def get_queryset(self):
        return perms.filter_categories(self.request.user, Category.objects.all())

