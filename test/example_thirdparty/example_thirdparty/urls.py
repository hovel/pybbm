
import django
from account.views import ChangePasswordView, SignupView, LoginView
from django.urls import include, re_path
from django.contrib import admin
from example_thirdparty.forms import SignupFormWithCaptcha

urlpatterns = [
    re_path(r'^admin/', include(admin.site.urls) if django.VERSION < (1, 10) else admin.site.urls),

    # aliases to match original django-registration urls
    re_path(r"^accounts/password/$", ChangePasswordView.as_view(),
        name="auth_password_change"),
    re_path(r"^accounts/signup/$",
        SignupView.as_view(form_class=SignupFormWithCaptcha),
        name="registration_register"),
    re_path(r"^accounts/login/$", LoginView.as_view(), name="auth_login"),

    re_path(r'^accounts/', include('account.urls')),
    re_path(r'^captcha/', include('captcha.urls')),
    re_path(r'^', include('pybb.urls', namespace='pybb')),
]
