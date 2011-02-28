from django.contrib.contenttypes.models import ContentType
import re
from datetime import datetime
import os.path
import inspect

from django import forms
from django.utils.translation import ugettext as _
from pybb.models import Topic, Post, Profile, Attachment
from django.contrib.auth.models import User

import defaults
from django.conf import settings

MEDIA_ROOT = settings.MEDIA_ROOT
class PostForm(forms.ModelForm):
    name = forms.CharField(label=_('Subject'))
    attachment = forms.FileField(label=_('Attachment'), required=False)

    class Meta(object):
        model = Post
        fields = ('body',)

    def __init__(self, *args, **kwargs):
    #Move args to kwargs
        if args:
            kwargs.update(dict(zip(inspect.getargspec(super(PostForm, self).__init__)[0][1:], args)))
        self.user = kwargs.pop('user', None)
        self.ip = kwargs.pop('ip', None)
        self.topic = kwargs.pop('topic', None)
        self.forum = kwargs.pop('forum', None)
        if not (self.topic or self.forum or ('instance' in kwargs)):
            raise ValueError('You should provide topic, forum or instance')
        #Handle topic subject if editing topic head
        if ('instance' in kwargs) and (kwargs['instance'].topic.head == kwargs['instance']):
            kwargs.setdefault('initial', {})['name'] = kwargs['instance'].topic.name

        super(PostForm, self).__init__(**kwargs)

        self.fields.keyOrder = ['name', 'body', 'attachment']

        if not (self.forum or (self.instance.pk and (self.instance.topic.head == self.instance))):
            self.fields['name'].widget = forms.HiddenInput()
            self.fields['name'].required = False

        if not defaults.PYBB_ATTACHMENT_ENABLE:
            self.fields['attachment'].widget = forms.HiddenInput()
            self.fields['attachment'].required = False

        self.aviable_smiles = defaults.PYBB_SMILES
        self.smiles_prefix = defaults.PYBB_SMILES_PREFIX

    def clean_attachment(self):
        for f in self.files:
            if self.files[f].size > defaults.PYBB_ATTACHMENT_SIZE_LIMIT:
                raise forms.ValidationError(_('Attachment is too big'))
        return self.cleaned_data['attachment']

    def save(self, commit=True):
        if self.instance.pk:
            post = super(PostForm, self).save(commit=False)
            if self.user:
                post.user = self.user
            if post.topic.head == post:
                post.topic.name = self.cleaned_data['name']
                post.topic.updated = datetime.now()
                post.topic.save()
            post.save()
            return post
        if self.forum:
            topic = Topic(forum=self.forum,
                          user=self.user,
                          name=self.cleaned_data['name'])
            topic.save()
        else:
            topic = self.topic
        post = Post(topic=topic, user=self.user, user_ip=self.ip,
                    markup=self.user.get_profile().markup,
                    body=self.cleaned_data['body'])
        post.save()
        if defaults.PYBB_ATTACHMENT_ENABLE:
            for f in self.files:
                self.save_attachment(post, self.files[f])
        return post

    def save_attachment(self, post, memfile):
        if memfile:
            obj = Attachment(size=memfile.size, content_type=memfile.content_type,
                             name=memfile.name, post=post)
            dir = os.path.join(MEDIA_ROOT, defaults.PYBB_ATTACHMENT_UPLOAD_TO)
            fname = '%d.0' % post.id
            path = os.path.join(dir, fname)
            file(path, 'w').write(memfile.read())
            obj.path = fname
            obj.save()


class AdminPostForm(PostForm):
    '''
    Superusers can post messages from any user and from any time
    If no user with specified name - new user will be created
    '''
    login = forms.CharField(label=_('User'))

    def __init__(self, *args, **kwargs):
        if args:
            kwargs.update(dict(zip(inspect.getargspec(forms.ModelForm.__init__)[0][1:], args)))
        if 'instance' in kwargs:
            kwargs.setdefault('initial', {}).update({'login': kwargs['instance'].user.username})
        super(AdminPostForm, self).__init__(**kwargs)
        self.fields.keyOrder = ['name', 'login', 'body', 'attachment']

    def save(self, *args, **kwargs):
        try:
            self.user = User.objects.filter(username=self.cleaned_data['login']).get()
        except:
            self.user = User.objects.create_user(self.cleaned_data['login'],
                                                 '%s@example.com' % self.cleaned_data['login'])
        return super(AdminPostForm, self).save(*args, **kwargs)

try:
    profile_app, profile_model = settings.AUTH_PROFILE_MODULE.split('.')
    profile_model = ContentType.objects.get(app_label=profile_app, model=profile_model).model_class()
except:
    profile_model = Profile

class EditProfileForm(forms.ModelForm):
    class Meta(object):
        model = profile_model
        fields = ['signature', 'time_zone', 'language',
                  'show_signatures', 'markup', 'avatar']

    def clean_avatar(self):
        if self.cleaned_data['avatar'] and (self.cleaned_data['avatar'].size > defaults.PYBB_MAX_AVATAR_SIZE):
            forms.ValidationError(_('Avatar is too large, max size: %s bytes' % defaults.PYBB_MAX_AVATAR_SIZE))
        return self.cleaned_data['avatar']

    def clean_signature(self):
        value = self.cleaned_data['signature'].strip()
        if len(re.findall(r'\n', value)) > defaults.PYBB_SIGNATURE_MAX_LINES:
            raise forms.ValidationError('Number of lines is limited to %d' % defaults.PYBB_SIGNATURE_MAX_LINES)
        if len(value) > defaults.PYBB_SIGNATURE_MAX_LENGTH:
            raise forms.ValidationError('Length of signature is limited to %d' % defaults.PYBB_SIGNATURE_MAX_LENGTH)
        return value


class UserSearchForm(forms.Form):
    query = forms.CharField(required=False, label='')

    def filter(self, qs):
        if self.is_valid():
            query = self.cleaned_data['query']
            return qs.filter(username__contains=query)
        else:
            return qs
