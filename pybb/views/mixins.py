# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils.decorators import method_decorator

from pybb import compat
from pybb.compat import get_atomic_func
from pybb.forms import (PostForm, AdminPostForm, AttachmentFormSet, PollForm,
                        PollAnswerFormSet)
from pybb.permissions import perms
from pybb.models import Topic

Paginator, pure_pagination = compat.get_paginator_class()


class PaginatorMixin(object):
    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True, **kwargs):
        kwargs = {}
        if pure_pagination:
            kwargs['request'] = self.request
        return Paginator(queryset, per_page, orphans=0, allow_empty_first_page=True, **kwargs)


class RedirectToLoginMixin(object):
    """ mixin which redirects to settings.LOGIN_URL if the view encounters an PermissionDenied exception
        and the user is not authenticated. Views inheriting from this need to implement
        get_login_redirect_url(), which returns the URL to redirect to after login (parameter "next")
    """
    def dispatch(self, request, *args, **kwargs):
        try:
            return super(RedirectToLoginMixin, self).dispatch(request, *args, **kwargs)
        except PermissionDenied:
            if not request.user.is_authenticated():
                return redirect_to_login(self.get_login_redirect_url())
            else:
                return HttpResponseForbidden()

    def get_login_redirect_url(self):
        """ get the url to which we redirect after the user logs in. subclasses should override this """
        return '/'

class PybbFormsMixin(object):

    post_form_class = PostForm
    admin_post_form_class = AdminPostForm
    attachment_formset_class = AttachmentFormSet
    poll_form_class = PollForm
    poll_answer_formset_class = PollAnswerFormSet

    def get_post_form_class(self):
        return self.post_form_class

    def get_admin_post_form_class(self):
        return self.admin_post_form_class

    def get_attachment_formset_class(self):
        return self.attachment_formset_class

    def get_poll_form_class(self):
        return self.poll_form_class

    def get_poll_answer_formset_class(self):
        return self.poll_answer_formset_class

class PostEditMixin(PybbFormsMixin):

    @method_decorator(get_atomic_func())
    def post(self, request, *args, **kwargs):
        return super(PostEditMixin, self).post(request, *args, **kwargs)

    def get_form_class(self):
        if perms.may_post_as_admin(self.request.user):
            return self.get_admin_post_form_class()
        else:
            return self.get_post_form_class()

    def get_context_data(self, **kwargs):

        ctx = super(PostEditMixin, self).get_context_data(**kwargs)

        if perms.may_attach_files(self.request.user) and (not 'aformset' in kwargs):
            ctx['aformset'] = self.get_attachment_formset_class()(
                instance=self.object if getattr(self, 'object') else None
            )

        if perms.may_create_poll(self.request.user) and ('pollformset' not in kwargs):
            ctx['pollformset'] = self.get_poll_answer_formset_class()(
                instance=self.object.topic if getattr(self, 'object') else None
            )

        return ctx

    def form_valid(self, form):
        success = True
        save_attachments = False
        save_poll_answers = False
        self.object = form.save(commit=False)

        if perms.may_attach_files(self.request.user):
            aformset = self.get_attachment_formset_class()(
                self.request.POST, self.request.FILES, instance=self.object
            )
            if aformset.is_valid():
                save_attachments = True
            else:
                success = False
        else:
            aformset = None

        if perms.may_create_poll(self.request.user):
            pollformset = self.get_poll_answer_formset_class()()
            if getattr(self, 'forum', None) or self.object.topic.head == self.object:
                if self.object.topic.poll_type != Topic.POLL_TYPE_NONE:
                    pollformset = self.get_poll_answer_formset_class()(self.request.POST,
                                                                       instance=self.object.topic)
                    if pollformset.is_valid():
                        save_poll_answers = True
                    else:
                        success = False
                else:
                    self.object.topic.poll_question = None
                    self.object.topic.poll_answers.all().delete()
        else:
            pollformset = None

        if success:
            self.object.topic.save()
            self.object.topic = self.object.topic
            self.object.save()
            if save_attachments:
                aformset.save()
            if save_poll_answers:
                pollformset.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, aformset=aformset, pollformset=pollformset))
