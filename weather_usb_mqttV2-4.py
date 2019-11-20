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

#Used for OLED
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

hubAddress = deviceId = sharedAccessKey = location = gps = interval = None

mode = "GO"
conn = False
			
#Get list of devices
def get_devices():
    devices = serial.tools.list_ports.comports()

    #array for sensors stored as com ports
    sensors = []

    mode = "BF"	
	
    #Loop through every USB deviceID
    #If a sensor has a different pid and vid add it hear
    for p in devices:
        if "2341:8036" in p[2]:#USB Leonardo Sensor
            sensors.append(p[0])
            sensorType.append("meaSense")
            #print("Found meaSense")
        elif "1A86:7523" in p[2]:#Unoffical Arduino Mega2560
            sensors.append(p[0])
            sensorType.append("logger")
            #print("Found Arduino Logger")
        elif "2A03:0042" in p[2]:#Offical Arduino Mega2560
            sensors.append(p[0])
            sensorType.append("logger")
            #print("Found Arduino Logger")
        elif "2341:0042" in p[2]:#Unoffical Arduino Mega2560
            sensors.append(p[0])
            sensorType.append("logger")
            #print("Found Arduino Logger")
        time.sleep(1.0)     
    conns = [] #array for usb connections
    for s in sensors:
        #Connection string requires baud rate 115200 (All devices use this rate)
        conns.append(serial.Serial(s, 115200, timeout=1))

    return conns
	
#Get the ID and rRanges of the sensor(s)
def get_sensorConfig(conn):
   
    try:
        #Send data to get sensor details
        conn.write(b'I')
        config = conn.readline().strip()
        config = config.decode()

        #Details are plsit as comma delimited string 
        configList = config.split(",")
        dataRate = configList[0]

        items = len(configList)    
        sensorNo = int(((items-1)/2))

        idRangeList = []
        index = 1
	
        #Loop through each sensor in device
        for x in range(0, sensorNo):
            #ID needs to be two digits. if less than 10 add leading 0
            if(int(configList[index]) < 10):
                strId = "0" + configList[index]
            else:
               strId = configList[index]
            index += 1

            #Range needs to be two digits. if less than 10 add leading 0
            if(int(configList[index]) < 10):
                strRange = "0" + configList[index]
            else:
                strRange = configList[index]
            index += 1

            #Combine ID and Range to make idRange and add to list
            idRangeList.append(strId + strRange)
        return idRangeList
    except:
        print("Error getting USB config")
	
#Get sensor data using connection
def get_sensorData(conn):


    try:
        conn.write(b'r') #Read once
        readings = conn.readline().strip()
        readings = readings.decode()
        print(readings)

        readingsList = readings.split(",")

        sensorNo = len(readingsList)

        data = []
        #Loop through every sensor in device to get readings
        #Readings are in same order as id range is get_sensorConfig
        for y in range(0, sensorNo):
            val = readingsList[y]
            data.append(val)

        return data
    except:
        print("Error getting USB data")
        #command = "/usr/bin/sudo /sbin/shutdown -r now"
        #process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        #output = process.communicate()[0]

