#!/bin/sh
# installer.sh will install the necessary packages to get the gifcam up and running with 
# basic functions

# Install packages
PACKAGES="python3 python3-pip python3-serial python3-rpi.gpio"
apt-get update
apt-get upgrade -y
apt-get install $PACKAGES -y

#pip packages
pip3 install pyowm
pip3 install paho-mqtt

echo "updating rc.local"

sed -i 's/exit 0/sudo python /home/pi/iothub/control.py &/g' /etc/rc.local

echo "IoT @ School Installed"
echo "To set device parameters open config.json"