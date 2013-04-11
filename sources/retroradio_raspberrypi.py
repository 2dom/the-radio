#!/usr/bin/env python

import serial
import time
import mpd
import os

client = mpd.MPDClient()           # create client object

while 1:
	# Connect and reconnect to mpd
	try:
         	status = client.status()
		break
        except:
		client.connect("localhost", 6600)

# Paramters for the FM-radio imitation - check picture 
# on the github project page for a further explanation
last_station_pos=0;
station_dist=500;
station_width=100;
vol_slope=0.015
vol_fac=1.0

play=True;
select_pressed=0; # optical button pressed
select_travel=0;  # depth of optical button press
# Previous states
switches_last=0;  
poti1_last=0;
poti2_last=0;

# Serial device
arddev = '/dev/ttyAMA0'
baud = 115200

#setup - if a Serial object can't be created, a SerialException will be raised.
while True:
    try:
        ser = serial.Serial(arddev, baud, rtscts=0, timeout=5)

        #break out of while loop when connection is made
        break
    except serial.SerialException:
        print 'waiting for device ' + arddev + ' to be available'
        time.sleep(3)
while True:
	data=ser.readline().rstrip()
	# whait for header 
	if data=='Start':
		# Read everything from serial
		poti1=(int(ser.readline().rstrip())/10)*10;
		poti2=(int(ser.readline().rstrip())/10)*10;
		poti3=int(ser.readline().rstrip());
		station=-int(ser.readline().rstrip());
		select=int(ser.readline().rstrip());
		switches=int(ser.readline().rstrip());
		

		# Distances to current station selector postion	
		station_curr_err=abs(station-last_station_pos)
		station_next_err=abs(station-last_station_pos-station_dist)
		station_prev_err=abs(station-last_station_pos+station_dist)
		# Closest sation selection error
		station_err=min(station_curr_err,station_next_err,station_prev_err)		
		# Reduce volume if error too big
		if station_err>station_width:
			vol_fac=1.0-float((station_err-station_width))*vol_slope
			if vol_fac>1:
				vol_fac=1
			if vol_fac<0:
					vol_fac=0
		else:
			vol_fac=1
	
		# More mpd reconnection code
		while 1:
			try:
               			status = client.status()
				break
            		except:
				client.connect("localhost", 6600)
				client.repeat(1)
				client.play()

		# Button pressed?
		if switches!=switches_last:
			switches_last=switches
			if switches==1:
				client.clear()
				client.load("web-radio")
				client.play()
			if switches==2:
				tracks=client.search('artist','Sesame')
				client.clear()
				for t in tracks:
					client.add(t['file'])
				client.play()
				tracks=client.search('genre','terror')
				for t in tracks:
					client.add(t['file'])
				client.play()

	# Base / treble code	
	#if poti1_last!=poti1:
	#		poti1_last=poti1
	#		os.system("amixer -D equal sset '01. 31 Hz',0 "+ str(poti1) +" % &> /dev/null")
	#		os.system("amixer -D equal sset '02. 63 Hz',0 "+ str((poti1-50)*.8+50) +" % &> /dev/null")
	#		os.system("amixer -D equal sset '03. 125 Hz',0 "+ str((poti1-50)*.5+50) +" % &> /dev/null")
	#		os.system("amixer -D equal sset '04. 250 Hz',0 "+ str((poti1-50)*.2+50) +" % &> /dev/null")
#
#		if poti2_last!=poti2:
#			poti2_last=poti2
#			os.system("amixer -D equal sset '10. 16 kHz',0 "+ str(poti2) +" % &> /dev/null")
#			os.system("amixer -D equal sset '09. 8 kHz',0 "+ str((poti2-50)*.8+50) +" % &> /dev/null")
#			os.system("amixer -D equal sset '08. 4 kHz',0 "+ str((poti2-50)*.5+50) +" % &> /dev/null")
#			os.system("amixer -D equal sset '07. 2 kHz',0 "+ str((poti2-50)*.2+50) +" % &> /dev/null")
#


		# Accumulate optical button movement
		select_travel=select_travel-select
		# Reset if released 
		if select>1:
			select_travel=0;
			select_pressed=0
		if select_travel>0:
			if not select_pressed:
				play= not play
				if (play):
					client.pause()
				else:
					client.play()
				select_pressed=1;
	
		# Change station if closer to next/previous station	
		if (station_next_err<station_curr_err):
			last_station_pos=station+station_dist/2-1;
			client.next()
		if (station_prev_err<station_curr_err):   
                        last_station_pos=station-station_dist/2+1;
                        client.previous()
	 
		# Only use FM radio imitation for web radio
		if switches==1:
			client.setvol(int(poti3*vol_fac))

		if switches==2:
			client.setvol(int(poti3))
ser.close()
client.close()                     # send the close command
client.disconnect()                # disconnect from the server


