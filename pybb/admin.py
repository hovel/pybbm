# -*- coding: utf-8
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from pybb.models import Category, Forum, Topic, Post, Profile, Read

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'forum_count']
    list_per_page = 20
    ordering = ['position']
    search_fields = ['name']

class ForumAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'position', 'topic_count']
    list_per_page = 20
    raw_id_fields = ['moderators']
    ordering = ['-category']
    search_fields = ['name', 'category__name']
    fieldsets = (
        (None, {
                'fields': ('category', 'name', 'updated')
                }
         ),
        (_('Additional options'), {
                'classes': ('collapse',),
                'fields': ('position', 'description', 'post_count', 'moderators')
                }
            ),
        )

class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'forum', 'created', 'head', 'post_count']
    list_per_page = 20
    raw_id_fields = ['user', 'forum', 'subscribers']
    ordering = ['-created']
    date_hierarchy = 'created'
    search_fields = ['name']
    fieldsets = (
        (None, {
                'fields': ('forum', 'name', 'user', ('created', 'updated'))
                }
         ),
        (_('Additional options'), {
                'classes': ('collapse',),
                'fields': (('views', 'post_count'), ('sticky', 'closed'), 'subscribers')
                }
         ),
        )

class PostAdmin(admin.ModelAdmin):
    list_display = ['topic', 'user', 'created', 'updated', 'summary']
    list_per_page = 20
    raw_id_fields = ['user', 'topic']
    ordering = ['-created']
    date_hierarchy = 'created'
    search_fields = ['body']
    fieldsets = (
        (None, {
                'fields': ('topic', 'user', 'markup')
                }
         ),
        (_('Additional options'), {
                'classes': ('collapse',),
                'fields' : (('created', 'updated'), 'user_ip')
                }
         ),
        (_('Message'), {
                'fields': ('body', 'body_html', 'body_text')
                }
         ),
        )

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'time_zone', 'location', 'language']
    list_per_page = 20
    raw_id_fields = ['user']
    ordering = ['-user']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    fieldsets = (
        (None, {
                'fields': ('user', 'time_zone', 'markup', 'location', 'language')
                }
         ),
        (_('IM'), {
                'classes': ('collapse',),
                'fields' : ('jabber', 'icq', 'msn', 'aim', 'yahoo')
                }
         ),
        (_('Additional options'), {
                'classes': ('collapse',),
                'fields' : ('site', 'avatar', 'signature', 'show_signatures')
                }
         ),
        (_('Ban options'), {
                'classes': ('collapse',),
                'fields' : ('ban_status', 'ban_till')
                }
         ),
        )

class ReadAdmin(admin.ModelAdmin):
    list_display = ['user', 'topic', 'time']
    list_per_page = 20
    raw_id_fields = ['user', 'topic']
    ordering = ['-time']
    date_hierarchy = 'time'
    search_fields = ['user__username', 'topic__name']

admin.site.register(Category, CategoryAdmin)
admin.site.register(Forum, ForumAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Read, ReadAdmin)
