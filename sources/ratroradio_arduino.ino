/*
 Retroradio frontend

 Created April 2013
 by Dominic Buchstaller
 
*/

#include <ps2.h>
PS2Mouse mouse(6, 7);

int poti1 = 0;    // first analog sensor
int poti1_last=0;
int poti2 = 0;    // second analog sensor
int poti2_last = 0;   
int poti3 = 0;    // third analog sensor
int poti3_last = 0;    
int switches = 0; // selector switches
int switches_last = 0;    
int station=0;    // optical staion selector pickup
int station_last=0;
int select=0;     // optical pressure sensistve push button (TM)
int select_last=0;
int sense=2;      // Only send serial message if delta > sense


// Averaging filter for analog inputs
const int numReadings = 2;
int poti1_readings[numReadings];      // the readings from the analog input
int poti2_readings[numReadings];      // the readings from the analog input
int poti3_readings[numReadings];      // the readings from the analog input

int index = 0;                  // the index of the current reading
int poti1_total = 0;                  // the running total
int poti2_total = 0;                  // the running total
int poti3_total = 0;                  // the running total


int inByte = 0;         // incoming serial byte

void setup()
{
  // start serial port at 9600 bps:
  Serial.begin(115200);
  pinMode(13, OUTPUT);
  pinMode(A0, INPUT);
  pinMode(A1, INPUT);
  pinMode(A2, INPUT);
  pinMode(A3, INPUT);
  digitalWrite(13, 1);
  delay(1000);
  digitalWrite(13, 0);
  
  mouse.init();
   digitalWrite(13, 1)
   
   
  }

void send_serial(){
  
    // Limit range
    if (poti1>100)
      poti1=100;
      
    if (poti2>100)
      poti2=100;
      
    if (poti3>100)
       poti3=100;
   
    // Write all values to serial
    Serial.write("Start\n");
    Serial.print(poti1,DEC);
    Serial.write("\n");
    Serial.print(poti2,DEC);
    Serial.write("\n");
    Serial.print(poti3,DEC);
    Serial.write("\n");
    Serial.print(station, DEC);
    Serial.write("\n");
    Serial.print(select, DEC);
    Serial.write("\n");
    Serial.print(switches,DEC);
    Serial.write("\n");
  
}

void loop()
{
    // Read mouse
    MouseInfo mouseInfo;
    mouse.getData(&mouseInfo);
    
    // Averaging code
    poti1_total= poti1_total - poti1_readings[index];
    poti2_total= poti2_total - poti2_readings[index];
    poti3_total= poti3_total - poti3_readings[index];
   
    // Read analog values
    poti1_readings[index]= analogRead(A0)/10;
    delay(10);
    poti2_readings[index] = analogRead(A1)/10;
    delay(10);
    poti3_readings[index] = analogRead(A2)/10;
    delay(10);
    switches = analogRead(A3);
    delay(10);
    // Copy mouse position
    station=mouseInfo.cX;
    select=mouseInfo.y;
   
    // Determine selector switch state from analog values
    if (switches > 900)
      switches=1;
    else if ((switches < 600) && (switches > 400))
      switches=2;
    else if (switches < 50)
      switches=3;
    else if ((switches > 50) && (switches < 300))
      switches=4; 
   
   
    // More averaging code
    poti1_total= poti1_total + poti1_readings[index];
    poti2_total= poti2_total + poti2_readings[index];
    poti3_total= poti3_total + poti3_readings[index];
   
    index=index+1;
    
    poti1=poti1_total / numReadings;
    poti2=poti2_total / numReadings;
    poti3=poti3_total / numReadings;
    
    if (index >= numReadings)              
      index = 0;  
    
    
    
    // Any change since last serial message?
    if ((abs(poti1 - poti1_last)>sense) || (abs(poti2-poti2_last)>sense) || (abs(poti3 - poti3_last)>sense) ||  (station != station_last) || (select != select_last) || (switches != switches_last)) 
    {
      poti1_last=poti1;
      poti2_last=poti2;
      poti3_last=poti3;
      switches_last=switches;
      station_last=station;
      select_last=select;
      
      send_serial();
      
    }
    
}


