# IoT @ School
ScineceScope Ltd IoT @ School github

Connect to the IoT @ School Exploraotry https://exploratory.sciencescope.uk/exploratory/ 

## Tested Hardware: 
Rapsberry Pi 3

## How to install
```
git clone https://github.com/DevScienceScope/IoTatSchool.git

cd IoTatSchool/iothub

sh install.sh
```

## install.sh
install.sh will install all required packages and update the rc.local file so the iothub is running when the rapsberry pi turns on

```json
{
  "configuration": {
    "tech": {
      "microbit": "false",
      "thermal": "false",
      "logger": "true"
    },
    "version": "2.0.1",
    "location": "ScienceScope Offices"
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

## Add line to rc.local
sudo python /home/pi/iothub/control.py &
