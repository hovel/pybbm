Example projects
================

The PyBBM source code contains two example projects under the ``test/example_bootstrap`` and ``test/example_thirdparty`` directories.
Both are fully deployed and ready to use forum applications.

There is only one difference between these projects:

* ``example_bootstrap`` includes the LESS (a CSS preprocessor) files from Twitter Bootstrap.
* ``example_thirdparty`` leaves this to the thirdparty app ``pinax-theme-bootstrap``.

We recommend to use ``example_thirdparty`` to start with. If you starting from scratch it's probaly the best way to begin.

Running the example projects
----------------------------

The ``example_bootstrap`` project requires the following dependencies:

* ``pybbm``
* ``south``
* ``django-registration``

You can do it by running this command::

    pip install pybbm south django-registration

or with easy_install::

    easy_install pybbm south django-registration

The ``example_thirdparty`` project requires the following dependencies:

* ``pybbm``
* ``south``
* ``django-user-accounts``
* ``pinax-theme-bootstrap``

Example directory contains requirements.txt file, you can run::

    pip install -r requirements.txt

to install all dependencies.

