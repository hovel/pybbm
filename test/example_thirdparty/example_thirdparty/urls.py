# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from account.views import ChangePasswordView, SignupView, LoginView
from django.conf.urls import include, url
from django.contrib import admin
from example_thirdparty.forms import SignupFormWithCaptcha

urlpatterns = [
    url(r'^admin/', include(admin.site.urls) if django.VERSION < (1, 10) else admin.site.urls),

    # aliases to match original django-registration urls
    url(r"^accounts/password/$", ChangePasswordView.as_view(),
        name="auth_password_change"),
    url(r"^accounts/signup/$",
        SignupView.as_view(form_class=SignupFormWithCaptcha),
        name="registration_register"),
    url(r"^accounts/login/$", LoginView.as_view(), name="auth_login"),

    url(r'^accounts/', include('account.urls')),
    url(r'^captcha/', include('captcha.urls')),
    url(r'^', include('pybb.urls', namespace='pybb')),
]
