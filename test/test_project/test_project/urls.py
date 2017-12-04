# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', include(admin.site.urls) if django.VERSION < (1, 10) else admin.site.urls),
    url(r'^', include('pybb.urls', namespace='pybb')),
]
