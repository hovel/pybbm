import re

from django.conf.urls.defaults import *
from django.conf import settings
import django.views.static

from debug import views

urlpatterns = patterns('',
    # This need if you want your debug server to serve static files
    # Check you MEDIA_URL and MEDIA_ROOT settings!
    (r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'),
        django.views.static.serve, {'document_root': settings.MEDIA_ROOT}),
    # This need if you want to see EXPLAIN of sql queries
    (r'^explain_query/$', views.explain_query),
)
