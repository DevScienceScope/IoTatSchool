import subprocess
import time
import os
import json

enabled = "true"

def getMAC(interface):
    #Get the MAC address of the device
    try:
        str = open('/sys/class/net/' + interface + '/address').read()
    except:
        str = "00:00:00:00:00:00"
    return str[0:17]

#Opens config file to get ftp details
with open("/home/pi/IoTatSchool/iothub/config.json") as config_data:
        settings = json.load(config_data)

#Sets ftp details fromn config file
microbit =      settings["configuration"]["tech"]["microbit"]
logger =        settings["configuration"]["tech"]["logger"]
thermal =       settings["configuration"]["tech"]["thermal"]

#Get MAC address of wireless device
mac = getMAC('wlan0')


if logger == enabled:
    #Create logger session
    os.system("screen -dmS logger")
    #Send it command to execute in the script location
    os.system("screen -r logger -p0 -X stuff 'cd /home/pi/IoTatSchool/iothub; sh sensorsControl.sh'")
    #Send carriage return to execute
    os.system("screen -r logger -p0 -X eval 'stuff \015'")
elif microbit == enabled:
    #Create moisture session
    os.system("screen -dmS microbit")
    #Send it command to execute in the script location
    os.system("screen -r microbit -p0 -X stuff 'cd /home/pi/IoTatSchool/iothub; sh microbit.sh'")
    #Send carriage return to execute
    os.system("screen -r microbit -p0 -X eval 'stuff \015'")

elif thermal == enabled:
    #Create login session
    os.system("screen -dmS thermal")
    #Send it command to execute in the script location
    os.system("screen -r thermal -p0 -X stuff 'cd /home/pi/iothub/weather_mqtt; sh sensorsControl.sh'")
    #Send carriage return to execute
    os.system("screen -r thermal -p0 -X eval 'stuff \015'")