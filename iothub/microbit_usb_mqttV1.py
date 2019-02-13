# https://azure.microsoft.com/en-us/documentation/articles/iot-hub-mqtt-support/
# http://stackoverflow.com/questions/35452072/python-mqtt-connection-to-azure-iot-hub/35473777
# https://azure.microsoft.com/en-us/documentation/samples/iot-hub-python-get-started/


# Mqtt Support https://www.eclipse.org/paho/clients/python/
# pip3 install paho-mqtt

# Weather data Open Weather Map using https://github.com/csparpa/pyowm
# pip3 install pyowm

#Used in Azure MQTT example
import paho.mqtt.client as mqtt
import time
import helper
import sys
import json
import os

#Used for Serial comms 
import serial
import serial.tools.list_ports
import datetime
import signal
from serial.tools import list_ports

#generic imports
from threading import Timer
import csv

#Internet Connection
import requests

#Used for executing cloud to device commands
import subprocess
import os

hubAddress = deviceId = sharedAccessKey = location = gps = interval = None

mode = "GO"
conn = False
			
#Get list of devices
def get_devices():
    devices = serial.tools.list_ports.comports()
    #devices = list_ports.comports().decode()

    #array for sensors stored as com ports
    sensors = []

    mode = "BF"	
	
    #Loop through every USB deviceID
    #If a sensor has a different pid and vid add it hear
    for p in devices:
        if "0D28:0204" in p[2]:#Microbit Serial
            sensors.append(p[0])
            sensorType.append("microbit")
            print("Found microbit")
        time.sleep(1.0)     
    conns = [] #array for usb connections
    for s in sensors:
        #Connection string requires baud rate 115200 (All devices use this rate)
        conns.append(serial.Serial(s, 115200, timeout=1))

    return conns

#Details for device used in authentication on IoT Hub
def config_defaults():
    global hubAddress, deviceId, sharedAccessKey, deviceType, location, gps, countryCode, interval
    print('Loading default config settings')

    hubAddress = 'sciencescope.azure-devices.net'

    with open("config.json") as config_data:
        settings = json.load(config_data)

    deviceId = settings["device"]["deviceId"]
    sharedAccessKey = settings["device"]["sharedAccessKey"]
    deviceType = settings["device"]["deviceType"]
    location = settings["device"]["location"]
    gps = settings["device"]["gps"]
    countryCode = settings["device"]["countryCode"]
    interval  = settings["device"]["interval"]

#Load details used for helper
def config_load():
    global hubAddress, deviceId, sharedAccessKey
    try:
        if len(sys.argv) == 2:
            print('Loading {0} settings'.format(sys.argv[1]))

            config_data = open(sys.argv[1])
            config = json.load(config_data)
            hubAddress = config['IotHubAddress']
            deviceId = config['DeviceId']
            sharedAccessKey = config['SharedAccessKey']
        else:
            config_defaults()
    except:
        config_defaults()

#When the device connects to IoT Hub
def on_connect(client, userdata, flags, rc):
    print("Connected with result code: %s" % rc)
    client.subscribe(help.hubTopicSubscribe)
    global conn
    if rc == 0:
        conn = True

#When device disconnects from IoT Hub
def on_disconnect(client, userdata, rc):
    print("Disconnected with result code: %s" % rc)
    client.username_pw_set(help.hubUser, help.generate_sas_token(help.endpoint, sharedAccessKey)) 
	
    global conn
    conn = False
	
    if(rc > 0):
        print("trying to reconnect")
        try:
            client.connect(hubAddress, 8883)
        except:
            print("Failed to connect to Azure: " + str(rc))
            conn = False
            time.sleep(10.0)

#Deals with messages
def on_message(client, userdata, msg):
    #print("{0} - {1} ".format(msg.topic, str(msg.payload)))
    # Do this only if you want to send a reply message every time you receive one
    #client.publish("devices/mqtt/messages/events", "REPLY", qos=1)
    msgIn = msg.payload.decode('UTF-8')
    print(msgIn)
    if msgIn == 'reboot':
        try:
            command = "/usr/bin/sudo /sbin/shutdown -r now"
            process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
            output = process.communicate()[0]
        except:
            print("Failed to reboot")
    elif msgIn == "disconnect":
        try:
            command = "/usr/bin/sudo killall autossh"
            process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
            output = process.communicate()[0]
        except:
            print("Failed to kill autossh connections")
    elif "connect" in msgIn:
        try:
            messageDetails = msgIn.split(",")
            port = messageDetails[1]
            command = "/usr/bin/sudo autossh -i /home/pi/id_rsa -M 0 -o ServerAliveInterval=20 -N -R "+port+":localhost:22 sciencescope@sciencescoperemote.westeurope.cloudapp.azure.com"
            process = subprocess.Popen(command.split())
        except:
            print("Failed to create remote connection")
    elif msgIn == "send":
        try:
            upload_data()
        except:
            print("Failed to send current data")

#When a record is published
def on_publish(client, userdata, mid):
    print("Message {0} sent from {1}".format(str(mid), deviceId))

