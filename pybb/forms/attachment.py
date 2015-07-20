# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext as _

from pybb import defaults
from pybb.models import Post, Attachment


class AttachmentForm(forms.ModelForm):
    class Meta(object):
        model = Attachment
        fields = ('file', )

    def clean_file(self):
        if self.cleaned_data['file'].size > defaults.PYBB_ATTACHMENT_SIZE_LIMIT:
            raise forms.ValidationError(_('Attachment is too big'))
        return self.cleaned_data['file']

AttachmentFormSet = inlineformset_factory(Post, Attachment, extra=1, form=AttachmentForm)
