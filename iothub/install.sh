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

echo "Install complete, rebooting."
reboot