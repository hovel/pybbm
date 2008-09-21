from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.html import strip_tags
from django.conf import settings

from pybb.markups import mypostmarkup 
from pybb.fields import AutoOneToOneField, ExtendedImageField

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

    @property
    def topics(self):
        return Topic.objects.filter(forum__category=self).select_related()
    
    @property
    def posts(self):
        return Post.objects.filter(topic__forum__category=self).select_related()


class Forum(models.Model):
    category = models.ForeignKey(Category, related_name='forums')
    name = models.CharField(max_length=80)
    position = models.IntegerField(blank=True, default=0)
    description = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['position']

    def __unicode__(self):
        return self.name

    def topic_count(self):
        return self.topics.all().count()

    def get_absolute_url(self):
        return reverse('forum', args=[self.id])
    
    @property
    def posts(self):
        return Post.objects.filter(topic__forum=self).select_related()

    @property
    def last_post(self):
        posts = self.posts.order_by('-created').select_related()
        if posts.count():
            return posts[0]


class Topic(models.Model):
    forum = models.ForeignKey(Forum, related_name='topics')
    name = models.CharField(max_length=255)
    created = models.DateTimeField(null=True)
    updated = models.DateTimeField(null=True)
    user = models.ForeignKey(User)
    views = models.IntegerField(blank=True, default=0)

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        return self.name
    
    def post_count(self):
        return self.posts.all().count()

    @property
    def head(self):
        return self.posts.all().order_by('created').select_related()[0]

    @property
    def last_post(self):
        return self.posts.all().order_by('-created').select_related()[0]

    def get_absolute_url(self):
        return reverse('topic', args=[self.id])

    def save(self, *args, **kwargs):
        if self.id is None:
            self.created = datetime.now()
        super(Topic, self).save(*args, **kwargs)

    def update_read(self, user):
        read, new = Read.objects.get_or_create(user=user, topic=self)
        if not new:
            read.time = datetime.now()
            read.save()

    def has_unreads(self, user):
        try:
            read = Read.objects.get(user=user, topic=self)
        except Read.DoesNotExist:
            return True
        else:
            return bool(self.posts.filter(created__gt=read.time).count())


class Post(models.Model):
    topic = models.ForeignKey(Topic, related_name='posts')
    user = models.ForeignKey(User, related_name='posts')
    created = models.DateTimeField(blank=True)
    updated = models.DateTimeField(blank=True, null=True)
    body = models.TextField()
    body_html = models.TextField()
    body_text = models.TextField()
    user_ip = models.IPAddressField(blank=True, default='')


    class Meta:
        ordering = ['created']

    def summary(self):
        LIMIT = 50
        tail = len(self.body) > LIMIT and '...' or '' 
        return self.body[:LIMIT] + tail

    __unicode__ = summary

    def save(self, *args, **kwargs):
        if self.created is None:
            self.created = datetime.now()
        self.body_html = mypostmarkup.markup(self.body)
        self.body_text = strip_tags(self.body_html)
        if self.id is None and self.topic is not None:
            self.topic.updated = datetime.now()
            self.topic.save()
        super(Post, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('post', args=[self.id])


LANGUAGE_CHOICES = (
    ('en', 'English'),
)

TZ_CHOICES = [(float(x[0]), x[1]) for x in (
    (-12, '-12'), (-11, '-11'), (-10, '-10'), (-9.5, '-09.5'), (-9, '-09'),
    (-8.5, '-08.5'), (-8, '-08 PST'), (-7, '-07 MST'), (-6, '-06 CST'),
    (-5, '-05 EST'), (-4, '-04 AST'), (-3.5, '-03.5'), (-3, '-03 ADT'),
    (-2, '-02'), (-1, '-01'), (0, '00 GMT'), (1, '+01 CET'), (2, '+02'),
    (3, '+03'), (3.5, '+03.5'), (4, '+04'), (4.5, '+04.5'), (5, '+05'),
    (5.5, '+05.5'), (6, '+06'), (6.5, '+06.5'), (7, '+07'), (8, '+08'),
    (9, '+09'), (9.5, '+09.5'), (10, '+10'), (10.5, '+10.5'), (11, '+11'),
    (11.5, '+11.5'), (12, '+12'), (13, '+13'), (14, '+14'))]

class Profile(models.Model):
    user = AutoOneToOneField(User, related_name='pybb_profile')
    site = models.URLField(verify_exists=False, blank=True, default='')
    jabber = models.CharField(max_length=80, blank=True, default='')
    icq = models.CharField(max_length=12, blank=True, default='')
    msn = models.CharField(max_length=80, blank=True, default='')
    aim = models.CharField(max_length=80, blank=True, default='')
    yahoo = models.CharField(max_length=80, blank=True, default='')
    location = models.CharField(max_length=30, blank=True, default='')
    signature = models.TextField(blank=True, default='', max_length=settings.PYBB_SIGNATURE_MAX_LENGTH)
    time_zone = models.FloatField(choices=TZ_CHOICES, default=float(settings.PYBB_DEFAULT_TIME_ZONE))
    language = models.CharField(max_length=3, blank=True, default='en', choices=LANGUAGE_CHOICES)
    avatar = ExtendedImageField(blank=True, default='', upload_to=settings.PYBB_AVATARS_UPLOAD_TO, width=settings.PYBB_AVATAR_WIDTH, height=settings.PYBB_AVATAR_HEIGHT)
    show_signatures = models.BooleanField(blank=True, default=True)


class Read(models.Model):
    """
    For each topic that user has entered the time 
    is logged to this model.
    """

    user = models.ForeignKey(User)
    topic = models.ForeignKey(Topic)
    #forum = models.ForeignKey(Forum)
    time = models.DateTimeField(blank=True)

    def save(self, *args, **kwargs):
        if self.time is None:
            self.time = datetime.now()
        super(Read, self).save(*args, **kwargs)

    class Meta:
        unique_together = ['user', 'topic']


#class Setting(model.Model):
    #topic_page_size = models.IntegerField(blank=True, default=20)
    #forum_page_size = models.IntegerField(blank=True, default=20)
    #default_time_zone = models.FloatField(blank=True, default=3.0, choices=TZ_CHOICES)
    #signature_max_length = models.integer_field(blank=true, default=1024)
    #signature_max_lines = models.integer_field(blank=true, default=3)
    #quick_topics_number = models.integer_field(blank=true, default=10)
    #quick_posts_number = models.integer_field(blank=true, default=10)
    #read_timeout = models.integer_field(blank=true, default=3600 * 24 * 7)
    #header = models.CharField(blank=True, default='pybb')
    #tagline = models.CharField(blank=True, default='Django based forum engine')
