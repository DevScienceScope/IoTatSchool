#!/bin/bash

echo "Starting"
until python3 thermal-cameraV2-1.py; do
    echo echo  "$(date): Weather usb sensors has stopped $?">&2 >> log.txt
    echo "restarting"
    sleep 5s
done
