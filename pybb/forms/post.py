# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import inspect

from django import forms
from django.utils.timezone import now as tznow
from django.utils.translation import ugettext, ugettext_lazy as _

from pybb import compat, defaults, util
from pybb.models import Post, Topic

User = compat.get_user_model()
username_field = compat.get_username_field()


class PostForm(forms.ModelForm):
    name = forms.CharField(label=_('Subject'))
    poll_type = forms.TypedChoiceField(label=_('Poll type'), choices=Topic.POLL_TYPE_CHOICES, coerce=int)
    poll_question = forms.CharField(
        label=_('Poll question'),
        required=False,
        widget=forms.Textarea(attrs={'class': 'no-markitup'}))
    slug = forms.CharField(label=_('Topic slug'), required=False)

    class Meta(object):
        model = Post
        fields = ('body',)
        widgets = {
            'body': util.get_markup_engine().get_widget_cls(),
        }

    def __init__(self, *args, **kwargs):
        # Move args to kwargs
        if args:
            kwargs.update(dict(zip(inspect.getargspec(super(PostForm, self).__init__)[0][1:], args)))
        self.user = kwargs.pop('user', None)
        self.ip = kwargs.pop('ip', None)
        self.topic = kwargs.pop('topic', None)
        self.forum = kwargs.pop('forum', None)
        self.may_create_poll = kwargs.pop('may_create_poll', True)
        self.may_edit_topic_slug = kwargs.pop('may_edit_topic_slug', False)
        if not (self.topic or self.forum or ('instance' in kwargs)):
            raise ValueError('You should provide topic, forum or instance')
            # Handle topic subject, poll type and question if editing topic head
        if kwargs.get('instance', None) and (kwargs['instance'].topic.head == kwargs['instance']):
            kwargs.setdefault('initial', {})['name'] = kwargs['instance'].topic.name
            kwargs.setdefault('initial', {})['poll_type'] = kwargs['instance'].topic.poll_type
            kwargs.setdefault('initial', {})['poll_question'] = kwargs['instance'].topic.poll_question

        super(PostForm, self).__init__(**kwargs)

        # remove topic specific fields
        if not (self.forum or (self.instance.pk and (self.instance.topic.head == self.instance))):
            del self.fields['name']
            del self.fields['poll_type']
            del self.fields['poll_question']
            del self.fields['slug']
        else:
            if not self.may_create_poll:
                del self.fields['poll_type']
                del self.fields['poll_question']
            if not self.may_edit_topic_slug:
                del self.fields['slug']

        self.available_smiles = defaults.PYBB_SMILES
        self.smiles_prefix = defaults.PYBB_SMILES_PREFIX

    def clean_body(self):
        body = self.cleaned_data['body']
        user = self.user or self.instance.user
        if defaults.PYBB_BODY_VALIDATOR:
            defaults.PYBB_BODY_VALIDATOR(user, body)

        for cleaner in defaults.PYBB_BODY_CLEANERS:
            body = util.get_body_cleaner(cleaner)(user, body)
        return body

    def clean(self):
        poll_type = self.cleaned_data.get('poll_type', None)
        poll_question = self.cleaned_data.get('poll_question', None)
        if poll_type is not None and poll_type != Topic.POLL_TYPE_NONE and not poll_question:
            raise forms.ValidationError(ugettext('Poll''s question is required when adding a poll'))

        return self.cleaned_data

    def save(self, commit=True):
        if self.instance.pk:
            post = super(PostForm, self).save(commit=False)
            if self.user:
                post.user = self.user
            if post.topic.head == post:
                post.topic.name = self.cleaned_data['name']
                if self.may_create_poll:
                    post.topic.poll_type = self.cleaned_data['poll_type']
                    post.topic.poll_question = self.cleaned_data['poll_question']
                post.topic.updated = tznow()
                if commit:
                    post.topic.save()
            post.updated = tznow()
            if commit:
                post.save()
            return post, post.topic

        allow_post = True
        if defaults.PYBB_PREMODERATION:
            allow_post = defaults.PYBB_PREMODERATION(self.user, self.cleaned_data['body'])
        if self.forum:
            topic = Topic(
                forum=self.forum,
                user=self.user,
                name=self.cleaned_data['name'],
                poll_type=self.cleaned_data.get('poll_type', Topic.POLL_TYPE_NONE),
                poll_question=self.cleaned_data.get('poll_question', None),
                slug=self.cleaned_data.get('slug', None),
            )
            if not allow_post:
                topic.on_moderation = True
        else:
            topic = self.topic
        post = Post(user=self.user, user_ip=self.ip, body=self.cleaned_data['body'])
        if not allow_post:
            post.on_moderation = True
        if commit:
            topic.save()
            post.topic = topic
            post.save()
        return post, topic


class AdminPostForm(PostForm):
    """
    Superusers can post messages from any user and from any time
    If no user with specified name - new user will be created
    """
    login = forms.CharField(label=_('User'))

    def __init__(self, *args, **kwargs):
        if args:
            kwargs.update(dict(zip(inspect.getargspec(forms.ModelForm.__init__)[0][1:], args)))
        if 'instance' in kwargs and kwargs['instance']:
            kwargs.setdefault('initial', {}).update({'login': getattr(kwargs['instance'].user, username_field)})
        super(AdminPostForm, self).__init__(**kwargs)

    def save(self, *args, **kwargs):
        try:
            self.user = User.objects.filter(**{username_field: self.cleaned_data['login']}).get()
        except User.DoesNotExist:
            if username_field != 'email':
                create_data = {username_field: self.cleaned_data['login'],
                               'email': '%s@example.com' % self.cleaned_data['login'],
                               'is_staff': False}
            else:
                create_data = {'email': '%s@example.com' % self.cleaned_data['login'],
                               'is_staff': False}
            self.user = User.objects.create(**create_data)
        return super(AdminPostForm, self).save(*args, **kwargs)
