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
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        return self.name
    
    def post_count(self):
        return self.posts.all().count()

    @property
    def head(self):
        return self.posts.get(head=True)

    def get_absolute_url(self):
        return reverse('topic', args=[self.id])


class Post(models.Model):
    topic = models.ForeignKey(Topic, related_name='posts')
    user = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(blank=True, null=True)
    body = models.TextField()
    head = models.BooleanField(blank=True, default=False)

    class Meta:
        ordering = ['created']

    def summary(self):
        LIMIT = 50
        tail = len(self.body) > LIMIT and '...' or '' 
        return self.body[:LIMIT] + tail

    __unicode__ = summary