#Upload data is triggered by a timer event
#Uploads all data gathered from all devices
def upload_data():

    global devices, sensors, values, conn
    idRanges = []

    if(conn == False):
        #Not connected
        print("not connected")
        t = Timer(interval, upload_data)#1:30 minutes
        t.start()
    else:
        #Restart timer
        t = Timer(interval, upload_data)#5 minutes
        t.start()

        for d in range(len(devices)):
            #Message start details for jsonString SGP, GBR
            msg_txt = "{\"deviceID\":\""+ str(devices[d]) +"\",\"tags\":\"Raspberry Pi Logger\",\"location\":\"" + gps + "\",\"locationName\":\"" + location + "\",\"deviceType\":\"" + deviceType + "\",\"countryCode\":\"" + countryCode + "\",\"dataReadings\":["
            msg_txt_end = "]}"
            msg_txt_sensor = ""

            #Loop through all data gathered from USB devices
            for s in range(0, len(sensors[d])):

                #Build snesor reading json
                if(s == 0):
    	            msg_txt_sensor = "{\"idRange\":\""+ sensors[d][s] +"\",\"channel\":\"0\",\"value\":" + str(values[d][s]) +",\"max\":" + str(values[d][s]) +",\"min\":" + str(values[d][s]) +",\"tags\":\"Microbit Sensor\",\"type\":\"" + deviceType + "\"}"
                else:
    	            msg_txt_sensor = ",{\"idRange\":\""+ sensors[d][s] +"\",\"channel\":\"0\",\"value\":" + str(values[d][s]) +",\"max\":" + str(values[d][s]) +",\"min\":" + str(values[d][s]) +",\"tags\":\"Microbit Sensor\",\"type\":\"" + deviceType + "\"}"

	 
                #Add the average value for the sensor
                #msg_txt_formatted = msg_txt_sensor % (average)	
                #msg_txt = msg_txt + msg_txt_formatted
                msg_txt = msg_txt + msg_txt_sensor

            #Add end bit of json message
            msg_txt = msg_txt + msg_txt_end

            #Display message and publish
            print(msg_txt)
            publish(msg_txt)

        devices = []
        sensors = []
        values = []
	
    

#Sends the payload to IoT Hub
def publish(msg):
    global mode
    try:
        result = client.publish(help.hubTopicPublish, msg)#Sending payload
    except KeyboardInterrupt:
        print("IoTHubClient sample stopped")
        return
    except Exception as e:
        print(e)
        time.sleep(10.0)

def check_internet():
    try:
        response = requests.get("http://www.google.com")
        return True
    except Exception as e:
        print("No Internet!!")
        return False


config_load()

#Use helper to work with connection and generation os SAS tokens
help = helper.Helper(hubAddress, deviceId, sharedAccessKey)

#Creating MQTT client with desired specifications 
client = mqtt.Client(deviceId, mqtt.MQTTv311)

#Define functions to deal with events
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.on_publish = on_publish

#Setup credentials for IoT Hub access
client.username_pw_set(help.hubUser, help.generate_sas_token(help.endpoint, sharedAccessKey))

#Use cert builtin on pi
client.tls_set("/etc/ssl/certs/ca-certificates.crt")

#This function implements a threaded interface to the network loop. See paho-mqtt documention for why
client.loop_start()

sensorType = []
devices = []
sensors = []
values = []


client.connect(hubAddress, 8883)
t = Timer(90.0, upload_data)#wait 90 seconds before first upload
t.start()

ports = get_devices()

#Loop forever
while True:
    #Connect to Azure IoT Hub
    att = 0

    s = 0
    #For every found port
    dCount = 0
    #Get conncted USB sensors

    if(conn == False):
        try:
            client.connect(hubAddress, 8883)
        except Exception as e:
            print(e)
            #sys.exit(0)
    else:
        #Check if ports have changed
        checkPorts = get_devices()
        if(len(checkPorts) != len(ports)):
            #New sensor has been connecteds
            time.sleep(5)
            ports = get_devices()#Reset USB devices

        try:

            p = ports[0]
            while True:
                #Do somethign with each microbit
                #Even though there should only be one

                readings = p.readline().strip()
                #print(readings)

                if not len(readings) == 0 :   
                    readings = readings.decode()
                    readings = json.loads(readings)

                    #readings now contains the json string
                    #{"t":960583,"s":-1492758428,"n":"0616","v":26} t=MB time alive, s=MB serial number, n=sensor id Range, v = value

                    #Get the readings we require
                    serialNumber = readings["s"]
                    idRange = readings["n"]
                    value = readings["v"]

                    #2D array format
                    #devices = [device1, device2, device3] This array will hold the serial numbers
                    #idRange = [[1424, 0616], [1424, 0616], [1424, 0616]] This will hold the id ranges of the sensors linked to each device
                    #values = [[22, 400], [20,300], [30,1000]] this will hold sensor value which will lik to devices for index and link to id range in correct sequence

                    #Check if serial number exists in the devices array
                    #if not then create it with the sensor and value
                    if(serialNumber not in devices):
                        #Serial number exists
                        devices.append(serialNumber)
                        newSensor = [idRange];
                        newValue = [value];

                        sensors.append(newSensor)
                        values.append(newValue)
                    else:
                        #Get the index of the device recieved
                        deviceIndex = devices.index(serialNumber)
                
                        #Now need to check if sensor exists in the correct index for that deviceID
                        #If not then create sensor and value
                        if(idRange not in sensors[deviceIndex]):
                            newSensor = idRange;
                            newValue = value;

                            sensors[deviceIndex].append(newSensor)
                            values[deviceIndex].append(newValue)
                        else:
                            #The device and sensor both exist so now the value needs to be updated
                            sensorIndex = sensors[deviceIndex].index(idRange)
                            values[deviceIndex][sensorIndex] = value

                    print(devices)
                    print(sensors)
                    print(values)
           #Check for next port
        except Exception as e:
            print("Error getting USB data")
            print(e)
            time.sleep(20.0)
            ports = get_devices()#Reset USB devices
