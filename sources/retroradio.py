#!/usr/bin/env python

import serial
import time
import mpd
import os
import pdb
import numpy
import pickle

client = mpd.MPDClient()           # create client object
client2 = mpd.MPDClient()           # create client object


# Connect to music server
while 1:
	try:
         	status = client.status()
		client.send_play()
		client.fetch_play()
		print("Initial connect music server")
                break
                
        except:
		client.connect("localhost", 6600)
                print("Initial connect music server failed ...")
		time.sleep(1)
	

# Connect to noise server
while 1:
	try:
         	status = client2.status()
		client2.send_setvol(0)
		client2.fetch_setvol(0)
		client2.send_clear()
		client2.fetch_clear()
		client2.send_add("/")
		client2.fetch_add("/")
		client2.send_play()
		client2.fetch_play()
		client2.send_repeat(1)
		client2.fetch_repeat(1)
		print("Initial connect noise server")
                break
                
        except:
		client2.connect("localhost", 6601)
                print("Initial connect noise server failed ...")
		time.sleep(1)
	


# Position of last station 
last_station_pos=0;

# Change noise track	
noise_track_skip=True;
# Distance between stations
station_dist=700;
# with of 100% volume area around stations
station_width=100;
# Outside of station_with volume decreases with slope
vol_slope=0.004
# Volume factor - this is what we change when we operate the station dial
vol_fac=1.0

# Volume filter array
vol_filter=numpy.arange(1,5);

# Initial master volume
master_volume=30

# How far deep is the start/stop button press
select_travel=0;
# start/stop button pressed?
select_pressed=0;

# Playlist names
playlist_name=["web-radio-local", "web-radio-int", "web-radio-news","volatile"];


# Read previous state from file
f=open('/home/mpd/state.pkl','r+');
state=pickle.load(f);
#state={'switches_last':0, 'queue_pos':[0,0,0,0]};
#pickle.dump(state,f);

if state['switches_last'] > 4 or state['switches_last'] <0:
	state['switches_last']=0
poti1_last=0;
poti2_last=0;

# Initial run?
Init=False

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

# Bridge power switch
ser.write("#DWP08")
ser.write("1")



