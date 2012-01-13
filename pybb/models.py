from datetime import datetime
import os.path
import uuid

try:
    from hashlib import sha1
except ImportError:
    from sha import sha as sha1

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _

from annoying.fields import AutoOneToOneField
from sorl.thumbnail import ImageField
from pybb.util import unescape

import defaults

from django.conf import settings

# None is safe as default since django settings always have LANGUAGES, MEDIA_ROOT and SECRET_KEY variable set
LANGUAGES = settings.LANGUAGES
MEDIA_ROOT = settings.MEDIA_ROOT
SECRET_KEY = settings.SECRET_KEY
MEDIA_URL = settings.MEDIA_URL

from south.modelsinspector import add_introspection_rules

add_introspection_rules([], ["^annoying\.fields\.JSONField"])
add_introspection_rules([], ["^annoying\.fields\.AutoOneToOneField"])

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

#noinspection PyUnusedLocal
def get_file_path(instance, filename, to='pybb/avatar'):
    """
    This function generate filename with uuid4
    it's useful if:
    - you don't want to allow others to see original uploaded filenames
    - users can upload images with unicode in filenames wich can confuse browsers and filesystem
    """
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join(to, filename)

class Category(models.Model):
    name = models.CharField(_('Name'), max_length=80)
    position = models.IntegerField(_('Position'), blank=True, default=0)
    hidden = models.BooleanField(_('Hidden'), blank=False, null=False, default=False,
        help_text = _('If checked, this category will be visible only for staff')
    )

    class Meta(object):
        ordering = ['position']
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __unicode__(self):
        return self.name

    def forum_count(self):
        return self.forums.all().count()

    def get_absolute_url(self):
        return reverse('pybb:category', kwargs={'pk': self.id})

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
    description = models.TextField(_('Description'), blank=True)
    moderators = models.ManyToManyField(User, blank=True, null=True, verbose_name=_('Moderators'))
    updated = models.DateTimeField(_('Updated'), blank=True, null=True)
    post_count = models.IntegerField(_('Post count'), blank=True, default=0)
    topic_count = models.IntegerField(_('Topic count'), blank=True, default=0)
    hidden = models.BooleanField(_('Hidden'), blank=False, null=False, default=False)
    readed_by = models.ManyToManyField(User, through='ForumReadTracker', related_name='readed_forums')
    headline = models.TextField(_('Headline'), blank=True, null=True)

    class Meta(object):
        ordering = ['position']
        verbose_name = _('Forum')
        verbose_name_plural = _('Forums')

    def __unicode__(self):
        return self.name

    def update_counters(self):
        self.post_count = Post.objects.filter(topic__forum=self).count()
        self.topic_count = Topic.objects.filter(forum=self).count()
        last_post = self.get_last_post()
        if last_post:
            self.updated = self.last_post.updated or self.last_post.created
        self.save()

    def get_absolute_url(self):
        return reverse('pybb:forum', kwargs={'pk': self.id})

    @property
    def posts(self):
        return Post.objects.filter(topic__forum=self).select_related()

    def get_last_post(self):
        try:
            return self.posts.order_by('-created').select_related()[0]
        except IndexError:
            return None

    @property
    def last_post(self):
        return self.get_last_post()

    def get_parents(self):
        """
        Used in templates for breadcrumb building
        """
        return self.category,


class Topic(models.Model):
    forum = models.ForeignKey(Forum, related_name='topics', verbose_name=_('Forum'))
    name = models.CharField(_('Subject'), max_length=255)
    created = models.DateTimeField(_('Created'), null=True)
    updated = models.DateTimeField(_('Updated'), null=True)
    user = models.ForeignKey(User, verbose_name=_('User'))
    views = models.IntegerField(_('Views count'), blank=True, default=0)
    sticky = models.BooleanField(_('Sticky'), blank=True, default=False)
    closed = models.BooleanField(_('Closed'), blank=True, default=False)
    subscribers = models.ManyToManyField(
        User,
        related_name='subscriptions',
        verbose_name=_('Subscribers'),
        blank=True
    )
    post_count = models.IntegerField(_('Post count'), blank=True, default=0)
    readed_by = models.ManyToManyField(User, through='TopicReadTracker', related_name='readed_topics')
    on_moderation = models.BooleanField(_('On moderation'), default=False)

    class Meta(object):
        ordering = ['-created']
        verbose_name = _('Topic')
        verbose_name_plural = _('Topics')

    def __unicode__(self):
        return self.name

    @property
    def head(self):
        """
        Get first post and cache it for request
        """
        if not hasattr(self, "_head"):
            self._head = self.posts.all().order_by('created')
        if not len(self._head):
            return None
        return self._head[0]

    def get_last_post(self):
        return self.posts.order_by('-created').select_related()[0]

    @property
    def last_post(self):
        return self.get_last_post()

    def get_absolute_url(self):
        return reverse('pybb:topic', kwargs={'pk': self.id})

    def save(self, *args, **kwargs):
        if self.id is None:
            self.created = datetime.now()
        super(Topic, self).save(*args, **kwargs)

    def update_counters(self):
        self.post_count = self.posts.count()
        self.updated = self.last_post.updated or self.last_post.created
        self.save()

    def get_parents(self):
        """
        Used in templates for breadcrumb building
        """
        return self.forum.category, self.forum


class RenderableItem(models.Model):
    """
    Base class for models that has markup, body, body_text and body_html fields.
    """

    class Meta(object):
        abstract = True

    body = models.TextField(_('Message'))
    body_html = models.TextField(_('HTML version'))
    body_text = models.TextField(_('Text version'))

    def render(self):
        self.body_html = defaults.PYBB_MARKUP_ENGINES[defaults.PYBB_MARKUP](self.body)
        # Remove tags which was generated with the markup processor
        text = strip_tags(self.body_html)
        # Unescape entities which was generated with the markup processor
        self.body_text = unescape(text)

