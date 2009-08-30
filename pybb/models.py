from datetime import datetime
from markdown import Markdown
import os.path
try:
    from hashlib import sha1
except ImportError:
    from sha import sha as sha1

from django.db import models
from django.db.models import F
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from pybb.markups import mypostmarkup
from pybb.fields import AutoOneToOneField, ExtendedImageField
from pybb.util import urlize, memoize_method, unescape
from pybb import settings as pybb_settings

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

MESSAGEBOX_CHOICES = (
    ('inbox', _('Inbox')),
    ('outbox', _('Outbox')),
    ('trash', _('Trash')),
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
            instance = Markdown(safe_mode='escape')
            self.body_html = unicode(instance.convert(self.body))
        else:
            raise Exception('Invalid markup property: %s' % self.markup)

        # Remove tags which was generated with the markup processor
        text = strip_tags(self.body_html)

        # Unescape entities which was generated with the markup processor
        self.body_text = unescape(text)

        self.body_html = urlize(self.body_html)


class Post(RenderableItem):
    topic = models.ForeignKey(Topic, related_name='posts', verbose_name=_('Topic'))
    user = models.ForeignKey(User, related_name='posts', verbose_name=_('User'))
    created = models.DateTimeField(_('Created'), blank=True)
    updated = models.DateTimeField(_('Updated'), blank=True, null=True)
    markup = models.CharField(_('Markup'), max_length=15, default=pybb_settings.DEFAULT_MARKUP, choices=MARKUP_CHOICES)
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
            Topic.objects.filter(id=self.topic_id).update(post_count=F('post_count')+1, updated=datetime.now())
            self.topic.forum.updated = datetime.now()
            self.topic.forum.post_count = Post.objects.filter(topic__forum=self.topic.forum).count()
            self.topic.forum.save()

        super(Post, self).save(*args, **kwargs)


    def get_absolute_url(self):
        return reverse('pybb_post', args=[self.id])


    def delete(self, *args, **kwargs):
        self_id = self.id
        head_post_id = self.topic.posts.order_by('created')[0].id
        super(Post, self).delete(*args, **kwargs)

        if self_id == head_post_id:
            self.topic.forum.post_count -= 1 + self.topic.posts.all().count()
            self.topic.delete()
        else:
            self.topic.post_count -= 1
            self.topic.save()
            self.topic.forum.post_count -= 1

        self.topic.forum.save()


BAN_STATUS = (
(0, _('No')),
(1, _('Caution')),
(2, _('Ban')))

class Profile(models.Model):
    user = AutoOneToOneField(User, related_name='pybb_profile', verbose_name=_('User'))
    site = models.URLField(_('Site'), verify_exists=False, blank=True, default='')
    jabber = models.CharField(_('Jabber'), max_length=80, blank=True, default='')
    icq = models.CharField(_('ICQ'), max_length=12, blank=True, default='')
    msn = models.CharField(_('MSN'), max_length=80, blank=True, default='')
    aim = models.CharField(_('AIM'), max_length=80, blank=True, default='')
    yahoo = models.CharField(_('Yahoo'), max_length=80, blank=True, default='')
    location = models.CharField(_('Location'), max_length=30, blank=True, default='')
    signature = models.TextField(_('Signature'), blank=True, default='', max_length=pybb_settings.SIGNATURE_MAX_LENGTH)
    time_zone = models.FloatField(_('Time zone'), choices=TZ_CHOICES, default=float(pybb_settings.DEFAULT_TIME_ZONE))
    language = models.CharField(_('Language'), max_length=10, blank=True, default='',
                                choices=settings.LANGUAGES)
    avatar = ExtendedImageField(_('Avatar'), blank=True, default='', upload_to=pybb_settings.AVATARS_UPLOAD_TO, width=pybb_settings.AVATAR_WIDTH, height=pybb_settings.AVATAR_HEIGHT)
    show_signatures = models.BooleanField(_('Show signatures'), blank=True, default=True)
    markup = models.CharField(_('Default markup'), max_length=15, default=pybb_settings.DEFAULT_MARKUP, choices=MARKUP_CHOICES)
    ban_status = models.SmallIntegerField(_('Ban status'), default=0, choices=BAN_STATUS)
    ban_till = models.DateTimeField(_('Ban till'), blank=True, null=True, default=None)

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')


    @memoize_method
    def unread_pm_count(self):
        return MessageBox.objects.filter(user=self.user, box='inbox', read=False).count()

    def is_banned(self):
        if self.ban_status == 2:
            if self.ban_till is None or self.ban_till < datetime.now():
                self.ban_status = 0
                self.ban_till = None
                self.save()
                return False
            return True
        return False

    @memoize_method
    def post_count(self):
        """ Use from template, in future may be replace by normalize field

        {% trans 'Posts' %}: {{ post.user.pybb_profile.post_count }}"""
        return self.user.posts.all().count()


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
    thread = models.ForeignKey('self', blank=True, null=True)
    user_box = models.ManyToManyField(User, verbose_name=_('User relation'), through='MessageBox')
    src_user = models.ForeignKey(User, verbose_name=_('Author'), related_name='pm_author')
    dst_user = models.ForeignKey(User, verbose_name=_('Recipient'), related_name='pm_recipient')
    created = models.DateTimeField(_('Created'), blank=True)
    markup = models.CharField(_('Markup'), max_length=15, default=pybb_settings.DEFAULT_MARKUP, choices=MARKUP_CHOICES)
    subject = models.CharField(_('Subject'), max_length=255)
    body = models.TextField(_('Message'))
    body_html = models.TextField(_('HTML version'))
    body_text = models.TextField(_('Text version'))

    class Meta:
        ordering = ['-created']
        verbose_name = _('Private message')
        verbose_name_plural = _('Private messages')

    # TODO: summary and part of the save method is the same as in the Post model
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

    def get_absolute_url(self):
        return reverse('pybb_pm_show_message', args=[self.id])


class MessageBox(models.Model):
    """
    Each private message may belong to one or more message boxes.

    This m2m relationship also defines which message is first
        in any given message thread (first message has head=True)
        and if the thread has unread messages (thread_read)
    """

    message = models.ForeignKey(PrivateMessage)
    user = models.ForeignKey(User)

    box = models.CharField(_('Messagebox'), max_length=15, choices=MESSAGEBOX_CHOICES, db_index=True)
    head = models.BooleanField(db_index=True)
    read = models.BooleanField(default=False)
    thread_read = models.BooleanField(db_index=True, default=False)
    message_count = models.IntegerField(default=1)


class Attachment(models.Model):
    post = models.ForeignKey(Post, verbose_name=_('Post'), related_name='attachments')
    size = models.IntegerField(_('Size'))
    content_type = models.CharField(_('Content type'), max_length=255)
    path = models.CharField(_('Path'), max_length=255)
    name = models.TextField(_('Name'))
    hash = models.CharField(_('Hash'), max_length=40, blank=True, default='', db_index=True)

    def save(self, *args, **kwargs):
        super(Attachment, self).save(*args, **kwargs)
        if not self.hash:
            self.hash = sha1(str(self.id) + settings.SECRET_KEY).hexdigest()
        super(Attachment, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('pybb_attachment', args=[self.hash])

    def size_display(self):
        size = self.size
        if size < 1024:
            return '%db' % size
        elif size < 1024 * 1024:
            return '%dKb' % int(size / 1024)
        else:
            return '%.2fMb' % (size / float(1024 * 1024))


    def get_absolute_path(self):
        return os.path.join(settings.MEDIA_ROOT, pybb_settings.ATTACHMENT_UPLOAD_TO,
                            self.path)


from pybb import signals
signals.setup_signals()
