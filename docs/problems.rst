Problems and solutions
======================

South fail to migrate PyBBM on first installation
-------------------------------------------------

If you got problem like::

    _mysql_exceptions.OperationalError: (1005, "Can't create table 'myknight.#sql-2bd_23a' (errno: 121)")

you probably have mysql with innodb engine and buggy south version. Drop all pybbm related tables and run::

    ./manage.py syncdb --all

to directly sync tables.