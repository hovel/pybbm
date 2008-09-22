from django.conf.urls.defaults import *

from pybb import views
from pybb.feeds import LastPosts

feeds = {
    'posts': LastPosts,
}

urlpatterns = patterns('',
    # Misc
    url('^$', views.index, name='index'),
    url('^category/(?P<category_id>\d+)/$', views.show_category, name='category'),
    url('^forum/(?P<forum_id>\d+)/$', views.show_forum, name='forum'),
    url('^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
        {'feed_dict': feeds}, name='pybb_feed'),

    # User
    url('^user/(?P<username>.*)/$', views.user, name='pybb_profile'),
    url('^profile/edit/$', views.edit_profile, name='edit_profile'),

    # Topic
    url('^topic/(?P<topic_id>\d+)/$', views.show_topic, name='topic'),
    url('^forum/(?P<forum_id>\d+)/topic/add/$', views.add_post,
        {'topic_id': None}, name='add_topic'),

    # Post
    url('^topic/(?P<topic_id>\d+)/post/add/$', views.add_post,
        {'forum_id': None}, name='add_post'),
    url('^post/(?P<post_id>\d+)/$', views.show_post, name='post'),
    url('^post/(?P<post_id>\d+)/edit/$', views.edit_post, name='edit_post'),
)
