from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', redirect_to, {'url': '/forum/'}),
    (r'^admin/(.*)', admin.site.root),
    (r'', include('account.urls')),
    (r'^forum/', include('board.urls')),
    (r'', include('debug.urls')),
)
