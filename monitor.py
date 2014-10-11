#!/usr/bin/env python

import time
import os
import re
import subprocess
import MySQLdb
import requests

db = MySQLdb.connect("localhost","root","Schumacher4","templogger" )

#base_dir = '/sys/bus/w1/devices/'
#device_folder = glob.glob( base_dir + '28*' )[0]
#device_file = device_folder + '/w1_slave'


probe=['28-00000405860e','28-00000405bb1e','28-00000405c040']
speriod=15

humidity=0

#os.system( 'modprobe w1-gpio' )
#os.system( 'modprobe w1-therm' )

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


# This function inserts received data into mysql database - Adjust parameters for your server
def insert_data(probe_number,humidity,temperature):
    print 'Inserting Probe={} Temp={} Humidity={}' .format(probe_number, temperature, humidity)
    mydb = MySQLdb.connect(host='localhost', user='root', passwd='Schumacher4', db='templogger')
    cursor = mydb.cursor()
    cursor.execute ("INSERT INTO data (probe_number,humidity,temperature) VALUES (%s, %s, %s)", (probe_number, humidity, temperature))
    mydb.commit()
    cursor.close()
    r = requests.post("http://localhost:8088/bmanagea/release", {'bid': probe_number})
    print r.status_code
 #   exit()

def read_dht22 (PiPin):
  while (1):
    output = subprocess.check_output(["/home/sakemon/sakemon/Adafruit_DHT", "2302", str(PiPin) ]);
    matches = re.search("Temp =\s+([0-9.]+)", output)
    if (matches):
        temp = float(matches.group(1))
        matches = re.search("Hum =\s+([0-9.]+)", output)
        global humidity 
        humidity = float(matches.group(1))
        break
    time.sleep(1)
  #print "Temperature: %.1f C" % temp
  #print "Humidity:    %.1f %%" % humidity
  insert_data ("3",humidity,temp)


def read_ds18B20 (port):
  w1devicefile = '/sys/bus/w1/devices/' + probe[port] + '/w1_slave'
  temperature = get_temp(w1devicefile)
  insert_data (port,humidity,temperature)


def main():
  while (1):
    read_dht22(22)
  

    for x in range(0,3):
      read_ds18B20(x)
  time.sleep(5)

if __name__=="__main__":
    main()
