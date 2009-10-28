from django.db.models.signals import post_save
from django.contrib.auth.models import User

from pybb.subscription import notify_topic_subscribers, notify_pm_recipients
from pybb.models import Post, PrivateMessage

def post_saved(instance, **kwargs):
    notify_topic_subscribers(instance)

def pm_saved(instance, **kwargs):
    notify_pm_recipients(instance)


def setup_signals():
    post_save.connect(post_saved, sender=Post)
    post_save.connect(pm_saved, sender=PrivateMessage)
