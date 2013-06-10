#!/usr/bin/env python

import serial
import time
import mpd
import os

client = mpd.MPDClient()           # create client object


# Reconnect
while 1:
	try:
         	status = client.status()
		#tracks=client.search('title','dreamharp')
		#client.clear()
		#for t in tracks:
		#	client.add(t['file'])
		#client.play()
		#client.setvol(80)
		print("Initial connect")
                break
                
        except:
		client.connect("localhost", 6600)
                print("Initial connect failed ...")
		time.sleep(1)
	

# State after power on
list_len=len(client.playlist()) 
status = client.currentsong()
songid=int(status['pos'])

# Position of last station 
last_station_pos=0;
# Distance between stations
station_dist=700;
# with of 100% volume area around stations
station_width=100;
# Outside of station_with volume decreases with slope
vol_slope=0.004
# Volume factor - this is what we change when we operate the station dial
vol_fac=1.0

# Are we playing something
play=True;
# How far deep is the start/stop button press
select_travel=0;
# start/stop button pressed?
select_pressed=0;

# Read previous state of switches from file
f=open('/home/mpd/last_switch.txt','r+');
f.seek(0)
switches_last=int(f.read());
f.close()
poti1_last=0;
poti2_last=0;


# Serial device
arddev = '/dev/ttyAMA0'
baud = 115200

#setup - if a Serial object can't be created, a SerialException will be raised.
while True:
    try:
        ser = serial.Serial(arddev, baud, rtscts=0, timeout=5)
	ser.flushInput()
        #break out of while loop when connection is made
        break
    except serial.SerialException:
        print 'waiting for device ' + arddev + ' to be available'
        time.sleep(3)
while True:
	# New data
	data=ser.readline().rstrip()
	if data=='Start':
		poti1=(int(ser.readline().rstrip())/10)*10;
		poti2=(int(ser.readline().rstrip())/10)*10;
		poti3=ser.readline().rstrip()
		poti3=int(100.0-float(poti3));
		if poti3<55:
			poti3=0
		station=-int(ser.readline().rstrip());
		select=int(ser.readline().rstrip());
		switches=int(ser.readline().rstrip());
		
		#print(poti2)		


		# Calculate station error
		# This is the distance to the current, last and next station
		station_curr_err=abs(station-last_station_pos)
		station_next_err=abs(station-last_station_pos-station_dist)
		station_prev_err=abs(station-last_station_pos+station_dist)
		# The smallest one is the one we work with
		station_err=min(station_curr_err,station_next_err,station_prev_err)		
		# Outside of 100% volume zone
		if station_err>station_width:
			# Compute volume factor based on slope
			vol_fac=1.0-float((station_err-station_width))*vol_slope
			if vol_fac>1:
				vol_fac=1
			if vol_fac<0:
					vol_fac=0
			#print(station_err)
			#print(station_err-station_width)
			#print(vol_fac)
			#print("\n")
		else:
			vol_fac=1
	
		# Check if we are still connected to MPD
		while 1:
			try:
               			status = client.status()
				ser.flushInput()
				break
            		except:
				client.connect("localhost", 6600)
				print("Reconnect ...")
				client.repeat(1)
				client.play(songid)

		# Switch pressed
		if switches!=switches_last:
			switches_last=switches
			# Save switch state to file
			f=open('/home/mpd/last_switch.txt','r+');
			f.seek(0)
			f.write(str(switches_last))
			f.close()
			last_station_pos=station
			if switches==1:
				client.clear()
				client.load("web-radio-local")
				songid=0
				client.play(songid)
				list_len=len(client.playlist())
			if switches==2:
				client.clear()
				client.load("web-radio-int")
				songid=0
				client.play(songid)
				list_len=len(client.playlist())
			if switches==3:
				tracks=client.search('artist','Sesame')
				client.clear()
				for t in tracks:
					client.add(t['file'])
				client.play()
				tracks=client.search('genre','terror')
				for t in tracks:
					client.add(t['file'])
				songid=0
				client.play(songid)
				list_len=len(client.playlist())

	
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


		# Summ incremental select button movement
		select_travel=select_travel-select
		# Did it move out?
		if select>1:
			# Reset absolute position
			select_travel=0;
			select_pressed=0
		# Did it move out?
		if select_travel>0:
			if not select_pressed:
				play= not play
				if (play):
					client.play(songid)
				else:
					client.stop()
				select_pressed=1;
	
		#print(select_travel)
		
		# If we dial across the middle of two stations 
		# play next station and move point of reference 
		if (station_next_err<station_curr_err):
			last_station_pos=station+station_dist/2-1;
			songid=songid+1;
			if songid==list_len:
				songid=0
			print(songid)
			client.play(songid)
		if (station_prev_err<station_curr_err):   
                        last_station_pos=station-station_dist/2+1;
			songid=songid-1
			if songid<0:
				songid=list_len-1
                        client.play(songid)
			print(songid)
	 
		#client.setvol(int(poti3*vol_fac))
		#print(poti3);
		
		# If we listen to radio we use volume factor
		if (switches==1) or (switches==2):
			# Volume is set via amixer since mpd library cannot
			# deal with a large amount of volume changes
			os.system("amixer -q sset PCM "+ str(int(poti3*vol_fac)) +"%")
			#client.setvol(int(poti3*vol_fac))
		# For kids sond - zero hassle just play the next one 
		if switches==3:
			os.system("amixer -q sset PCM "+ str(int(poti3)) +"%")
			#client.setvol(int(poti3))
ser.close()
client.close()                     # send the close command
client.disconnect()                # disconnect from the server


