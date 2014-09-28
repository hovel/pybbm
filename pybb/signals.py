# coding=utf-8
from __future__ import unicode_literals
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, post_delete
from pybb.models import Post
from pybb.subscription import notify_topic_subscribers
from pybb import util, defaults, compat


def post_saved(instance, **kwargs):
    notify_topic_subscribers(instance)

    if util.get_pybb_profile(instance.user).autosubscribe:
        instance.topic.subscribers.add(instance.user)

    if kwargs['created']:
        profile = util.get_pybb_profile(instance.user)
        profile.post_count = instance.user.posts.count()
        profile.save()


def post_deleted(instance, **kwargs):
    profile = util.get_pybb_profile(instance.user)
    profile.post_count = instance.user.posts.count()
    profile.save()


def user_saved(instance, created, **kwargs):
    if not created:
        return

    try:
        add_post_permission = Permission.objects.get_by_natural_key('add_post', 'pybb', 'post')
        add_topic_permission = Permission.objects.get_by_natural_key('add_topic', 'pybb', 'topic')
    except (Permission.DoesNotExist, ContentType.DoesNotExist):
        return
    instance.user_permissions.add(add_post_permission, add_topic_permission)
    instance.save()

    if defaults.PYBB_PROFILE_RELATED_NAME:
        ModelProfile = util.get_pybb_profile_model()
        profile = ModelProfile()
        setattr(instance, defaults.PYBB_PROFILE_RELATED_NAME, profile)
        profile.save()


def setup():
    post_save.connect(post_saved, sender=Post)
    post_delete.connect(post_deleted, sender=Post)
    if defaults.PYBB_AUTO_USER_PERMISSIONS:
        post_save.connect(user_saved, sender=compat.get_user_model())
