Example project
===============

Project tree contains two example projects in `test/example_bootstrap` and `test/example_thirdparty` folders,
it is fully deployed and ready to use forum applications. Only one distinction between this projects:
example_bootstrap includes Twitter bootstrap's less files while example_thirdparty leave this to thirdparty apps -
pinax-theme-bootstrap, django-forms-bootstrap and pinax-theme-bootstrap-account. We recommend to use thirdparty apps to start with.
If you starting from scratch it's probaly the best way to begin.

Running example project
-----------------------

You need to install next packages for running example projects:

* pybb
* south

For example_bootstrap project also install django-registration application

you can do it by running this command::

    pip install pybbm south django-registration

or with easy_install::

    easy_install pybbm south django-registration

To run example_thirdparty project you need to install next apps:

* django-user-accounts
* pinax-theme-bootstrap
* django-forms-bootstrap
* pinax-theme-bootstrap-account

Example directory contains requirements.txt file, you can run::

    pip install -r requirements.txt

to install all dependencies.

