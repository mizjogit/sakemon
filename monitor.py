#!/home/sakemon/.virtualenvs/sakemon/bin/python 

import time
import os
import re
import subprocess
import MySQLdb
import requests
import dhtreader

#base_dir = '/sys/bus/w1/devices/'
#device_folder = glob.glob( base_dir + '28*' )[0]
#device_file = device_folder + '/w1_slave'

probe=['28-00000405860e','28-00000405bb1e','28-00000405c040']
speriod=10
humidity=0
mydb = MySQLdb.connect(host='localhost', user='root', passwd='Schumacher4', db='templogger')


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
    print 'Inserting Probe={0} Temp={1:0.1f} Humidity={2:0.1f}' .format(probe_number, temperature, humidity)
    cursor = mydb.cursor()
    cursor.execute ("INSERT INTO data (probe_number,humidity,temperature) VALUES (%s, %s, %s)", (probe_number, humidity, temperature))
    cursor.close()
    r = requests.post("http://localhost:8088/bmanagea/release", {'bid': probe_number})
    mydb.commit()

def read_ds18B20 (port):
  w1devicefile = '/sys/bus/w1/devices/' + probe[port] + '/w1_slave'
  temperature = get_temp(w1devicefile)
  insert_data (port,humidity,temperature)


def main():
  global humidity

  dhtreader.init()
  time.sleep(3)

  while (1):
     try:
        temp,humidity = dhtreader.read(22,22) 
     except TypeError:
        print "Read Error"
     insert_data ("3",humidity,temp)

     for x in range(0,3):
        read_ds18B20(x)

     time.sleep(speriod)

if __name__=="__main__":
    main()
