
import django
from django.urls import include, re_path
from django.contrib import admin

urlpatterns = [
    re_path(r'^admin/', include(admin.site.urls) if django.VERSION < (1, 10) else admin.site.urls),
    re_path(r'^accounts/', include('registration.urls')),
    re_path(r'^', include('pybb.urls', namespace='pybb')),
]
