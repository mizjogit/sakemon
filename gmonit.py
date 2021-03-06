#!/usr/bin/env python
import functools
import gevent.monkey
import time
import requests
import optparse
import logging
import datetime

import subprocess
import re


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import gevent
from gevent.pywsgi import WSGIServer

from engineconfig import cstring

import sakidb
import sys
import Adafruit_DHT
import weather

logger = logging.getLogger('templogger')
logging.basicConfig()
logger.setLevel(logging.DEBUG)


speriod = 15

gevent.monkey.patch_all()


def get_ds_temp(port):
    probe = ['28-0000057c6966', '28-000005879fd0']
    devicefile = '/sys/bus/w1/devices/' + probe[port] + '/w1_slave'
    try:
        with open(devicefile, 'r') as fileobj:
            lines = fileobj.readlines()
    except:
        logger.error("There was an error from %s" % devicefile)
        return None

    # get the status from the end of line 1
    status = lines[0][-4:-1]

    # is the status is ok, get the temperature from line 2
    if status == "YES":
        tempstr = lines[1][-6:-1]
        tempvalue = float(tempstr) / 1000
        return tempvalue
    else:
        logger.error("There was an error from %s status %s" % (devicefile, status))
        return None


class SimulateDhtReader:
    def __init__(self):
        pass

    @staticmethod
    def read(type, dhtpin):
        return 25, 99

def SimulateDsTemp(port):
    return 26

class CollectApp:
    def __init__(self, cstring, simulator=None, ports=2):
        self.session = sessionmaker(bind=create_engine(cstring))()
        self.ports = ports
        self.sleep_interval = speriod
        self.unlock_target = 'http://localhost:8088/bmanagea/release'
        if not simulator:
            logger.info("Initialising DHT22")	
            self.get_ds_temp = get_ds_temp
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(17, GPIO.OUT)
            GPIO.output(17, GPIO.LOW)
            time.sleep(5)
            GPIO.output(17, GPIO.HIGH)
            logger.info("Complete")
            time.sleep(5)
        else:
            self.dhtreader = SimulateDhtReader
            self.get_ds_temp = SimulateDsTemp

    def application(self, environ, start_response):
        response_headers = [('Content-type', 'text/plain')]
        start_response("200 OK", response_headers)
        return iter([])

    def read_ds18B20(self):
    	port_map = {0:'FEXT', 1:'FINT', 2:'KOJI', 3:'RH'}
        while True:
            for port in xrange(self.ports):
                temp = self.get_ds_temp(port)
                if temp is None:
                  logger.info('DS18B20 Read FAIL, Break')
                  break
                logger.info('DS18B20 Probe={0} Temp={1:0.1f}'.format(port, temp))
		dte = sakidb.DataTable(probe_label=port_map[port], temperature=temp, timestamp=datetime.datetime.now())
                #print dte
                self.session.add(dte)
                self.session.commit()
            gevent.sleep(self.sleep_interval)    

    def read_dht22(self):
        while True:
	    humidity, temp = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 22)
   	    if humidity is not None and temp is not None:
	           #print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temp, humidity)
            	   logger.info('DHT22 Probe=3 Temp={1:0.1f} Humidity={2:0.1f}'.format(3, temp, humidity))
            	   dte = sakidb.DataTable(probe_label='RH', temperature=temp, humidity=humidity, timestamp=datetime.datetime.now())
            	   self.session.add(dte)
            	   self.session.commit()
            gevent.sleep(self.sleep_interval)


    def weather(self):
        stations = self.session.query(sakidb.Sensors.label).filter(sakidb.Sensors.sclass == 'EXTEMP').all()
        while True:
            wvals = weather.get()
            for station in stations:
                if station.label in wvals:
                    print wvals[station.label]
                    dte = sakidb.DataTable(probe_label=station.label,
                                           temperature=wvals[station.label]['temp'],
                                           humidity=wvals[station.label]['relhum'],
                                           timestamp=datetime.datetime.now())
                    self.session.merge(dte)
                    self.session.commit()
                    try:
                        result = requests.post(self.unlock_target, {'bid': station.label})
                        logger.info("weather unlocker reply %s" % result)
                    except requests.exceptions.ConnectionError:
                        logger.info("weather unlocker failed")
                else:
                    print "no station", station.label
            gevent.sleep(500)

    def simulator(self):
        while True:
            dte = sakidb.DataTable(probe_label='SIM1',
                                   temperature=datetime.datetime.now().second / 10 + 30,
                                   timestamp=datetime.datetime.now())
            self.session.merge(dte)
            self.session.commit()
            result = requests.post(self.unlock_target, {'bid': 'SIM1'})
            print "simulatpr", result, dte
            gevent.sleep(11)


    def aggregator(self):
        while True:
            sakidb.mtable.check_agg(self.session)
            gevent.sleep(60)

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option("-s", "--simulator", dest="simulator", action="store_true", default=None, help="Run simulator")
    parser.add_option("-w", "--weather", dest="weather", action="store_true", default=None, help="Get basline weather")
    options, args = parser.parse_args()
    semapp = CollectApp(cstring, options.simulator)
    gevent.spawn(functools.partial(CollectApp.weather, semapp))
    if not options.simulator:
        gevent.spawn(functools.partial(CollectApp.read_dht22, semapp))
        gevent.spawn(functools.partial(CollectApp.read_ds18B20, semapp))
    else:
        gevent.spawn(functools.partial(CollectApp.simulator, semapp))
    gevent.spawn(functools.partial(CollectApp.aggregator, semapp))
    WSGIServer(('0.0.0.0', 8089), functools.partial(CollectApp.application, semapp)).serve_forever()
