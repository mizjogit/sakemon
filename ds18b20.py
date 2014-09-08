#!/usr/bin/env python

import os
import glob
import time

# load the kernel modules needed to handle the sensor
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# find the path of a sensor directory that starts with 28
devicelist = glob.glob('/sys/bus/w1/devices/28*')
# append the device file name to get the absolute path of the sensor 
devicefile = devicelist[0] + '/w1_slave'

# open the file representing the sensor.
fileobj = open(devicefile,'r')
lines = fileobj.readlines()
fileobj.close()

# print the lines read from the sensor apart from the extra \n chars
print(lines[0][:-1])
print(lines[1][:-1])
