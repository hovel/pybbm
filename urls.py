from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to
from django.conf import settings
import django.views.static

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', redirect_to, {'url': '/forum/'}),
    (r'^admin/(.*)', admin.site.root),
    (r'', include('account.urls')),
    (r'^forum/', include('pybb.urls')),
)

if (settings.DEBUG):
    urlpatterns += patterns('',
        (r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'),
            django.views.static.serve, {'document_root': settings.MEDIA_ROOT}),
    )
