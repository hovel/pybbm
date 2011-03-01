from django.db.models.signals import post_save

from pybb.subscription import notify_topic_subscribers
from pybb.models import Post
from django.contrib.auth.models import User, Permission


def post_saved(instance, **kwargs):
    notify_topic_subscribers(instance)

    if instance.user.get_profile().autosubscribe:
        instance.topic.subscribers.add(instance.user)

    profile = instance.user.get_profile()
    profile.post_count = instance.user.posts.count()
    profile.save()

def user_saved(instance, created, **kwargs):
    add_post_permission = Permission.objects.get(codename='add_post', content_type__name='Post')
    add_topic_permission = Permission.objects.get(codename='add_topic', content_type__name='Topic')
    if created:
        instance.user_permissions.add(add_post_permission, add_topic_permission)
        instance.save()

def setup_signals():
    post_save.connect(post_saved, sender=Post)
    post_save.connect(user_saved, sender=User)
