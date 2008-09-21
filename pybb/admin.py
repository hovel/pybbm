# -*- coding: utf-8
from django.contrib import admin
from pybb.models import Category, Forum, Topic, Post, Profile

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'forum_count']

class ForumAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'position', 'topic_count']

class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'forum', 'created', 'head', 'post_count']

class PostAdmin(admin.ModelAdmin):
    list_display = ['topic', 'user', 'created', 'summary']
    search_fields = ['body']

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'time_zone', 'location', 'language']

admin.site.register(Category, CategoryAdmin)
admin.site.register(Forum, ForumAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Profile, ProfileAdmin)
