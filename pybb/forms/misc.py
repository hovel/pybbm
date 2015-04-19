# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms


class UserSearchForm(forms.Form):
    query = forms.CharField(required=False, label='')

    def filter(self, qs):
        if self.is_valid():
            query = self.cleaned_data['query']
            return qs.filter(**{'%s__contains' % username_field: query})
        else:
            return qs
