from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.html import escape, strip_tags
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
#from django.contrib.markup.templatetags.markup import markdown
from markdown import Markdown

from pybb.markups import mypostmarkup 
from pybb.fields import AutoOneToOneField, ExtendedImageField
from pybb.subscription import notify_subscribers
from pybb.util import urlize

LANGUAGE_CHOICES = (
    ('en', 'English'),
    ('ru', _('Russian')),
)

TZ_CHOICES = [(float(x[0]), x[1]) for x in (
    (-12, '-12'), (-11, '-11'), (-10, '-10'), (-9.5, '-09.5'), (-9, '-09'),
    (-8.5, '-08.5'), (-8, '-08 PST'), (-7, '-07 MST'), (-6, '-06 CST'),
    (-5, '-05 EST'), (-4, '-04 AST'), (-3.5, '-03.5'), (-3, '-03 ADT'),
    (-2, '-02'), (-1, '-01'), (0, '00 GMT'), (1, '+01 CET'), (2, '+02'),
    (3, '+03'), (3.5, '+03.5'), (4, '+04'), (4.5, '+04.5'), (5, '+05'),
    (5.5, '+05.5'), (6, '+06'), (6.5, '+06.5'), (7, '+07'), (8, '+08'),
    (9, '+09'), (9.5, '+09.5'), (10, '+10'), (10.5, '+10.5'), (11, '+11'),
    (11.5, '+11.5'), (12, '+12'), (13, '+13'), (14, '+14'),
)]

MARKUP_CHOICES = (
    ('bbcode', 'bbcode'),
    ('markdown', 'markdown'),
)


class Category(models.Model):
    name = models.CharField(_('Name'), max_length=80)
    position = models.IntegerField(_('Position'), blank=True, default=0)

    class Meta:
        ordering = ['position']
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __unicode__(self):
        return self.name

    def forum_count(self):
        return self.forums.all().count()

    def get_absolute_url(self):
        return reverse('pybb_category', args=[self.id])

    @property
    def topics(self):
        return Topic.objects.filter(forum__category=self).select_related()
    
    @property
    def posts(self):
        return Post.objects.filter(topic__forum__category=self).select_related()


class Forum(models.Model):
    category = models.ForeignKey(Category, related_name='forums', verbose_name=_('Category'))
    name = models.CharField(_('Name'), max_length=80)
    position = models.IntegerField(_('Position'), blank=True, default=0)
    description = models.TextField(_('Description'), blank=True, default='')
    moderators = models.ManyToManyField(User, blank=True, null=True, verbose_name=_('Moderators'))
    updated = models.DateTimeField(_('Updated'), null=True)
    post_count = models.IntegerField(_('Post count'), blank=True, default=0)

    class Meta:
        ordering = ['position']
        verbose_name = _('Forum')
        verbose_name_plural = _('Forums')

    def __unicode__(self):
        return self.name

    def topic_count(self):
        return self.topics.all().count()

    def get_absolute_url(self):
        return reverse('pybb_forum', args=[self.id])
    
    @property
    def posts(self):
        return Post.objects.filter(topic__forum=self).select_related()

    @property
    def last_post(self):
        posts = self.posts.order_by('-created').select_related()
        try:
            return posts[0]
        except IndexError:
            return None


class Topic(models.Model):
    forum = models.ForeignKey(Forum, related_name='topics', verbose_name=_('Forum'))
    name = models.CharField(_('Subject'), max_length=255)
    created = models.DateTimeField(_('Created'), null=True)
    updated = models.DateTimeField(_('Updated'), null=True)
    user = models.ForeignKey(User, verbose_name=_('User'))
    views = models.IntegerField(_('Views count'), blank=True, default=0)
    sticky = models.BooleanField(_('Sticky'), blank=True, default=False)
    closed = models.BooleanField(_('Closed'), blank=True, default=False)
    subscribers = models.ManyToManyField(User, related_name='subscriptions', verbose_name=_('Subscribers'), blank=True)
    post_count = models.IntegerField(_('Post count'), blank=True, default=0)

    class Meta:
        ordering = ['-created']
        verbose_name = _('Topic')
        verbose_name_plural = _('Topics')

    def __unicode__(self):
        return self.name
    
    @property
    def head(self):
        return self.posts.all().order_by('created').select_related()[0]

    @property
    def last_post(self):
        return self.posts.all().order_by('-created').select_related()[0]

    def get_absolute_url(self):
        return reverse('pybb_topic', args=[self.id])

    def save(self, *args, **kwargs):
        if self.id is None:
            self.created = datetime.now()
        super(Topic, self).save(*args, **kwargs)

    def update_read(self, user):
        read, new = Read.objects.get_or_create(user=user, topic=self)
        if not new:
            read.time = datetime.now()
            read.save()

    #def has_unreads(self, user):
        #try:
            #read = Read.objects.get(user=user, topic=self)
        #except Read.DoesNotExist:
            #return True
        #else:
            #return self.updated > read.time


class RenderableItem(models.Model):
    """
    Base class for models that has markup, body, body_text and body_html fields.
    """

    class Meta:
        abstract = True

    def render(self):
        if self.markup == 'bbcode':
            self.body_html = mypostmarkup.markup(self.body, auto_urls=False)
        elif self.markup == 'markdown':
            self.body_html = unicode(Markdown(self.body, safe_mode='escape'))
        else:
            raise Exception('Invalid markup property: %s' % self.markup)
        self.body_text = strip_tags(self.body_html)
        self.body_html = urlize(self.body_html)


