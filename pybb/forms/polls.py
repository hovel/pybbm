# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import ugettext as _

from pybb import defaults
from pybb.models import PollAnswer, Topic

class PollForm(forms.Form):
    def __init__(self, topic, *args, **kwargs):
        self.topic = topic

        super(PollForm, self).__init__(*args, **kwargs)

        qs = PollAnswer.objects.filter(topic=topic)
        if topic.poll_type == Topic.POLL_TYPE_SINGLE:
            self.fields['answers'] = forms.ModelChoiceField(
                label='', queryset=qs, empty_label=None,
                widget=forms.RadioSelect())
        elif topic.poll_type == Topic.POLL_TYPE_MULTIPLE:
            self.fields['answers'] = forms.ModelMultipleChoiceField(
                label='', queryset=qs,
                widget=forms.CheckboxSelectMultiple())

    def clean_answers(self):
        answers = self.cleaned_data['answers']
        if self.topic.poll_type == Topic.POLL_TYPE_SINGLE:
            return [answers]
        else:
            return answers

class PollAnswerForm(forms.ModelForm):
    class Meta:
        model = PollAnswer
        fields = ('text', )


class BasePollAnswerFormset(BaseInlineFormSet):
    def clean(self):
        forms_cnt = (len(self.initial_forms) + len([form for form in self.extra_forms if form.has_changed()]) -
                     len(self.deleted_forms))
        if forms_cnt > defaults.PYBB_POLL_MAX_ANSWERS:
            raise forms.ValidationError(
                _('You can''t add more than %s answers for poll' % defaults.PYBB_POLL_MAX_ANSWERS))
        if forms_cnt < 2:
            raise forms.ValidationError(_('Add two or more answers for this poll'))


PollAnswerFormSet = inlineformset_factory(Topic, PollAnswer, extra=2, max_num=defaults.PYBB_POLL_MAX_ANSWERS,
                                          form=PollAnswerForm, formset=BasePollAnswerFormset)
