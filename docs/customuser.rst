How to integrate custom user model in pybbm forum
=================================================

`Custom user model <https://docs.djangoproject.com/en/1.5/topics/auth/customizing/#substituting-a-custom-user-model>`_
is a great feature introduced in django framework since version 1.5. This topic describes how
to integrate your custom user model in pybbm forum application.

First of all pybbm uses some fields from standard User model and permission system.
The simplest way to make your custom model compatible with pybbm is to inherite from
`django.contrib.auth.models.AbstractUser`
Second way is to meet next requirments:
* define USERNAME_FIELD constant, which point to unique field on your model
* define email, is_staff, is_superuser fields or properties
* inherite from `django.contib.auth.models.PermissionsMixin` or reproduce django's
default permission system