#Details for device used in authentication on IoT Hub
def config_defaults():
    global hubAddress, deviceId, sharedAccessKey, deviceType, location, gps, countryCode, interval
    print('Loading default config settings')

    #hubAddress = 'sciencescope.azure-devices.net'
    hubAddress = 'abu-dhabi.azure-devices.net'
    

    with open("config.json") as config_data:
        settings = json.load(config_data)

    deviceId = settings["device"]["deviceId"]
    sharedAccessKey = settings["device"]["sharedAccessKey"]
    deviceType = settings["device"]["deviceType"]
    location = settings["device"]["location"]
    gps = settings["device"]["gps"]
    countryCode = settings["device"]["countryCode"]
    interval = settings["device"]["interval"]

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
        # Draw a black filled box to clear the image.
        draw.rectangle((0,0,width,height), outline=0, fill=0)

        draw.text((x, top),        "IoT @ School",  font=font, fill=255)
        draw.text((x, top+8),      "Connected",  font=font, fill=255)
        draw.text((x, top+16),     "Initialising",  font=font, fill=255)

        # Display image.
        disp.image(image)
        disp.display()

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

    global dataPoints, deviceId, deviceType, conn
    idRanges = []

    if(conn == False):
        #Not connected
        print("not connected")
        t = Timer(interval, upload_data)#5 minutes
        t.start()
    else:
        #Restart timer
        t = Timer(interval, upload_data)#5 minutes
        t.start()
	
        #Message start details for jsonString SGP, GBR
        msg_txt = "{\"deviceID\":\""+ deviceId +"\",\"tags\":\"Raspberry Pi Logger\",\"location\":\"" + gps + "\",\"locationName\":\"" + location + "\",\"deviceType\":\"" + deviceType + "\",\"countryCode\":\"" + countryCode + "\",\"dataReadings\":["
        msg_txt_end = "]}"
        msg_txt_sensor = ""

        value = 2e+53
        a = ("{:.2e}".format(value))

        channels = 0
        #Loop through all data gathered from USB devices
        for x in range(0, len(averages)):
            #Minus min becuase sometimes a min value can be miss read
            print(averages[x])
            if(averages[x][1] == complex(2,53)):
                print("NaN")
                #print(averages[x])
                average = a
            else:
                try:
                    average = (averages[x][1] - mins[x]) / (averages[x][3] - 1)
                except ZeroDivisionError:
                    average = a
                    averages[x][1] = a
                except:
                    average = a
                    averages[x][1] = a
                
            idRange = averages[x][0]
            type = averages[x][2]
            maxValue = maxs[x]
            minValue = mins[x]
		
            if(average == a):
                value = a
                maxValue = a
                minValue = a
            else:
                try:
                    value = str(round(average, 2))
                except:
                    value = a

            maxs[x] = minValue
            mins[x] = maxValue

            #channel = 0;
            #if idRange in idRanges:
                #channel += 1
            #Need to minus 1 as channel count starts from 0
            idRanges.append(idRange)
            channel = idRanges.count(idRange) - 1
            

            #Build snesor reading json
            if(x == 0):
    	        msg_txt_sensor = "{\"idRange\":\""+ idRange +"\",\"channel\":\"" + str(channel) + "\",\"value\":" + str(value) +",\"max\":" + str(maxValue) +",\"min\":" + str(minValue) +",\"tags\":\"Generic Sensor\",\"type\":\"" + type + "\"}"
            else:
    	        msg_txt_sensor = ",{\"idRange\":\""+ idRange +"\",\"channel\":\"" + str(channel) + "\",\"value\":" + str(value) +",\"max\":" + str(maxValue) +",\"min\":" + str(minValue) +",\"tags\":\"Generic Sensor\",\"type\":\"" + type + "\"}"

            channel = 0
        
            averages[x][3] = 0
            averages[x][1] = a
	 
            #Add the average value for the sensor
            #msg_txt_formatted = msg_txt_sensor % (average)	
            #msg_txt = msg_txt + msg_txt_formatted
            msg_txt = msg_txt + msg_txt_sensor


        #Add CPU temperature from Raspberry pi
        msg_txt = msg_txt + ",{\"idRange\":\"3141\",\"channel\":\"0\",\"value\":" + str(measure_temp()) +",\"max\":" + str(measure_temp()) +",\"min\":" + str(measure_temp()) +",\"tags\":\"Generic Sensor\",\"type\":\"CPU Temperature\"}"


        #Add end bit of json message
        msg_txt = msg_txt + msg_txt_end

        #Display message and publish
        print(msg_txt)
        publish(msg_txt)

        #reset datapoints 
        #averages = []
        #mins = []
        #maxs = []
        dataPoints = 0
	
    

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

def measure_temp():
    temp = os.popen("vcgencmd measure_temp").readline()
    temp = temp.replace("'C", "")
    return (temp.replace("temp=",""))


# Raspberry Pi pin configuration:
RST = 24

# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Load default font.
font = ImageFont.load_default()

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

draw.text((x, top),        "IoT @ School",  font=font, fill=255)
draw.text((x, top+8),      "Connecting",  font=font, fill=255)

# Display image.
disp.image(image)
disp.display()

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

averages = []
mins = []
maxs = []
dataPoints = 0

client.connect(hubAddress, 8883)
t = Timer(30.0, upload_data)#Wait 30 seconds before first upload
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
            averages = []
            mins = []
            maxs = []
            dataPoints = 0


        # Draw a black filled box to clear the image.
        draw.rectangle((0,0,width,height), outline=0, fill=0)

        draw.text((x, top),        "IoT @ School",  font=font, fill=255)
        draw.text((x, top+8),      "Connected",  font=font, fill=255)
        draw.text((x, top+24),     "CPU Temp: " + measure_temp(),  font=font, fill=255)
        draw.text((x, top+32),     "Sensors Connected: " + str(len(ports)-1), font=font, fill=255)

        # Display image.
        disp.image(image)
        disp.display()

        try:
            for p in ports:
                #Get sensor details
                details = get_sensorConfig(p)
                time.sleep(1.0)
                #Get sensor readings
                data = get_sensorData(p)

                #print(details)
                #print(data)

                for x in range(0, len(details)):
                    #Get sensor details
                    value = data[x]
                    if(value == "inf"):
                        #print("no data")
                        a = complex(2,53)
                        if(len(averages) <= s):
                            averages.append([details[x], a, "", 1])
                            mins.append(a)
                            maxs.append(a)
#                            print(averages)
                            
                    else:
                        #Check if averages exist, if not create them
                        if(len(averages) <= s):
                            #0 = idrange, 1 = average, 2 = type, 3 = count, 4 = min, 5 = max
                            averages.append([details[x], float(value), "", 1])
                            mins.append(float(value))
                            maxs.append(float(value))
                            #print(averages)
                        else:
                            averages[s][1] = averages[s][1] + float(value)
                            averages[s][2] = sensorType[dCount]

                            if(float(value) < float(mins[s])):
                                mins[s] = float(value)
                            if(float(value) > float(maxs[s])):
                                maxs[s] = float(value)

                            averages[s][3] = averages[s][3] + 1
            
                        #Used to count sensors for averages
                    s += 1
            time.sleep(1.0)
            dCount += 1      
            #Count the amount of datapoints
            dataPoints += 1
        except:
            print("Error getting USB Main")
            time.sleep(20.0)
            ports = get_devices()#Reset USB devices
            averages = []
            dataPoints = 0
