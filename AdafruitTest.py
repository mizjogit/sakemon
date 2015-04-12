#!/usr/bin/python
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola

import sys

import Adafruit_DHT


# Parse command line parameters.

sensor = Adafruit_DHT.AM2302

humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 22)

# Note that sometimes you won't get a reading and
# the results will be null (because Linux can't
# guarantee the timing of calls to read the sensor).  
# If this happens try again!
if humidity is not None and temperature is not None:
	print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity)
else:
	print 'Failed to get reading. Try again!'
