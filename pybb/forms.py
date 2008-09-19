from django import forms

from pybb.models import Topic, Post

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
