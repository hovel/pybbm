Installation
============

* Firstly you have to install pybb. You have two ways:
  * Install pybb with easy_install or pip tools
  * Clone pybb repository from http://bitbucket.org/zeus/pybb and place it in your project

* Put `pybb` into settings.INSTALLED_APPS
* Put `include('pybb.urls', namespace='pybb'))` into main project urls.py file::

    urlpatterns = patterns('',
        (r'^forum/', include('pybb.urls', namespace='pybb')),
    )

* Add `pybb.context_processors.processor` to your settings.CONTEXT_PROCESSORS
* Add `pybb.middleware.PybbMiddleware` to your settings.MIDDLEWARE_CLASSES
* Do `manage.py migrate` if you have South installed or 'manage.py syncdb'

* Your base template should provide *content*, *head*, *title* and *breadcrumb* blocks

* If you want to migrate old pybb profiles to your.site.profile use  migrate_profile manage.py command