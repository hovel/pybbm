# -*- coding: utf-8

from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.core.urlresolvers import reverse

from pybb.models import Category, Forum, Topic, Post, Profile, Attachment, PollAnswer

from pybb import util
username_field = util.get_username_field()


class ForumInlineAdmin(admin.TabularInline):
    model = Forum
    fields = ['name', 'hidden', 'position']
    extra = 0

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'hidden', 'forum_count']
    list_per_page = 20
    ordering = ['position']
    search_fields = ['name']
    list_editable = ['position']

    inlines = [ForumInlineAdmin]


class ForumAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'hidden', 'position', 'topic_count', ]
    list_per_page = 20
    raw_id_fields = ['moderators']
    ordering = ['-category']
    search_fields = ['name', 'category__name']
    list_editable = ['position', 'hidden']
    fieldsets = (
        (None, {
                'fields': ('category', 'name', 'hidden', 'position', )
                }
         ),
        (_('Additional options'), {
                'classes': ('collapse',),
                'fields': ('updated', 'description', 'headline', 'post_count', 'moderators')
                }
            ),
        )


class PollAnswerAdmin(admin.TabularInline):
    model = PollAnswer
    fields = ['text', ]
    extra = 0


class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'forum', 'created', 'head', 'post_count', 'poll_type',]
    list_per_page = 20
    raw_id_fields = ['user', 'subscribers']
    ordering = ['-created']
    date_hierarchy = 'created'
    search_fields = ['name']
    fieldsets = (
        (None, {
                'fields': ('forum', 'name', 'user', ('created', 'updated'), 'poll_type',)
                }
         ),
        (_('Additional options'), {
                'classes': ('collapse',),
                'fields': (('views', 'post_count'), ('sticky', 'closed'), 'subscribers')
                }
         ),
        )
    inlines = [PollAnswerAdmin, ]

class TopicReadTrackerAdmin(admin.ModelAdmin):
    list_display = ['topic', 'user', 'time_stamp']
    search_fields = ['user__%s' % username_field]

class ForumReadTrackerAdmin(admin.ModelAdmin):
    list_display = ['forum', 'user', 'time_stamp']
    search_fields = ['user__%s' % username_field]

class PostAdmin(admin.ModelAdmin):
    list_display = ['topic', 'user', 'created', 'updated', 'summary']
    list_per_page = 20
    raw_id_fields = ['user', 'topic']
    ordering = ['-created']
    date_hierarchy = 'created'
    search_fields = ['body']
    fieldsets = (
        (None, {
                'fields': ('topic', 'user')
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
    list_display = ['user', 'time_zone', 'language', 'post_count']
    list_per_page = 20
    ordering = ['-user']
    search_fields = ['user__%s' % username_field]
    fieldsets = (
        (None, {
                'fields': ('time_zone', 'language')
                }
         ),
        (_('Additional options'), {
                'classes': ('collapse',),
                'fields' : ('avatar', 'signature', 'show_signatures')
                }
         ),
        )


class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['file', 'size', 'admin_view_post', 'admin_edit_post']

    def admin_view_post(self, obj):
        return u'<a href="%s">view</a>' % obj.post.get_absolute_url()
    admin_view_post.allow_tags = True
    admin_view_post.short_description = _('View post')

    def admin_edit_post(self, obj):
        return u'<a href="%s">edit</a>' % reverse('admin:pybb_post_change', args=[obj.post.pk])
    admin_edit_post.allow_tags = True
    admin_edit_post.short_description = _('Edit post')


admin.site.register(Category, CategoryAdmin)
admin.site.register(Forum, ForumAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Attachment, AttachmentAdmin)

if util.get_pybb_profile_model() == Profile:
    admin.site.register(Profile, ProfileAdmin)

# This can be used to debug read/unread trackers

#admin.site.register(TopicReadTracker, TopicReadTrackerAdmin)
#admin.site.register(ForumReadTracker, ForumReadTrackerAdmin)