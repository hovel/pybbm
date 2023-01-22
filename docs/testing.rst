Testing
=======

PyBBM has good unittest coverage. There is two way to test pybbm: a "multi-env way" via tox
(multiple versions of Django, Python...), and a "local env way" with your
version of python and locally installed python packages.


Testing with tox (recommended)
------------------------------

This is the recommended way to test pybbm if you want to contribute.
You must have tox installed on your system. (eg: `sudo pip install tox`)

1) Clone your github pybbm fork and go in its directory::

    git clone git@github.com:yourGithubUsername/pybbm.git
    cd pybbm

2) run tox::

    tox

That's all ;-). Tox will tests pybbm in multiple environnements configured in the pybbm's tox.ini.
If you want to test only a specific environment from that list, you can run tox with the "-e"
option. For example, this command will test pybbm only with python 2.7 and Django 1.8::

    tox -e py27-django18

There is a special tox env to check code coverage called `coverage`. By running it, it will output
a summary of code coverage and will generate a HTML rapport (in `htmlcov/index.html`) to see which
part of code is not yet tested.

**If you add new features to pybbm, ensure that lines you add are covered by tests** ;-)


Testing in your local environment
-----------------------------------

If you want to contribute, you should use the "tox way" to test your contributions before
creating a pull-request ! This testing way will allow you to test pybbm in your current local
environment. It is usefull if you have a specific environment which is not covered by tox.ini.

If you already have a working pybb in your environment, you can go to the step 4.
Else, steps 1-3 will allow you to have a minimal environment to run pybb test project.

1) Your environment must be ready to use pip and install Pillow and lxml python packages.
   For Debian, the simplest way is to install debian python packages with their dependencies::

    sudo apt-get install python-pip python-lxml python-pillow

2) Now, your environment is ready to install python packages via pip. Install pybbm from your
   github fork with the "-e" option to be able to contribute, and install the test requirements::

    mkdir -p ~/tests/ && cd ~/tests/
    pip install --user -e git+git@github.com:yourGithubUsername/pybbm.git#egg=pybbm
    pip install --user -r src/pybbm/test/test_project/requirements_test.txt

3) Now, add your user-local pip install directory and the pybbm directory to your PYTHONPATH::

    export PYTHONPATH=$PYTHONPATH:~/.local/lib/python3.7/site-packages/:~/tests/src/pybbm

4) Now, you have an editable version of pybbm and you can run tests from the "test_project"::

    cd ~/tests/src/pybbm/test/test_project/
    python manage.py test pybb

5) If you want to display a coverage summary and create a coverage HTML report::

    pip install --user coveralls
    PATH=$PATH:~/.local/bin/
    cd ~/tests/src/pybbm/test/test_project/
    coverage run --rcfile ../../.coveragerc manage.py test pybb
    coverage report
    coverage html

   Index HTML report is created in `htmlcov/index.html`
