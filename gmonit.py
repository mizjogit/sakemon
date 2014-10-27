#!/usr/bin/env python
import functools
import urlparse
import datetime
import os
import random
import dhtreader
import gevent.monkey
import time
import requests

from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import sessionmaker

import gevent
from gevent.pywsgi import WSGIServer
from gevent.coros import Semaphore

from engineconfig import cstring, servahost

import sakidb


probe=['28-00000405860e','28-00000405bb1e','28-00000405c040']
speriod=10

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
	temp = 0
	humidity = 0

    def application(self, environ, start_response):
        response_headers = [('Content-type', 'text/plain')]
        start_response("200 OK", response_headers)
        return iter([])

    def read_ds18B20(self):
	global humidity
	global temp
        while True:
	    for port in range(0,3):
  	    	w1devicefile = '/sys/bus/w1/devices/' + probe[port] + '/w1_slave'
  	    	temp = get_temp(w1devicefile)
    		print 'DS18B20 Probe={0} Temp={1:0.1f} Humidity={2:0.1f}' .format(port, temp, humidity)
		r = requests.post("http://localhost:8088/bmanagea/release", {'bid': port})
		print (r)
            	dte = sakidb.DataTable(probe_number=port,temperature=temp, humidity=humidity)
            	self.session.add(dte)
            	self.session.commit()
            gevent.sleep(self.event_rate)


    def read_dht22(self):
	global humidity
	global temp
        while True:
            try:
               temp,humidity = dhtreader.read(22,22) 
            except TypeError:
               print "Read Error"
 	    print 'DHT22 Probe=3 Temp={1:0.1f} Humidity={2:0.1f}' .format(3, temp, humidity)
	    r = requests.post("http://localhost:8088/bmanagea/release", {'bid': 3})
	    print(r)
            dte = sakidb.DataTable(probe_number=3,temperature=temp,humidity=humidity)
            self.session.add(dte)
            self.session.commit()
            gevent.sleep(self.event_rate)

if __name__ == '__main__':
    global humidity
    semapp = CollectApp(cstring)
    print("Initialising DHT22")
    dhtreader.init()
    time.sleep(3)
    print("Done")
    gevent.spawn(functools.partial(CollectApp.read_dht22, semapp))
    gevent.spawn(functools.partial(CollectApp.read_ds18B20, semapp))
    WSGIServer(('0.0.0.0', 8089), functools.partial(CollectApp.application, semapp)).serve_forever()
