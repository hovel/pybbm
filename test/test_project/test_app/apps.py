from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class TestApp(AppConfig):
    name = 'test_app'
    verbose_name = _('Pybbm Test App')
    default_auto_field = 'django.db.models.AutoField'
