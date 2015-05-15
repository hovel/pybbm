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

Each example directory contains requirements.txt file, you can run::

    pip install -r requirements.txt

to install all dependencies.

Also `example_bootstrap/fixtures` directory contains `demo_data.json` file with some example data.
So, you can run::

    python manage.py loaddata <path to example_bootstrap>/fixtures/demo_data.json

from root directory to load some models in you database.
