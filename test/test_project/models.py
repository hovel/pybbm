import django

if django.VERSION[:2] >= (1, 5):
    from django.core.exceptions import ImproperlyConfigured
    from django.db import models
    from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, SiteProfileNotAvailable
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
        is_staff = models.BooleanField('staff')
        is_active = models.BooleanField('active', default=True)
        date_joined = models.DateTimeField('date joined', default=timezone.now)

        USERNAME_FIELD = 'username'

        objects = CustomUserManager()

        class Meta:
            abstract = False

        def get_profile(self):
            """
            Returns site-specific profile for this user. Raises
            SiteProfileNotAvailable if this site does not allow profiles.
            """
            if not hasattr(self, '_profile_cache'):
                from django.conf import settings
                try:
                    app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
                except ValueError:
                    raise SiteProfileNotAvailable(
                        'app_label and model_name should be separated by a dot in '
                        'the AUTH_PROFILE_MODULE setting')
                try:
                    model = models.get_model(app_label, model_name)
                    if model is None:
                        raise SiteProfileNotAvailable(
                            'Unable to load the profile model, check '
                            'AUTH_PROFILE_MODULE in your project settings')
                    self._profile_cache = model._default_manager.using(self._state.db).get(user__id__exact=self.id)
                    self._profile_cache.user = self
                except (ImportError, ImproperlyConfigured):
                    raise SiteProfileNotAvailable
            return self._profile_cache