class Post(RenderableItem):
    topic = models.ForeignKey(Topic, related_name='posts', verbose_name=_('Topic'))
    user = models.ForeignKey(User, related_name='posts', verbose_name=_('User'))
    created = models.DateTimeField(_('Created'), blank=True)
    updated = models.DateTimeField(_('Updated'), blank=True, null=True)
    user_ip = models.IPAddressField(_('User IP'), blank=True, default='0.0.0.0')
    on_moderation = models.BooleanField(_('On moderation'), default=False)

    class Meta(object):
        ordering = ['created']
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def summary(self):
        LIMIT = 50
        tail = len(self.body) > LIMIT and '...' or ''
        return self.body[:LIMIT] + tail

    __unicode__ = summary

    def save(self, *args, **kwargs):
        now = datetime.now()
        if self.created is None:
            self.created = now
        self.render()

        new = self.pk is None

        super(Post, self).save(*args, **kwargs)

        if new:
            self.topic.updated = now
            self.topic.forum.updated = now
        # If post is topic head and moderated, moderate topic too
        if self.topic.head == self and self.on_moderation == False and self.topic.on_moderation == True:
            self.topic.on_moderation = False
        self.topic.update_counters()
        self.topic.forum.update_counters()

    def get_absolute_url(self):
        return reverse('pybb:post', kwargs={'pk': self.id})

    def delete(self, *args, **kwargs):
        self_id = self.id
        head_post_id = self.topic.posts.order_by('created')[0].id

        if self_id == head_post_id:
            self.topic.delete()
        else:
            super(Post, self).delete(*args, **kwargs)
            self.topic.update_counters()

        self.topic.forum.update_counters()

    def get_parents(self):
        """
        Used in templates for breadcrumb building
        """
        return self.topic.forum.category, self.topic.forum, self.topic,

class PybbProfile(models.Model):
    """
    Abstract class for user profile, site profile should be inherted from this class
    """

    class Meta(object):
        abstract = True
        permissions = (
            ("block_users", "Can block any user"),
        )

    signature = models.TextField(_('Signature'), blank=True,
        max_length=defaults.PYBB_SIGNATURE_MAX_LENGTH)
    signature_html = models.TextField(_('Signature HTML Version'), blank=True,
        max_length=defaults.PYBB_SIGNATURE_MAX_LENGTH + 30)
    time_zone = models.FloatField(_('Time zone'), choices=TZ_CHOICES,
        default=float(defaults.PYBB_DEFAULT_TIME_ZONE))
    language = models.CharField(_('Language'), max_length=10, blank=True,
        choices=settings.LANGUAGES,
        default=dict(settings.LANGUAGES)[settings.LANGUAGE_CODE.split('-')[0]])
    show_signatures = models.BooleanField(_('Show signatures'), blank=True,
        default=True)
    post_count = models.IntegerField(_('Post count'), blank=True, default=0)
    avatar = ImageField(_('Avatar'), blank=True, null=True,
        upload_to=get_file_path)
    autosubscribe = models.BooleanField(_('Automatically subscribe'),
        help_text=_('Automatically subscribe to topics that you answer'),
        default=defaults.PYBB_DEFAULT_AUTOSUBSCRIBE)

    def save(self, *args, **kwargs):
        self.signature_html = defaults.PYBB_MARKUP_ENGINES[defaults.PYBB_MARKUP](self.signature)
        super(PybbProfile, self).save(*args, **kwargs)

    @property
    def avatar_url(self):
        try:
            return self.avatar.url
        except:
            return defaults.PYBB_DEFAULT_AVATAR_URL


class Profile(PybbProfile):
    """
    Profile class that can be used if you doesn't have
    your site profile.
    """
    user = AutoOneToOneField(User, related_name='pybb_profile', verbose_name=_('User'))

    class Meta(object):
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')

    def get_absolute_url(self):
        return reverse('pybb:user', kwargs={'username': self.user.username})


class Attachment(models.Model):

    class Meta(object):
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')

    post = models.ForeignKey(Post, verbose_name=_('Post'), related_name='attachments')
    size = models.IntegerField(_('Size'))
    file = models.FileField(_('File'),
                            upload_to=lambda instance, filename: get_file_path(instance, filename, to=defaults.PYBB_ATTACHMENT_UPLOAD_TO))

    def save(self, *args, **kwargs):
        self.size = self.file.size
        super(Attachment, self).save(*args, **kwargs)

    def size_display(self):
        size = self.size
        if size < 1024:
            return '%db' % size
        elif size < 1024 * 1024:
            return '%dKb' % int(size / 1024)
        else:
            return '%.2fMb' % (size / float(1024 * 1024))


class TopicReadTracker(models.Model):
    """
    Save per user topic read tracking
    """
    class Meta(object):
        verbose_name = _('Topic read tracker')
        verbose_name_plural = _('Topic read trackers')

    user = models.ForeignKey(User, blank=False, null=False)
    topic = models.ForeignKey(Topic, blank=True, null=True)
    time_stamp = models.DateTimeField(auto_now=True)

class ForumReadTracker(models.Model):
    """
    Save per user forum read tracking
    """
    class Meta(object):
        verbose_name = _('Forum read tracker')
        verbose_name_plural = _('Forum read trackers')

    user = models.ForeignKey(User, blank=False, null=False)
    forum = models.ForeignKey(Forum, blank=True, null=True)
    time_stamp = models.DateTimeField(auto_now=True)

from pybb import signals

signals.setup_signals()
