# -*- coding: utf-8 -*-
"""
Extensible permission system for pybbm
"""
from django.utils.importlib import import_module
from django.db.models import Q

from pybb import defaults

def _resolve_class(name):
    """ resolves a class function given as string, returning the function """
    if not name: return False
    modname, funcname = name.rsplit('.', 1)
    return getattr(import_module(modname), funcname)() 

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
        return qs.filter(hidden=False) if not user.is_staff else qs
    
    # 
    # permission checks on forums
    # 
    def filter_forums(self, user, qs):
        """ return a queryset with forums `user` is allowed to see """                
        return qs.filter(Q(hidden=False) & Q(category__hidden=False)) if not user.is_staff else qs
    
    def may_create_topic(self, user, forum):
        """ return True if `user` is allowed to create a new topic in `forum` """
        return user.has_perm('pybb.add_post')
    
    #
    # permission checks on topics
    # 
    def filter_topics(self, user, qs):
        """ return a queryset with topics `user` is allowed to see """
        if not user.is_staff:
            qs = qs.filter(Q(forum__hidden=False) & Q(forum__category__hidden=False))
        if not user.is_superuser:
            if user.is_authenticated():
                qs = qs.filter(Q(forum__moderators=user) | Q(user=user) | Q(on_moderation=False))
            else:
                qs = qs.filter(on_moderation=False)
        return qs
    
    def may_moderate_topic(self, user, topic):
        return user.is_superuser or user in topic.forum.moderators.all()
    
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
    
    def may_create_post(self, user, topic):
        """ return True if `user` is allowed to create a new post in `topic` """
        # if topic is hidden, only staff may post
        if topic.forum.hidden and (not user.is_staff):
            return False
        # if topic is closed, only staff may post
        if topic.closed and (not user.is_staff):
            return False
        # only user which have 'pybb.add_post' permission may post
        return user.has_perm('pybb.add_post')
    
    def may_post_as_admin(self, user):
        """ return True if `user` may post as admin """
        return user.is_staff
    
    #
    # permission checks on posts
    #    
    def filter_posts(self, user, qs):
        """ return a queryset with posts `user` is allowed to see """
        if not defaults.PYBB_PREMODERATION or user.is_superuser:
            # superuser may see all posts, also if premoderation is turned off moderation 
            # flag is ignored
            return qs 
        elif user.is_authenticated():
            # post is visible if user is author, post is not on moderation, or user is moderator
            # for this forum
            qs = qs.filter(Q(user=user) | Q(on_moderation=False) | Q(topic__forum__moderators=user))
        else:
            # anonymous user may not see posts which are on moderation
            qs = qs.filter(on_moderation=False)
        return qs
            
    def may_edit_post(self, user, post):
        """ return True if `user` may edit `post` """
        return user.is_superuser or post.user == user or self.may_moderate_topic(user, post.topic)
        
    def may_delete_post(self, user, post):
        """ return True if `user` may delete `post` """
        return self.may_moderate_topic(user, post.topic)
    
    #
    # permission checks on users
    #
    def may_block_user(self, user, user_to_block):
        """ return True if `user` may block `user_to_block` """
        return user.has_perm('pybb.block_users')
    
perms = _resolve_class(defaults.PYBB_PERMISSION_HANDLER)