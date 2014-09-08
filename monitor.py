#!/usr/bin/env python

#import sqlite3
#test`
import os
import time
import glob

probe=['28-00000405860e','28-00000405bb1e','28-00000405c040']


# global variables
speriod=(15*60)-1
#dbname='/var/www/templog.db'
dbname='/root/templog.db'


# store the temperature in the database
#def log_temperature(temp):

#    conn=sqlite3.connect(dbname)
#    curs=conn.cursor()
#    curs.execute("INSERT INTO temps values(datetime('now'), (?))", (temp,))
    # commit the changes
    #conn.commit()
    #conn.close()


# display the contents of the database
#def display_data():

    #conn=sqlite3.connect(dbname)
    #curs=conn.cursor()
    #for row in curs.execute("SELECT * FROM temps"):
    #    print str(row[0])+"	"+str(row[1])
    #conn.close()



# get temerature
# returns None on error, or the temperature as a float
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
#        print(status)
        tempstr= lines[1][-6:-1]
        tempvalue=float(tempstr)/1000
        #print(tempvalue)
        return(tempvalue)
    else:
        print("There was an error.")
        return None


# This is where the program starts 
def main():


	w1devicefile = '/sys/bus/w1/devices/' + probe[0] + '/w1_slave'
	temperature = get_temp(w1devicefile)
	print("PROBE.0="+str(temperature))

	w1devicefile = '/sys/bus/w1/devices/' + probe[1] + '/w1_slave'
	temperature = get_temp(w1devicefile)
	print("PROBE.1="+str(temperature))

	w1devicefile = '/sys/bus/w1/devices/' + probe[2] + '/w1_slave'
	temperature = get_temp(w1devicefile)
	print("PROBE.2="+str(temperature))



if __name__=="__main__":
    main()




