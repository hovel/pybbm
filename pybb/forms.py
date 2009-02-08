import re
from datetime import datetime
import os.path

from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User

from pybb.models import Topic, Post, Profile, PrivateMessage, Attachment
from pybb import settings as pybb_settings

class AddPostForm(forms.ModelForm):
    name = forms.CharField(label=_('Subject'))
    attachment = forms.FileField(label=_('Attachment'), required=False)

    class Meta:
        model = Post
        fields = ['markup', 'body']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.topic = kwargs.pop('topic', None)
        self.forum = kwargs.pop('forum', None)
        self.ip = kwargs.pop('ip', None)
        super(AddPostForm, self).__init__(*args, **kwargs)

        self.fields.keyOrder = ['name', 'markup', 'body', 'attachment']

        if self.topic:
            self.fields['name'].widget = forms.HiddenInput()
            self.fields['name'].required = False

        if not pybb_settings.ATTACHMENT_ENABLE:
            self.fields['attachment'].widget = forms.HiddenInput()
            self.fields['attachment'].required = False
 

    def clean_attachment(self):
        if self.cleaned_data['attachment']:
            memfile = self.cleaned_data['attachment']
            if memfile.size > pybb_settings.ATTACHMENT_SIZE_LIMIT:
                raise forms.ValidationError(_('Attachment is too big'))
        return self.cleaned_data['attachment']



    def save(self):
        if self.forum:
            topic = Topic(forum=self.forum,
                          user=self.user,
                          name=self.cleaned_data['name'])
            topic.save()
        else:
            topic = self.topic

        post = Post(topic=topic, user=self.user, user_ip=self.ip,
                    markup=self.cleaned_data['markup'],
                    body=self.cleaned_data['body'])
        post.save()

        if pybb_settings.ATTACHMENT_ENABLE:
            self.save_attachment(post, self.cleaned_data['attachment'])
        return post


    def save_attachment(self, post, memfile):
        if memfile:
            obj = Attachment(size=memfile.size, content_type=memfile.content_type,
                             name=memfile.name, post=post)
            dir = os.path.join(settings.MEDIA_ROOT, pybb_settings.ATTACHMENT_UPLOAD_TO)
            fname = '%d.0' % post.id
            path = os.path.join(dir, fname)
            file(path, 'w').write(memfile.read())
            obj.path = fname
            obj.save()


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['site', 'jabber', 'icq', 'msn', 'aim', 'yahoo',
                  'location', 'signature', 'time_zone', 'language',
                  'avatar', 'show_signatures',
                  'markup',
                  ]


    #def __init__(self, *args, **kwargs):
        #super(EditProfileForm, self).__init__(*args, **kwargs)

    def clean_signature(self):
        value = self.cleaned_data['signature'].strip()
        if len(re.findall(r'\n', value)) > pybb_settings.SIGNATURE_MAX_LINES:
            raise forms.ValidationError('Number of lines is limited to %d' % pybb_settings.SIGNATURE_MAX_LINES)
        if len(value) > pybb_settings.SIGNATURE_MAX_LENGTH:
            raise forms.ValidationError('Length of signature is limited to %d' % pybb_settings.SIGNATURE_MAX_LENGTH)
        return value

class EditPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['markup', 'body']

    def save(self):
        post = super(EditPostForm, self).save(commit=False)
        post.updated = datetime.now()
        post.save()
        return post


class UserSearchForm(forms.Form):
    query = forms.CharField(required=False, label='')

    def filter(self, qs):
        if self.is_valid():
            query = self.cleaned_data['query']
            return qs.filter(username__contains=query)
        else:
            return qs


class CreatePMForm(forms.ModelForm):
    recipient = forms.CharField(label=_('Recipient'))

    class Meta:
        model = PrivateMessage
        fields = ['subject', 'body', 'markup']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(CreatePMForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['recipient', 'subject', 'body', 'markup']


    def clean_recipient(self):
        name = self.cleaned_data['recipient']
        try:
            user = User.objects.get(username=name)
        except User.DoesNotExist:
            raise forms.ValidationError(_('User with login %s does not exist') % name)
        else:
            return user
    def save(self):
        pm = PrivateMessage(src_user=self.user, dst_user=self.cleaned_data['recipient'])
        pm = forms.save_instance(self, pm)
        return pm
