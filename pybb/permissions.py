# -*- coding: utf-8 -*-
"""
Extensible permission system for pybbm
"""

from __future__ import unicode_literals
from django.db.models import Q

from pybb import defaults, util
from pybb.compat import is_authenticated


class DefaultPermissionHandler(object):
    """ 
    Default Permission handler. If you want to implement custom permissions (for example,
    private forums based on some application-specific settings), you can inherit from this
    class and override any of the `filter_*` and `may_*` methods. Methods starting with
    `may` are expected to return `True` or `False`, whereas methods starting with `filter_*`
    should filter the queryset they receive, and return a new queryset containing only the
    objects the user is allowed to see.
    
    To activate your custom permission handler, set `settings.PYBB_PERMISSION_HANDLER` to
    the full qualified name of your class, e.g. "`myapp.pybb_adapter.MyPermissionHandler`".    
    """
    #
    # permission checks on categories
    #
    def filter_categories(self, user, qs):
        """ return a queryset with categories `user` is allowed to see """
        if user.is_superuser or user.is_staff:
            # FIXME: is_staff only allow user to access /admin but does not mean user has extra
            # permissions on pybb models. We should add pybb perm test
            return qs
        return qs.filter(hidden=False)

    def may_view_category(self, user, category):
        """ return True if `user` may view this category, False if not """
        if user.is_superuser or user.is_staff:
            # FIXME: is_staff only allow user to access /admin but does not mean user has extra
            # permissions on pybb models. We should add pybb perm test
            return True
        return not category.hidden

    # 
    # permission checks on forums
    # 
    def filter_forums(self, user, qs):
        """ return a queryset with forums `user` is allowed to see """
        if user.is_superuser or user.is_staff:
            # FIXME: is_staff only allow user to access /admin but does not mean user has extra
            # permissions on pybb models. We should add pybb perm test
            return qs
        return qs.filter(Q(hidden=False) & Q(category__hidden=False))

    def may_view_forum(self, user, forum):
        """ return True if user may view this forum, False if not """
        if user.is_superuser or user.is_staff:
            # FIXME: is_staff only allow user to access /admin but does not mean user has extra
            # permissions on pybb models. We should add pybb perm test
            return True
        return forum.hidden == False and forum.category.hidden == False 

    def may_create_topic(self, user, forum):
        """ return True if `user` is allowed to create a new topic in `forum` """
        if user.is_superuser:
            return True
        return user.has_perm('pybb.add_post')

    #
    # permission checks on topics
    # 
    def filter_topics(self, user, qs):
        """ return a queryset with topics `user` is allowed to see """
        if user.is_superuser:
            return qs
        if user.has_perm('pybb.change_topic'):
            # if I can edit, I can view
            return qs
        if not user.is_staff:
            # FIXME: is_staff only allow user to access /admin but does not mean user has extra
            # permissions on pybb models. We should add pybb perm test
            qs = qs.filter(Q(forum__hidden=False) & Q(forum__category__hidden=False))
        if is_authenticated(user):
            qs = qs.filter(
                # moderator can view on_moderation
                Q(forum__moderators=user) |
                # author can view on_moderation only if there is one post in the topic
                # (mean that post is owned by author)
                Q(user=user, post_count=1) |
                # posts not on_moderation are accessible
                Q(on_moderation=False)
            )
        else:
            qs = qs.filter(on_moderation=False)
        return qs.distinct()

    def may_view_topic(self, user, topic):
        """ return True if user may view this topic, False otherwise """
        if self.may_moderate_topic(user, topic):
            # If i can moderate, it means I can view.
            return True
        if topic.on_moderation:
            if not topic.head.on_moderation:
                # topic is in general moderation waiting (it has been marked as on_moderation
                # but my post is not on_moderation. So it's a manual action we MUST respect)
                return False
            if topic.head.on_moderation and topic.head.user != user:
                # topic is on moderation because of the first post but this is not my post
                # User must not access to it, only it's author can do in moderation mode
                return False
        # FIXME: is_staff only allow user to access /admin but does not mean user has extra
        # permissions on pybb models. We should add pybb perm test
        return user.is_staff or (not topic.forum.hidden and not topic.forum.category.hidden)

    def may_moderate_topic(self, user, topic):
        if user.is_superuser:
            return True
        if not is_authenticated(user):
            return False
        return user.has_perm('pybb.change_topic') or user in topic.forum.moderators.all()

    def may_close_topic(self, user, topic):
        """ return True if `user` may close `topic` """
        return self.may_moderate_topic(user, topic)

    def may_open_topic(self, user, topic):
        """ return True if `user` may open `topic` """
        return self.may_moderate_topic(user, topic)

    def may_stick_topic(self, user, topic):
        """ return True if `user` may stick `topic` """
        return self.may_moderate_topic(user, topic)

    def may_unstick_topic(self, user, topic):
        """ return True if `user` may unstick `topic` """
        return self.may_moderate_topic(user, topic)

    def may_vote_in_topic(self, user, topic):
        """ return True if `user` may unstick `topic` """
        if topic.poll_type == topic.POLL_TYPE_NONE or not is_authenticated(user):
            return False
        elif user.is_superuser:
            return True
        elif not topic.closed and not user.poll_answers.filter(poll_answer__topic=topic).exists():
            return True
        return False

    def may_create_post(self, user, topic):
        """ return True if `user` is allowed to create a new post in `topic` """

        if user.is_superuser:
            return True
        if not defaults.PYBB_ENABLE_ANONYMOUS_POST and not is_authenticated(user):
            return False
        if not self.may_view_topic(user, topic):
            return False
        if not user.has_perm('pybb.add_post'):
            return False
        if topic.closed or topic.on_moderation:
            return self.may_moderate_topic(user, topic)
        return True


    def may_post_as_admin(self, user):
        """ return True if `user` may post as admin """
        if user.is_superuser:
            return True
        # FIXME: is_staff only allow user to access /admin but does not mean user has extra
        # permissions on pybb models. We should add pybb perm test
        return user.is_staff  

    def may_subscribe_topic(self, user, topic):
        """ return True if `user` is allowed to subscribe to a `topic` """
        return not defaults.PYBB_DISABLE_SUBSCRIPTIONS and is_authenticated(user)

    #
    # permission checks on posts
    #    
    def filter_posts(self, user, qs):
        """ return a queryset with posts `user` is allowed to see """

        # first filter by topic availability
        if user.is_superuser:
            return qs
        if user.has_perm('pybb.change_post'):
            # If I can edit all posts, I can view all posts
            return qs
        if not user.is_staff:
            # remove hidden forum/cats posts
            query = Q(topic__forum__hidden=False, topic__forum__category__hidden=False)
        else:
            query = Q(pk__isnull=False)
        if defaults.PYBB_PREMODERATION:
            # remove moderated posts
            query = query & Q(on_moderation=False, topic__on_moderation=False)
        if is_authenticated(user):
            # cancel previous remove if it's my post, or if I'm moderator of the forum
            query = query | Q(user=user) | Q(topic__forum__moderators=user)
        return qs.filter(query).distinct()

    def may_view_post(self, user, post):
        """ return True if `user` may view `post`, False otherwise """
        if user.is_superuser:
            return True
        if self.may_edit_post(user, post):
            # if I can edit, I can view
            return True
        if defaults.PYBB_PREMODERATION and (post.on_moderation or post.topic.on_moderation):
            return False
        # FIXME: is_staff only allow user to access /admin but does not mean user has extra
        # permissions on pybb models. We should add pybb perm test
        return user.is_staff or (not post.topic.forum.hidden and
                                 not post.topic.forum.category.hidden)

    def may_moderate_post(self, user, post):
        if user.is_superuser:
            return True
        return user.has_perm('pybb.change_post') or self.may_moderate_topic(user, post.topic)
        
    def may_edit_post(self, user, post):
        """ return True if `user` may edit `post` """
        if user.is_superuser:
            return True
        return post.user == user or self.may_moderate_post(user, post)

    def may_delete_post(self, user, post):
        """ return True if `user` may delete `post` """
        if user.is_superuser:
            return True
        if not is_authenticated(user):
            return False
        return (defaults.PYBB_ALLOW_DELETE_OWN_POST and post.user == user) or \
               user.has_perm('pybb.delete_post') or \
               user in post.topic.forum.moderators.all()
        # may_moderate_post does not mean that user is a moderator: a user who is not a moderator
        # may_moderate_post if he has change_post perms. For this reason, we need to check
        # if user is really a post's topic moderator.


    def may_admin_post(self, user, post):
        """ return True if `user` may use the admin interface to administrate the `post` """
        if user.is_superuser:
            return True
        return user.is_staff and user.has_perm('pybb.change_post')

    #
    # permission checks on users
    #
    def may_block_user(self, user, user_to_block):
        """ return True if `user` may block `user_to_block` """
        if user.is_superuser:
            return True
        return user.has_perm('pybb.block_users')

    def may_attach_files(self, user):
        """
        return True if `user` may attach files to posts, False otherwise.
        By default controlled by PYBB_ATTACHMENT_ENABLE setting
        """
        return defaults.PYBB_ATTACHMENT_ENABLE

    def may_create_poll(self, user):
        """
        return True if `user` may add poll to posts, False otherwise.
        By default always True
        """
        return True

    def may_edit_topic_slug(self, user):
        """
        returns True if `user` may choose topic's slug, False otherwise.
        When True adds field slug in the Topic form.
        By default always False
        """
        return False

    def may_change_forum(self, user, forum):
        """
        Returns True if the user has the permissions to add modertors to a forum
        By default True if user can change forum
        """
        if user.is_superuser:
            return True
        return user.has_perm('pybb.change_forum')

    def may_manage_moderators(self, user):
        """ return True if `user` may manage moderators"""
        if user.is_superuser:
            return True
        # FIXME: is_staff only allow user to access /admin but does not mean user has extra
        # permissions on pybb models. We should add pybb perm test
        return user.is_staff

perms = util.resolve_class(defaults.PYBB_PERMISSION_HANDLER)
