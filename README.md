# IoT @ School
ScineceScope Ltd IoT @ School github

Connect to the IoT @ School Exploraotry https://exploratory.sciencescope.uk/exploratory/ 

## Tested Hardware: 
Rapsberry Pi 3

## How to install
```
git clone https://github.com/DevScienceScope/IoTatSchool.git

cd IoTatSchool/iothub

sudo sh install.sh
```

## install.sh
install.sh will install all required packages and update the rc.local file so the iothub is running when the rapsberry pi turns on

## config.json
config.json controls the device properties below is a sample json string. This file will need changing
```json
{
  "configuration": {
    "tech": {
      "microbit": "false",
      "thermal": "false",
      "logger": "true"
    },
    "version": "2.0.1"
  },
  "device": {
    "deviceId": "MBxxxxxx",
    "sharedAccessKey": "key",
    "deviceType": "Weather Station",
    "location": "name of device",
    "gps": "latitude, longitude",
    "countryCode": "GBR",
    "interval":  300
  }
}
```
The table below explains each property
### configuration
| Property  | Description |
| ------------- | ------------- |
| microbit  | Acts as a gateway to turn the micro:bit into an IoT device. See our micro:bit IoT repo  |
| thermal  | For use with a flir lepton camera module  |
| logger  | Standard IoT logger for use with meaSense  |

### Device
The properties can be changed later by using the tagging system

| Property  | Description |
| ------------- | ------------- |
| deviceId  | Unique deviceId supplied by ScienceScope for connection to IoT @ School  |
| sharedAccessKey  | Unique access key paired with deviceId to enable connection to IoT @ School |
| deviceType  | Weather Station, IoT Logger, Cooking, Thermal Camera, microbit Gateway  |
| location  | Name of the device  |
| gps  | Latitude, longitide  |
| countryCode | 3 digit country code  |
| interval  | The interval between data uploads in seconds, Default 300 seconds (5 minutes)  |
