#!/usr/bin/env python
import functools
import urlparse
import datetime
import os
import random

import gevent.monkey

from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import sessionmaker

import gevent
from gevent.pywsgi import WSGIServer
from gevent.coros import Semaphore

from engineconfig import cstring, servahost

import sakidb


probe=['28-00000405860e','28-00000405bb1e','28-00000405c040']
speriod=10
humidity=0

gevent.monkey.patch_all()

def get_temp(devicefile):
    try:
        fileobj = open(devicefile,'r')
        lines = fileobj.readlines()
        fileobj.close()
    except:
        return None

    # get the status from the end of line 1 
    status = lines[0][-4:-1]

    # is the status is ok, get the temperature from line 2
    if status=="YES":
        tempstr= lines[1][-6:-1]
        tempvalue=float(tempstr)/1000
        return(tempvalue)
    else:
        print("There was an error.")
        return None


class CollectApp:
    def __init__(self, cstring, event_rate=10):
        self.event_rate = event_rate
        self.session = sessionmaker(bind=create_engine(cstring))()
        self.temp = 20
        self.loops = 0

    def application(self, environ, start_response):
        response_headers = [('Content-type', 'text/plain')]
        start_response("200 OK", response_headers)
        return iter([])

    def timer(self):
        while True:
            dte = sakidb.DataTable(timestamp=datetime.datetime.now(),
                                   probe_number=random.randint(0, 4),
                                   temperature=self.temp + (self.loops % 5))
            self.loops += 1
            self.session.add(dte)
            self.session.commit()
            gevent.sleep(self.event_rate)

    def read_ds18B20(self):
        while True:
	    for probe in range(0,3):
  	    	w1devicefile = '/sys/bus/w1/devices/' + probe[port] + '/w1_slave'
  	    	temperature = get_temp(w1devicefile)
   	    	#insert_data (port,humidity,temperature)
            	dte = sakidb.DataTable(timestamp=datetime.datetime.now(),
                                   	probe_number=probe,
                                   	temperature=temperature)
            	self.session.add(dte)
            	self.session.commit()
            gevent.sleep(self.event_rate)


if __name__ == '__main__':
    semapp = CollectApp(cstring)
    gevent.spawn(functools.partial(CollectApp.timer, semapp))
    WSGIServer(('0.0.0.0', 8089), functools.partial(CollectApp.application, semapp)).serve_forever()
