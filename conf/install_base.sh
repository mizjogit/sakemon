#!/bin/bash
apt-get -y  update;
apt-get -y  upgrade;
apt-get -y install mysql-server;
apt-get -y install mysql-client;
apt-get -y install python-mysqldb;
apt-get -y install libmysqlclient-dev;
apt-get -y install python;
apt-get -y install python-dev;
apt-get -y install python-virtualenv;
pip install virtualenv;
pip install virtualenvwrapper;
export WORKON_HOME=~/Envs;
mkdir -p $WORKON_HOME;
source /usr/local/bin/virtualenvwrapper.sh;
mkvirtualenv sakemon;
workon sakemon;
pip install -r ~/sakemon/requirements.txt
apt-get install supervisor