class Post(RenderableItem):
    topic = models.ForeignKey(Topic, related_name='posts', verbose_name=_('Topic'))
    user = models.ForeignKey(User, related_name='posts', verbose_name=_('User'))
    created = models.DateTimeField(_('Created'), blank=True)
    updated = models.DateTimeField(_('Updated'), blank=True, null=True)
    markup = models.CharField(_('Markup'), max_length=15, default=settings.PYBB_DEFAULT_MARKUP, choices=MARKUP_CHOICES)
    body = models.TextField(_('Message'))
    body_html = models.TextField(_('HTML version'))
    body_text = models.TextField(_('Text version'))
    user_ip = models.IPAddressField(_('User IP'), blank=True, default='')


    class Meta:
        ordering = ['created']
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def summary(self):
        LIMIT = 50
        tail = len(self.body) > LIMIT and '...' or '' 
        return self.body[:LIMIT] + tail

    __unicode__ = summary

    def save(self, *args, **kwargs):
        if self.created is None:
            self.created = datetime.now()
        self.render()

        new = self.id is None

        if new:
            self.topic.updated = datetime.now()
            self.topic.post_count += 1
            self.topic.save()
            self.topic.forum.updated = self.topic.updated
            self.topic.forum.post_count += 1
            self.topic.forum.save()

        super(Post, self).save(*args, **kwargs)

        if new:
            notify_subscribers(self)




    def get_absolute_url(self):
        return reverse('pybb_post', args=[self.id])

    def delete(self, *args, **kwargs):
        self_id = self.id
        head_post_id = self.topic.posts.order_by('created')[0].id
        super(Post, self).delete(*args, **kwargs)

        self.topic.post_count -= 1
        self.topic.save()
        self.topic.forum.post_count -= 1
        self.topic.forum.save()

        if self_id == head_post_id:
            self.topic.delete()


class Profile(models.Model):
    user = AutoOneToOneField(User, related_name='pybb_profile', verbose_name=_('User'))
    site = models.URLField(_('Site'), verify_exists=False, blank=True, default='')
    jabber = models.CharField(_('Jabber'), max_length=80, blank=True, default='')
    icq = models.CharField(_('ICQ'), max_length=12, blank=True, default='')
    msn = models.CharField(_('MSN'), max_length=80, blank=True, default='')
    aim = models.CharField(_('AIM'), max_length=80, blank=True, default='')
    yahoo = models.CharField(_('Yahoo'), max_length=80, blank=True, default='')
    location = models.CharField(_('Location'), max_length=30, blank=True, default='')
    signature = models.TextField(_('Signature'), blank=True, default='', max_length=settings.PYBB_SIGNATURE_MAX_LENGTH)
    time_zone = models.FloatField(_('Time zone'), choices=TZ_CHOICES, default=float(settings.PYBB_DEFAULT_TIME_ZONE))
    language = models.CharField(_('Language'), max_length=3, blank=True, default='en', choices=LANGUAGE_CHOICES)
    avatar = ExtendedImageField(_('Avatar'), blank=True, default='', upload_to=settings.PYBB_AVATARS_UPLOAD_TO, width=settings.PYBB_AVATAR_WIDTH, height=settings.PYBB_AVATAR_HEIGHT)
    show_signatures = models.BooleanField(_('Show signatures'), blank=True, default=True)
    markup = models.CharField(_('Default markup'), max_length=15, default=settings.PYBB_DEFAULT_MARKUP, choices=MARKUP_CHOICES)

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')


class Read(models.Model):
    """
    For each topic that user has entered the time 
    is logged to this model.
    """

    user = models.ForeignKey(User, verbose_name=_('User'))
    topic = models.ForeignKey(Topic, verbose_name=_('Topic'))
    time = models.DateTimeField(_('Time'), blank=True)

    class Meta:
        unique_together = ['user', 'topic']
        verbose_name = _('Read')
        verbose_name_plural = _('Reads')

    def save(self, *args, **kwargs):
        if self.time is None:
            self.time = datetime.now()
        super(Read, self).save(*args, **kwargs)


    def __unicode__(self):
        return u'T[%d], U[%d]: %s' % (self.topic.id, self.user.id, unicode(self.time))


class PrivateMessage(RenderableItem):

    dst_user = models.ForeignKey(User, verbose_name=_('Recipient'), related_name='dst_users')
    src_user = models.ForeignKey(User, verbose_name=_('Author'), related_name='src_users')
    read = models.BooleanField(_('Read'), blank=True, default=False)
    created = models.DateTimeField(_('Created'), blank=True)
    markup = models.CharField(_('Markup'), max_length=15, default=settings.PYBB_DEFAULT_MARKUP, choices=MARKUP_CHOICES)
    subject = models.CharField(_('Subject'), max_length=255)
    body = models.TextField(_('Message'))
    body_html = models.TextField(_('HTML version'))
    body_text = models.TextField(_('Text version'))

    class Meta:
        ordering = ['-created']
        verbose_name = _('Private message')
        verbose_name_plural = _('Private messages')

    # TODO: summary and part of the save methid is the same as in the Post model
    # move to common functions
    def summary(self):
        LIMIT = 50
        tail = len(self.body) > LIMIT and '...' or '' 
        return self.body[:LIMIT] + tail

    def __unicode__(self):
        return self.subject

    def save(self, *args, **kwargs):
        if self.created is None:
            self.created = datetime.now()
        self.render()

        new = self.id is None
        super(PrivateMessage, self).save(*args, **kwargs)
        # TODO: make email notifications
        #if new:
            #notify_subscribers(self)


