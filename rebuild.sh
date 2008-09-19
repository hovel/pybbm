#!/bin/sh
mysql -e 'drop database pybb'
mysql -e 'create database pybb charset utf8'
./manage.py syncdb --noinput
python fill.py
