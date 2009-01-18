from django.db.models.signals import post_save
from django.contrib.auth.models import User

from pybb.gravatar import check_gravatar

def user_saved(instance, **kwargs):
    check_gravatar(instance)


post_save.connect(user_saved, sender=User)
