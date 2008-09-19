# -*- coding: utf-8
from django.contrib import admin
from pybb.models import Category, Forum, Topic, Post

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'forum_count']

class ForumAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'position', 'topic_count']

class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'forum', 'created', 'head', 'post_count']

class PostAdmin(admin.ModelAdmin):
    list_display = ['topic', 'user', 'created', 'summary']
    search_fields = ['body']

admin.site.register(Category, CategoryAdmin)
admin.site.register(Forum, ForumAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Post, PostAdmin)
