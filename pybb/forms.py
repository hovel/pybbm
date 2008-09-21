import re

from django import forms
from django.conf import settings

from pybb.models import Topic, Post, Profile

class AddPostForm(forms.ModelForm):
    name = forms.CharField()

    class Meta:
        model = Post
        fields = ['body']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.topic = kwargs.pop('topic', None)
        self.forum = kwargs.pop('forum', None)
        super(AddPostForm, self).__init__(*args, **kwargs)
        if self.topic:
            self.fields['name'].widget = forms.HiddenInput()
            self.fields['name'].required = False


    def save(self):
        if self.forum:
            topic = Topic(forum=self.forum,
                          user=self.user,
                          name=self.cleaned_data['name'])
            topic.save()
        else:
            topic = self.topic

        post = Post(topic=topic, user=self.user,
                    body=self.cleaned_data['body'])
        post.save()
        return post


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['site', 'jabber', 'icq', 'msn', 'aim', 'yahoo',
                  'location', 'signature', 'time_zone', 'language',
                  'avatar', 'show_signatures']


    #def __init__(self, *args, **kwargs):
        #super(EditProfileForm, self).__init__(*args, **kwargs)

    def clean_signature(self):
        value = self.cleaned_data['signature'].strip()
        if len(re.findall(r'\n', value)) > settings.PYBB_SIGNATURE_MAX_LINES:
            raise forms.ValidationError('Number of lines is limited to %d' % settings.PYBB_SIGNATURE_MAX_LINES)
        if len(value) > settings.PYBB_SIGNATURE_MAX_LENGTH:
            raise forms.ValidationError('Length of signature is limited to %d' % settings.PYBB_SIGNATURE_MAX_LENGTH)
        return value

