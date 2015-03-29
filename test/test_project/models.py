from __future__ import unicode_literals

import django
from django.core.urlresolvers import reverse
from django.db import models

from pybb.compat import get_user_model_path, get_username_field
from pybb.profiles import PybbProfile

if django.VERSION[:2] >= (1, 5):
    from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
    from django.utils import timezone

    class CustomUserManager(BaseUserManager):
        def create_user(self, username, email=None, password=None, **extra_fields):
            """
            Creates and saves a User with the given username, email and password.
            """
            email = BaseUserManager.normalize_email(email)
            user = self.model(username=username, email=email, is_staff=False, is_active=True, is_superuser=False)

            user.set_password(password)
            user.save(using=self._db)
            return user

    class CustomUser(AbstractBaseUser, PermissionsMixin):
        username = models.CharField('username', unique=True, max_length=100)
        email = models.EmailField('email')
        is_staff = models.BooleanField('staff', default=False)
        is_active = models.BooleanField('active', default=True)
        date_joined = models.DateTimeField('date joined', default=timezone.now)

        USERNAME_FIELD = 'username'

        objects = CustomUserManager()

        class Meta:
            abstract = False


class CustomProfile(PybbProfile):
    user = models.OneToOneField(get_user_model_path(),
        verbose_name='linked account',
        related_name='pybb_customprofile',
        blank=False, null=False,)

    class Meta(object):
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def get_absolute_url(self):
        return reverse('pybb:user', kwargs={'username': getattr(self.user, get_username_field())})

    def get_display_name(self):
        return self.user.get_username()
