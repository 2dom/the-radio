#include <Servo.h>
#include <ps2.h>
PS2Mouse mouse(6, 7);
unsigned long serialdata;
int inbyte;

char command[4];
int pinNumber;
int value;

Servo servo1;

void setup()
{
  Serial.begin(9600);
  
  usage();
}

void loop()
{
  
  inbyte = 0;
  
  while (inbyte != '#')
  {
   
    inbyte = Serial.read(); 
  }
  wait_for_serial();
  //Serial.println(inbyte);
  for (int i=0; i<3 ;i++){
    wait_for_serial();
    inbyte=Serial.read(); 
    command[i]= inbyte;
  }
  command[3]='\0';
  
  wait_for_serial();
  pinNumber = Serial.read()-'0';
  wait_for_serial();
  pinNumber = pinNumber*10+Serial.read()-'0';
  
  //Serial.println(command);
  //Serial.println(pinNumber,DEC);
  
  // Digital Write Port
  if (strcmp(command,"DWP")==0) {
    wait_for_serial();
    value=Serial.read()-'0'; 
    
    pinMode(pinNumber, OUTPUT);
    if (value==1){
      digitalWrite(pinNumber,HIGH);
    }
    else {
      digitalWrite(pinNumber,LOW);  
    }
  }
  
  // Digital Read Port
  else if (strcmp(command,"DRP")==0) {
    
    pinMode(pinNumber, INPUT);
    Serial.println(digitalRead(pinNumber),DEC);
    
  }
  
   // Analog Write Port
  else if (strcmp(command,"AWP")==0) {
    
    pinMode(pinNumber, OUTPUT);
    
    wait_for_serial();
    value = Serial.read()-'0';
    wait_for_serial();
    value = pinNumber*10+Serial.read()-'0';
    wait_for_serial();
    value = value*10+Serial.read()-'0';
    analogWrite(pinNumber,value);
    
  }
  
  // Analog Read Port
  else if (strcmp(command,"ARP")==0) {
    
    pinMode(pinNumber, INPUT);
    Serial.println(analogRead(pinNumber),DEC);
    
  }
  // Initialize Mouse interface  
  else if (strcmp(command,"IMI")==0) {
    
    mouse.init();
    
  }
  // Accumulated Mouse Read  
  else if (strcmp(command,"ARM")==0) {
    
    // Read mouse
    MouseInfo mouseInfo;
    mouse.getData(&mouseInfo);
    delay(10);

    if (pinNumber==0){
      Serial.println(mouseInfo.cX,DEC);
    }
    else {
      Serial.println(mouseInfo.cY,DEC);  
    }
  }
  
  // Delta Mouse Read  
  else if (strcmp(command,"DRM")==0) {
    
    // Read mouse
    MouseInfo mouseInfo;
    mouse.getData(&mouseInfo);
    delay(10);

    if (pinNumber==0){
      Serial.println(mouseInfo.x,DEC);
    }
    else {
      Serial.println(mouseInfo.y,DEC);  
    }
  }
  // Initialize Servo interface  
  else if (strcmp(command,"ISI")==0) {
    
    servo1.attach(pinNumber); //analog pin 1
    
  } 
   // Digital Write Servo 
  else if (strcmp(command,"DWS")==0) {
    
    wait_for_serial();
    value = Serial.read()-'0';
    wait_for_serial();
    value = pinNumber*10+Serial.read()-'0';
    wait_for_serial();
    value = value*10+Serial.read()-'0';
    servo1.write(value);
    
  } 
  else {
    
    usage();
    
  }
    
  
  
  /*
  pinNumber=  Serial.read();
  //pinNumber=  pinNumber*10+ Serial.read() -'0';
  
  
  Serial.println(pinNumber,DEC);
 */ 
}

void wait_for_serial (){
  
  while (1){
    if (Serial.available() > 0)
    {
      break;
    }
  
  }
}
  
  
  void usage(void){
    
    Serial.println("Usage:");
    Serial.println("#DWP010:   Digital Write Port 01 to 0");
    Serial.println("#DRP07:    Digital Read Port 07");
    Serial.println("#AWP06255: Analog Write Port A06 to 255");
    Serial.println("#ARP04:    Analog Read Port A04:");
    Serial.println("#IMI:      Initialze mouse interface:");
    Serial.println("#ARM00:    Accumulated Read Mouse x-axis:");
    Serial.println("#DRM01:    Delta Read Mouse y-axis:");
    Serial.println("#ISI14:    Initialze servo interface to pin 14:");
    Serial.println("#DWS090:   Digital Write Servo 90 deg:");
    
  }

