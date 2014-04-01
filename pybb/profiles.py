# coding=utf-8
import functools
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from pybb import defaults
from pybb.compat import get_image_field_class
from pybb.util import get_file_path


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
        default=settings.LANGUAGE_CODE)
    show_signatures = models.BooleanField(_('Show signatures'), blank=True,
        default=True)
    post_count = models.IntegerField(_('Post count'), blank=True, default=0)
    avatar = get_image_field_class()(_('Avatar'), blank=True, null=True,
        upload_to=functools.partial(get_file_path, to='pybb/avatar'))
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