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

#Used for the camera
import threading
import RPi.GPIO as GPIO
import picamera

#Azure Blob storage
from azure.storage.blob import BlockBlobService
from azure.storage.blob import PublicAccess
from azure.storage.blob import ContentSettings

from subprocess import call

#Used for BME280
import smbus2
import bme280

hubAddress = deviceId = sharedAccessKey = location = gps = None

mode = "GO"
conn = False

#Setup power and LED state
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

Blue = 11
Green = 13
Red = 15
Camera = 22

camera = picamera.PiCamera()

GPIO.setup(Blue, GPIO.OUT) #Blue
GPIO.setup(Green, GPIO.OUT) #Green
GPIO.setup(Red, GPIO.OUT) #Red
GPIO.setup(Camera, GPIO.OUT) #Camera

GPIO.output(Blue, GPIO.LOW) #On
GPIO.output(Green, GPIO.HIGH) #Off
GPIO.output(Red, GPIO.HIGH) #Off
GPIO.output(Camera, GPIO.LOW) #Off

port = 1
address = 0x76
bus = smbus2.SMBus(port)

#Details for device used in authentication on IoT Hub
def config_defaults():
    global hubAddress, deviceId, sharedAccessKey, deviceType, location, gps, countryCode
    print('Loading default config settings')

    hubAddress = 'sciencescope.azure-devices.net'

    with open("/home/pi/iothub/config.json") as config_data:
        settings = json.load(config_data)

    deviceId = settings["device"]["deviceId"]
    sharedAccessKey = settings["device"]["sharedAccessKey"]
    deviceType = settings["device"]["deviceType"]
    location = settings["device"]["location"]
    gps = settings["device"]["gps"]
    countryCode = settings["device"]["countryCode"]

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
        GPIO.output(Blue, GPIO.HIGH)
        GPIO.output(Green, GPIO.LOW)
        GPIO.output(Red, GPIO.HIGH)

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
            GPIO.output(Blue, GPIO.LOW)
            GPIO.output(Green, GPIO.HIGH)
            GPIO.output(Red, GPIO.HIGH)
        except:
            print("Failed to connect to Azure: " + str(rc))
            conn = False
            time.sleep(10.0)
            GPIO.output(Blue, GPIO.HIGH)
            GPIO.output(Green, GPIO.HIGH)
            GPIO.output(Red, GPIO.LOW)

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

    #Restart timer
    t = Timer(300.0, upload_data)#5 minutes
    t.start()

    GPIO.output(Camera, GPIO.HIGH) #Turn camera on
    time.sleep(2)

    global dataPoints, deviceId, deviceType
    channels = 0

    ts = time.time()
    fileName = str(ts) + ".csv"
    cameraFile = str(ts) + ".jpg"

    camera.resolution = (640, 480)
    time.sleep(2)
    camera.capture(cameraFile)

    call(["./raspberrypi_capture", fileName])
    time.sleep(10)
    GPIO.output(Camera, GPIO.LOW) #Turn camera off

    #Upload to blob storage
    resp = block_blob_service = BlockBlobService(account_name='sciencescope',account_key='gsgfEufjVsGzMRyoWbkoglppAfSF2N8FPMO9FFAW8AMenu60JJBrv0jf/hkeym+TiEjnfOZboNRb+p2XE2wqJg==')
    print(resp)
    resp = block_blob_service.create_container(deviceId, public_access=PublicAccess.Container)
    print(resp)

    resp = block_blob_service.create_blob_from_path(deviceId,str(fileName),str(fileName),content_settings=ContentSettings(content_type="text/csv"))
    print(resp)
    resp = block_blob_service.create_blob_from_path(deviceId,str(cameraFile),str(cameraFile),content_settings=ContentSettings(content_type="image/jpg"))
    print(resp)

    try:
        calibration_params = bme280.load_calibration_params(bus, address)
        data = bme280.sample(bus, address, calibration_params)

        #Message start details for jsonString SGP, GBR
        msg_txt = "{\"deviceID\":\""+ deviceId +"\",\"tags\":\"Thermal Camera\",\"location\":\"" + gps + "\",\"locationName\":\"" + location + "\",\"" + deviceType + "\":\"Weather Station\",\"countryCode\":\"GBR\",\"dataReadings\":["
        msg_txt_sensor = "{\"idRange\":\"4501\",\"channel\":\"0\",\"value\":"+ str(ts) +",\"tags\":\"Thermal Camera\",\"type\":\"Camera\"},"
        msg_txt_sensor += "{\"idRange\":\"0301\",\"channel\":\"0\",\"value\":"+ str(data.pressure) +",\"tags\":\"Thermal Sensor\",\"type\":\"Camera\"},"
        msg_txt_sensor += "{\"idRange\":\"1701\",\"channel\":\"0\",\"value\":"+ str(data.humidity) +",\"tags\":\"Thermal Sensor\",\"type\":\"Camera\"},"
        msg_txt_sensor += "{\"idRange\":\"0501\",\"channel\":\"0\",\"value\":"+ str(data.temperature) +",\"tags\":\"Thermal Sensor\",\"type\":\"Camera\"}"
        msg_txt_end = "]}"
    except:
        #Message start details for jsonString SGP, GBR
        msg_txt = "{\"deviceID\":\""+ deviceId +"\",\"tags\":\"Thermal Camera\",\"location\":\"" + gps + "\",\"locationName\":\"" + location + "\",\"" + deviceType + "\":\"Weather Station\",\"countryCode\":\"GBR\",\"dataReadings\":["
        msg_txt_sensor = "{\"idRange\":\"4501\",\"channel\":\"0\",\"value\":"+ str(ts) +",\"tags\":\"Thermal Camera\",\"type\":\"Camera\"}"
        msg_txt_end = "]}"

    

    #Add end bit of json message
    msg_txt = msg_txt + msg_txt_sensor + msg_txt_end

    #Display message and publish
    print(msg_txt)
    publish(msg_txt)

    #reset datapoints 
    dataPoints = 0

    #Delete Files
    time.sleep(60)
    os.remove(fileName)
    os.remove(cameraFile)
    os.remove("IMG_0000.pgm")
	
    

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

client.connect(hubAddress, 8883)
t = Timer(30.0, upload_data)#5 minutes
t.start()

#Loop forever
while True:
   #Connect to Azure IoT Hub
    att = 0
    while conn == False:
        try:
            client.connect(hubAddress, 8883)
            conn = True
        except:
            print("Failed to connect to Azure")
            time.sleep(10.0)
            conn = False
        att += 1

        if att > 6:
            if check_internet():
                #Has internet try connection again
                att = 0
            else:
                time.sleep(60.0)#Wait 1 minute before trying again
                att = 0

    s = 0
