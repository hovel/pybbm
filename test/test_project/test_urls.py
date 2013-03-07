# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),

    # TODO: we have to break such dependencies in application
    url(r"^accounts/password/$", 'django.contrib.auth.views.password_change', name="auth_password_change"),
    url(r"^accounts/signup/$", 'django.contrib.auth.views.login', name="registration_register", kwargs={'template_name': 'base.html'}),
    url(r"^accounts/login/$", 'django.contrib.auth.views.login', name="auth_login", kwargs={'template_name': 'base.html'}),

    url(r'^', include('pybb.urls', namespace='pybb')),
)
