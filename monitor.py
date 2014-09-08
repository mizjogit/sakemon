#!/usr/bin/env python

probe=['28-00000405860e','28-00000405bb1e','28-00000405c040']

# get temerature
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
