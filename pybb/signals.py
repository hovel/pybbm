from django.db.models.signals import post_save
from django.contrib.auth.models import User

from pybb.subscription import notify_topic_subscribers
from pybb.models import Post


def post_saved(instance, **kwargs):
    notify_topic_subscribers(instance)


def setup_signals():
    post_save.connect(post_saved, sender=Post)
