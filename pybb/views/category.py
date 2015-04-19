# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.views import generic

from pybb.permissions import perms
from pybb.models import Category

from .mixins import RedirectToLoginMixin


class CategoryView(RedirectToLoginMixin, generic.DetailView):

    template_name = 'pybb/index.html'
    context_object_name = 'category'

    def get_login_redirect_url(self):
        return reverse('pybb:category', args=(self.kwargs['pk'],))

    def get_queryset(self):
        return Category.objects.all()

    def get_object(self, queryset=None):
        obj = super(CategoryView, self).get_object(queryset)
        if not perms.may_view_category(self.request.user, obj):
            raise PermissionDenied
        return obj

    def get_context_data(self, **kwargs):
        ctx = super(CategoryView, self).get_context_data(**kwargs)
        ctx['category'].forums_accessed = perms.filter_forums(self.request.user, ctx['category'].forums.filter(parent=None))
        ctx['categories'] = [ctx['category']]
        return ctx
