#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Input button manager
import Adafruit_BBIO.GPIO as GPIO
import time
import subprocess
GPIO.setup("P8_7", GPIO.OUT) # goes to Otto S input
GPIO.output("P8_7", GPIO.LOW)
GPIO.setup("P8_11", GPIO.IN)
GPIO.add_event_detect("P8_11", GPIO.RISING)
GPIO.setup("P8_12", GPIO.IN)
GPIO.add_event_detect("P8_12", GPIO.RISING)
GPIO.setup("P8_14", GPIO.IN)
GPIO.add_event_detect("P8_14", GPIO.RISING)
GPIO.setup("P8_16", GPIO.IN)
GPIO.add_event_detect("P8_16", GPIO.RISING)
GPIO.setup("P8_18", GPIO.IN)
GPIO.add_event_detect("P8_18", GPIO.RISING)
GPIO.setup("P8_9", GPIO.OUT) # goes to Otto OE input
GPIO.output("P8_9", GPIO.HIGH)
GPIO.setup("P8_10", GPIO.OUT)
GPIO.output("P8_10", GPIO.LOW)
GPIO.setup("P8_13", GPIO.OUT)
GPIO.output("P8_13", GPIO.LOW)
GPIO.setup("P8_15", GPIO.OUT)
GPIO.output("P8_15", GPIO.LOW)
GPIO.setup("P8_17", GPIO.OUT)
GPIO.output("P8_17", GPIO.LOW)
GPIO.setup("P8_19", GPIO.OUT)
GPIO.output("P8_19", GPIO.LOW)
subprocess.call("./BBB_in.sh")
subprocess.call("./Speaker_out.sh")
subprocess.call("./netio_server.py")
def buttonloop():
    while True:
        if GPIO.event_detected("P8_11"):
            subprocess.call("./S_kill.sh", shell=True)
            subprocess.call("./Speaker_out.sh", shell=True)
            time.sleep(1)
        elif GPIO.event_detected("P8_12"):
            subprocess.call("./S_kill.sh", shell=True)
            subprocess.call("./Phone_out.sh", shell=True)
            time.sleep(1)
        elif GPIO.event_detected("P8_14"):
            GPIO.output("P8_7", GPIO.HIGH)
            GPIO.output("P8_9", GPIO.HIGH) # move to bash script - echo
            subprocess.call("./SonyTV_in.sh", shell=True)
            time.sleep(1)
        elif GPIO.event_detected("P8_16"):
            GPIO.output("P8_9", GPIO.LOW)
            GPIO.output("P8_7", GPIO.HIGH)
            subprocess.call("./AppleTV_in.sh", shell=True)
            time.sleep(1)
        elif GPIO.event_detected("P8_18"):
            subprocess.call("./BBB_in.sh", shell=True)
            time.sleep(1)
        time.sleep(.4)
buttonloop()
print("exiting button loop")
GPIO.cleanup()
