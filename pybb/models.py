from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

class Category(models.Model):
    name = models.CharField(max_length=80)
    position = models.IntegerField(blank=True, default=0)

    class Meta:
        ordering = ['position']

    def __unicode__(self):
        return self.name

    def forum_count(self):
        return self.forums.all().count()

    def get_absolute_url(self):
        return reverse('category', args=[self.id])


class Forum(models.Model):
    category = models.ForeignKey(Category, related_name='forums')
    name = models.CharField(max_length=80)
    position = models.IntegerField(blank=True, default=0)

    class Meta:
        ordering = ['position']

    def __unicode__(self):
        return self.name

    def topic_count(self):
        return self.topics.all().count()

    def get_absolute_url(self):
        return reverse('forum', args=[self.id])


class Topic(models.Model):
    forum = models.ForeignKey(Forum, related_name='topics')
    name = models.CharField(max_length=255)
    created = models.DateTimeField(null=True)
    updated = models.DateTimeField(null=True)
    user = models.ForeignKey(User)

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        return self.name
    
    def post_count(self):
        return self.posts.all().count()

    @property
    def head(self):
        return self.posts.all().order_by('created')[0]

    @property
    def last_post(self):
        return self.posts.all().order_by('-created')[0]

    def get_absolute_url(self):
        return reverse('topic', args=[self.id])

    def save(self):
        if self.id is None:
            self.created = datetime.now()
        super(Topic, self).save()


class Post(models.Model):
    topic = models.ForeignKey(Topic, related_name='posts')
    user = models.ForeignKey(User, related_name='posts')
    created = models.DateTimeField(blank=True)
    updated = models.DateTimeField(blank=True, null=True)
    body = models.TextField()

    class Meta:
        ordering = ['created']

    def summary(self):
        LIMIT = 50
        tail = len(self.body) > LIMIT and '...' or '' 
        return self.body[:LIMIT] + tail

    __unicode__ = summary

    def save(self):
        if self.created is None:
            self.created = datetime.now()
            self.updated = datetime.now()
        if self.id is None and self.topic is not None:
            self.topic.updated = datetime.now()
            self.topic.save()
        super(Post, self).save()
