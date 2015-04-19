# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.generic.edit import ModelFormMixin

from pybb.permissions import perms
from pybb.models import Topic, PollAnswerUser
from pybb.templatetags.pybb_tags import pybb_topic_poll_not_voted

from .mixins import PybbFormsMixin


class TopicPollVoteView(PybbFormsMixin, generic.UpdateView):
    model = Topic
    http_method_names = ['post', ]

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(TopicPollVoteView, self).dispatch(request, *args, **kwargs)

    def get_form_class(self):
        return self.get_poll_form_class()

    def get_form_kwargs(self):
        kwargs = super(ModelFormMixin, self).get_form_kwargs()
        kwargs['topic'] = self.object
        return kwargs

    def form_valid(self, form):
        # already voted
        if not perms.may_vote_in_topic(self.request.user, self.object) or \
           not pybb_topic_poll_not_voted(self.object, self.request.user):
            return HttpResponseForbidden()

        answers = form.cleaned_data['answers']
        for answer in answers:
            # poll answer from another topic
            if answer.topic != self.object:
                return HttpResponseBadRequest()

            PollAnswerUser.objects.create(poll_answer=answer, user=self.request.user)
        return super(ModelFormMixin, self).form_valid(form)

    def form_invalid(self, form):
        return redirect(self.object)

    def get_success_url(self):
        return self.object.get_absolute_url()