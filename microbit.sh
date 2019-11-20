#!/bin/bash

echo "Starting"
until python3 microbit_usb_mqttV1.py; do
    echo echo  "$(date): Weather usb sensors has stopped $?">&2 >> log.txt
    echo "restarting"
    sleep 5s
done
