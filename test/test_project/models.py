import django

if django.VERSION[:2] >= (1, 5):
    from django.db import models
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
        is_staff = models.BooleanField('staff')
        is_active = models.BooleanField('active', default=True)
        date_joined = models.DateTimeField('date joined', default=timezone.now)

        USERNAME_FIELD = 'username'

        objects = CustomUserManager()

        class Meta:
            abstract = False