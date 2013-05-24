# -*- coding: utf-8 -*-
from test.example_thirdparty.forms import SignupFormWithCaptcha

try:
    from django.conf.urls import patterns, include, url
except ImportError:
    from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

admin.autodiscover()

from account.views import ChangePasswordView, SignupView, LoginView

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),

    # aliases to match original django-registration urls
    url(r"^accounts/password/$", ChangePasswordView.as_view(), name="auth_password_change"),
    url(r"^accounts/signup/$", SignupView.as_view(form_class=SignupFormWithCaptcha), name="registration_register"),
    url(r"^accounts/login/$", LoginView.as_view(), name="auth_login"),

    url(r'^accounts/', include('account.urls')),
    url(r'^captcha/', include('captcha.urls')),
    url(r'^', include('pybb.urls', namespace='pybb')),
)