while True:
	time.sleep(.05)
	client.send_repeat(1)
	client.fetch_repeat(1)
	client2.send_play()
	client2.fetch_play()
	#pdb.set_trace()
	#ser.write("#DWP08")
	#ser.write("1")
	
	if True:
		poti1=0;
		poti2=0;
		vol_filter=numpy.roll(vol_filter,1);
		ser.write("#ARP02")
		vol_filter[0]=int(ser.readline().rstrip())/10;
		if vol_filter[0]>100:
			vol_filter[0]=100;

		if vol_filter[0]<0:
			vol_filter[0]=0;		

		poti3=sum(vol_filter)/len(vol_filter);
		poti3=int(100.0-float(poti3));
		
		ser.write("#ARP03")
		switches_raw=int(ser.readline().rstrip());
	
		if switches_raw >1020:
			
			# Check again after 1.5s to prevent acidental shutdown
			time.sleep(1.5);
			ser.write("#ARP03")
			switches_raw=int(ser.readline().rstrip());

			if switches_raw > 1020:
				
				# Stop playback
				client.send_stop()
                                client.fetch_stop()
				
				# Save old playlist
				if state['switches_last']>1 and state['switches_last'] < 4:
					client.send_rm(playlist_name[state['switches_last']-1])
					client.fetch_rm(playlist_name[state['switches_last']-1])
					client.send_save(playlist_name[state['switches_last']-1])
					client.fetch_save(playlist_name[state['switches_last']-1])
			
				# Save state
				pickle.dump(state,f);
				f.close();

				os.system("sync")
				os.system("mount -fo remount,ro /")
               		 	# De-bridge power switch
				ser.write("#DWP08")
				ser.write("0")       
			
				print "halt";
		if switches_raw > 900 and switches_raw < 1000:
      			switches=1;
    		if switches_raw < 600 and switches_raw > 400:
      			switches=2;
    		if switches_raw < 50:
      			switches=3;
    		if switches_raw > 50 and switches_raw < 300:
      			switches=4; 
	
		ser.write("#ARM00")
		station=-int(ser.readline().rstrip());
	

		ser.write("#DRM01");	
		select=-int(ser.readline().rstrip());
		#print "Switches" + str(switches)
		#print "Station" + str(station)
		#print "Volume" + str(poti3)
		#print "Select" + str(select)
		
		# This is the first run - station position from Ardunio might be non zero
		if not Init:
			last_station_pos=station



		# Calculate station error
		# This is the distance to the current, last and next station
		station_curr_err=abs(station-last_station_pos)
		station_next_err=abs(station-last_station_pos-station_dist)
		station_prev_err=abs(station-last_station_pos+station_dist)
		# The smallest one is the one we work with
		station_err=min(station_curr_err,station_next_err,station_prev_err)		
		
		# If go past a station we skipt to the next noise track
		#print "Station error" + str(station_curr_err)
		if abs(station_curr_err)<30 and noise_track_skip==True:
			client2.send_next();
			client2.fetch_next();
			noise_track_skip=False;
			#print "Next noise track";
			
		station_last_err=station_curr_err;
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
	
		# Switch pressed
		if switches!=state['switches_last']:
			print switches	
			# Center station position
			last_station_pos=station
		       	
			# Save old playlist
			if state['switches_last']>1 and state['switches_last']<4:
				client.send_rm(playlist_name[state['switches_last']-1])
				client.fetch_rm(playlist_name[state['switches_last']-1])
				client.send_save(playlist_name[state['switches_last']-1])
				client.fetch_save(playlist_name[state['switches_last']-1])
			
			
			# Save queue position
			#print switches
			#print state['switches_last']
			client.send_currentsong()
			song = client.fetch_currentsong()
			
			# Check if mpd returns somethin 
			if any(song):
				song=int(song['pos']);
			else:
				song=1;
			state['queue_pos'][state['switches_last']-1]=song;
			
			if state['switches_last']==4:
				# Stop CD player
                       		fifofile.write("quit\n")
                       		try:	
					fifofile.flush()
				except:
					pass
				fifofile.close()

			state['switches_last']=switches
			
			# Clear play queue
			client.send_clear()
			client.fetch_clear()


			if switches!=4:
				
				client.send_load(playlist_name[switches-1])
				client.fetch_load(playlist_name[switches-1])
			
				#pdb.set_trace()	
				# Get length of playlist
				client.send_playlist()
				playlist=client.fetch_playlist()
				#print "Playlist" + str(playlist)
				queue_len=len(playlist)
				if queue_len==0:
					client.send_add('Noise')
					client.fetch_add('Noise')
					#pdb.set_trace()
					queue_len=1;
				
				#print "queue length" + str(queue_len)	
				# Saved queue position
				song_no=state['queue_pos'][switches-1]
				if song_no>queue_len:
					#pdb.set_trace()
					song_no=queue_len;
		
				#print "songno" + str(song_no)	
				try:
					client.send_play(song_no)
					client.fetch_play(song_no)
				except:	
					client.send_play(1)
					client.fetch_play(1)
			
			if switches == 4:
				#pdb.set_trace()
				os.system("mplayer -slave -input file=/home/mpd/cdfifo -quiet -cdrom-device /dev/sr0 cdda://1-99 &")
				
				time.sleep(1);
				# CD Player - volume is set via mplayer
				volstring="volume " + str(int(poti3)) + " 1\n ";
				fifofile = open('/home/mpd/cdfifo','w')
				fifofile.write(volstring)
				try:
					fifofile.flush()
				except:
					pass


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
				client.send_status()
				status=client.fetch_status();
				print "eject CD"
				os.system("eject /dev/sr0");
				#if (status['state']!='play'):
				#	client.send_play()
				#	client.fetch_play()
				#else:
				#	client.send_stop()
				#	client.fetch_stop()
				select_pressed=1;
	
		#print(select_travel)
		
		# If we dial across the middle of two stations 
		# play next station and move point of reference 
		if (station_next_err<station_curr_err):
			last_station_pos=station+station_dist/2-1;

			if switches == 4:
					
				# Next CD track
                       		fifofile.write("seek_chapter 1 \n")
                       		try:
					fifofile.flush()
				except:
					pass

			if switches < 4:
				# Get length of playlist
				client.send_playlist()
				playlist_len=len(client.fetch_playlist())
	
				# Check if something is playing
				client.send_currentsong()
				song = client.fetch_currentsong()
				if not any(song):
					break;
	
				# Play next song
				song=int(song['pos']);
				song=song+1;
				if song> playlist_len-1:
					song=0
				client.send_play(song);
				client.fetch_play(song);
	
				# Change noise track	
				noise_track_skip=True;
			
			
		if (station_prev_err<station_curr_err):   
                        last_station_pos=station-station_dist/2+1;
                        
			if switches == 4:
				# Prev cd track
                       		fifofile.write("seek_chapter -1\n")
                       		try:
					fifofile.flush()
				except:
					pass


			if switches < 4:
				# Get length of playlist
				client.send_playlist()
				playlist_len=len(client.fetch_playlist())
	
				# Check if something is playing
				client.send_currentsong()
				song = client.fetch_currentsong()
				if not any(song):
					break;
	
				# Play previous song
				song=int(song['pos']);
				song=song-1;
				if song<0:
					song=playlist_len-1;
				client.send_play(song);
				client.fetch_play(song);
	
				# Change noise track	
				noise_track_skip=True;
	
	 
		# If we listen to radio we use volume factor
		if (switches==1) or (switches==2) or (switches==3):
			# Volume is set via amixer since mpd library cannot
			# deal with a large amount of volume changes
			#os.system("amixer -q sset PCM "+ str(int(poti3*vol_fac)) +"%")
			client.send_setvol(int(poti3*vol_fac))
			client.fetch_setvol(int(poti3*vol_fac))

			client2.send_setvol(int(poti3*(1.0-vol_fac)))
			client2.fetch_setvol(int(poti3*(1.0-vol_fac)))


		if switches==4:
			# CD Player - volume is set via mplayer
			volstring="volume " + str(int(poti3)) + " 1\n ";
			fifofile.write(volstring)
			try:
				fifofile.flush()
			except:
				pass


		# For kids sond - zero hassle just play the next one 
		if switches==10:
			#os.system("amixer -q sset PCM "+ str(int(poti3)) +"%")
			client.send_setvol(int(poti3))
			client.fetch_setvol(int(poti3))


	        if master_volume < 100:

			master_volume=master_volume+2;
			os.system("amixer -q sset PCM "+ str(int(master_volume)) +"%")
                        			
		# First run done
		Init = True
ser.close()
client.close()                     # send the close command
client.disconnect()                # disconnect from the server


