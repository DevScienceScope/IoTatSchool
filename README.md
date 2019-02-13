# IoT @ School
ScineceScope Ltd IoT @ School github

Connect to the IoT @ School Exploraotry https://exploratory.sciencescope.uk/exploratory/ 

## Tested Hardware: 
Rapsberry Pi 3

## install Required Packages
```
sudo apt-get install screen

sudo apt-get install python3 

sudo apt-get install python3-pip 

sudo apt-get install python3-serial 

sudo apt-get install python3-rpi.gpio
```

```
sudo pip3 install pyowm

sudo pip3 install paho-mqtt
```

## Add line to rc.local
sudo python /home/pi/iothub/control.py &
