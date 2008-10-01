What is PYBB?
=============

The main point in development of pybb is to build it so it could be
*easily* integrated to existing django based site. This mean:

* pybb does not provide features like user registration, password restoring.
  It does not provide authentication page. You should use your favorite
  application for such things. You can try well known django-registration
  http://code.google.com/p/django-registration/ or my own implementation 
  http://hg.pydev.ru/django-account. Both applications contain install instruction
  in the distributive. The demo site http://pybb.org use django-account.

* all pybb stuff placed in one application which is called pybb

* I'm trying to stay with KISS principle. At least in the beginning of pybb 
  development. I mean that there are no threaded posts and there is only bbcode
  markup support and there is no multi-level nested categories.


How to install PYBB?
====================

* copy or symlink pybb directory to you project directory
* copy or symlink pybb/static/pybb to you media/pybb" directory
* write {% extends 'pybb/base.html' %} to templates of other modules which you want to use the forum design
* add include('pybb.urls')) to the urlpatterns
* add pybb to the INSTALLED_APPS
* add pybb settings to main settings file (take pybb settings from the settings file of the example project from the repo)
* make syncdb

How to glue PYBB with account application?
==========================================
* For registration, login, logout links PYBB uses reverse and url template tag
  with names same to django-registration application. Django-account uses the same
  names too. This mean that if you want use one of these two application then
  all you need is to correctly install one.
* If you account application use specific url names or don't use them at all then
  you have two ways:
  * edit PYBB sources and write correct urls
  * add required url names to account application urlpatterns
