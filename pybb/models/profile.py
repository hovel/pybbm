# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from annoying.fields import AutoOneToOneField

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^annoying\.fields\.AutoOneToOneField"])
except ImportError:
    pass

from pybb.compat import get_user_model_path, get_username_field
from pybb.profiles import PybbProfile

class Profile(PybbProfile):
    """
    Profile class that can be used if you doesn't have
    your site profile.
    """
    user = AutoOneToOneField(get_user_model_path(), related_name='pybb_profile', verbose_name=_('User'))

    class Meta(object):
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')
        app_label = 'pybb'

    def get_absolute_url(self):
        return reverse('pybb:user', kwargs={'username': getattr(self.user, get_username_field())})

    def get_display_name(self):
        return self.user.get_username()
