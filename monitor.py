#!/usr/bin/env python

import time
import sqlite3

#globals
dbname='/var/www/templog.db'
probe=['28-00000405860e','28-00000405bb1e','28-00000405c040']
speriod=15

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

def log_temp(temp):
    
   file = open('temp.txt','a')
   print("temperature="+str(temp))
   file.write(str(temp)+',')

   conn=sqlite3.connect(dbname)
   curs=conn.cursor()

   curs.execute("INSERT INTO temps values(datetime('now'), (?))", (temp,))

   # commit the changes
   conn.commit()
   conn.close()


def main():


  while True:
      w1devicefile = '/sys/bus/w1/devices/' + probe[0] + '/w1_slave'
      temperature = get_temp(w1devicefile)
      log_temp(temperature)


      w1devicefile = '/sys/bus/w1/devices/' + probe[1] + '/w1_slave'
      temperature = get_temp(w1devicefile)
      log_temp(temperature)

      w1devicefile = '/sys/bus/w1/devices/' + probe[2] + '/w1_slave'
      temperature = get_temp(w1devicefile)
      log_temp(temperature)

      time.sleep(speriod)

if __name__=="__main__":
    main()
