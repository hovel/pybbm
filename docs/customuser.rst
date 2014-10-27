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

Next step is to decide which model will store all fields for pybb forum profiles.
This model should be referenced to current User model (custom or default) in OneToOne
relationship. To easily setup such model you can use predefined `pybb.profiles.PybbProfile`
class. If profile model is custom user model itself then you can use `PybbProfile` class
as mixin for adding required fields. For more granunal control of fields in your forum
profile model you may not rely on `PybbProfile` and define all fields from
this model manually. You can use fields from another app (such as `avatar` or `language`),
but you have to define proxy properties in forum profile model and build custom
edit profile view, which will be override default pybb profile edit view in urls.py.

Next define `get_display_name` method for your profile model if you want custom username
rendering everywhere in forum. Default `pybb.Profile` model return user's username field
as display name, base `pybb.profiles.PybbProfile` class trying to return `self.user.get_username()`
or `self.get_username()`.

Last step is to correctly set `PYBB_PROFILE_RELATED_NAME` setting. You have to set this
setting to related_name parameter from profile's model from OneToOne relation to User model.
If you use custom user model and this model is profile model itself, then you have to set
this setting to `None`
