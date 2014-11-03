#!/usr/bin/env python
import functools
import gevent.monkey
import time
import requests
import optparse
import logging
import subprocess
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import gevent
from gevent.pywsgi import WSGIServer

from engineconfig import cstring

import sakidb


logger = logging.getLogger('templogger')
logging.basicConfig()
logger.setLevel(logging.DEBUG)


probe = ['28-00000405860e', '28-00000405bb1e', '28-00000405c040']
speriod = 10

gevent.monkey.patch_all()

#@route('/ioupdate', methods=['POST'])
#def post():
#    for port, value in request.form.items():
#	logger.info("IO Update port=%s value=%s" % (port, value))
#    return " "


def get_ds_temp(port):
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
    def __init__(self, cstring, simulator=None, ports=3):
        self.session = sessionmaker(bind=create_engine(cstring))()
        self.ports = ports
        self.sleep_interval = speriod
        self.unlock_target = 'http://localhost:8088/bmanagea/release'
        if not simulator:
            logger.info("Initialising DHT22")	
            self.get_ds_temp = get_ds_temp
        else:
            self.dhtreader = SimulateDhtReader
            self.get_ds_temp = SimulateDsTemp

    def application(self, environ, start_response):
        response_headers = [('Content-type', 'text/plain')]
        start_response("200 OK", response_headers)
        return iter([])

    def read_ds18B20(self):
        while True:
            for port in xrange(self.ports):
                temp = self.get_ds_temp(port)
                logger.info('DS18B20 Probe={0} Temp={1:0.1f}'.format(port, temp))
                #logger.info('unlocker reply %s' % requests.post(self.unlock_target, {'bid': port}))
                dte = sakidb.DataTable(probe_number=port, temperature=temp)
                self.session.add(dte)
                self.session.commit()
            gevent.sleep(self.sleep_interval)

    def read_dht22(self):
        while True:
	    output = subprocess.check_output(["/home/sakemon/sakemon/Adafruit_DHT", "2302", "22" ]);
    	    matches = re.search("Temp =\s+([0-9.]+)", output)
    	    if (matches):
        	   temp = float(matches.group(1))
           	   matches = re.search("Hum =\s+([0-9.]+)", output)
        	   humidity = float(matches.group(1))
            	   logger.info('DHT22 Probe=3 Temp={1:0.1f} Humidity={2:0.1f}'.format(3, temp, humidity))
           	  #logger.info('unlocker reply %s' % requests.post(self.unlock_target, {'bid': 3}))
            	   dte = sakidb.DataTable(probe_number=3, temperature=temp, humidity=humidity)
            	   self.session.add(dte)
            	   self.session.commit()
            gevent.sleep(self.sleep_interval)

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option("-s", "--simulator", dest="simulator", action="store_true", default=None, help="Run simulator")
    options, args = parser.parse_args()
    semapp = CollectApp(cstring, options.simulator)
    gevent.spawn(functools.partial(CollectApp.read_dht22, semapp))
    #gevent.spawn(functools.partial(CollectApp.read_ds18B20, semapp))
    WSGIServer(('0.0.0.0', 8089), functools.partial(CollectApp.application, semapp)).serve_forever()
