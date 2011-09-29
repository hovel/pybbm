from django.db.models.signals import post_save
from django.conf import settings

from pybb.subscription import notify_topic_subscribers
from django.contrib.auth.models import User, Permission


def post_saved(instance, **kwargs):
    notify_topic_subscribers(instance)

    if instance.user.get_profile().autosubscribe:
        instance.topic.subscribers.add(instance.user)

    profile = instance.user.get_profile()
    profile.post_count = instance.user.posts.count()
    profile.save()

def user_saved(instance, created, **kwargs):
    if not created:
        return
    try:
        add_post_permission = Permission.objects.get(codename='add_post', content_type__name='Post')
        add_topic_permission = Permission.objects.get(codename='add_topic', content_type__name='Topic')
    except Permission.DoesNotExist:
        return
    instance.user_permissions.add(add_post_permission, add_topic_permission)
    instance.save()
    if settings.AUTH_PROFILE_MODULE == 'pybb.Profile':
        instance.get_profile().save()

def setup_signals():
    from models import Post
    post_save.connect(post_saved, sender=Post)
    post_save.connect(user_saved, sender=User)
