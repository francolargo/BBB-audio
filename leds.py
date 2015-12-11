#!/usr/bin/env python
# -*- coding: utf-8 -*-
import Adafruit_BBIO.GPIO as GPIO
import time
import smbus # needed if you later want to add i2c functions
# GPIO setup needed to address pins
GPIO.setup("P9_11", GPIO.OUT)
GPIO.output("P9_11", GPIO.LOW)
GPIO.setup("P9_12", GPIO.OUT)
GPIO.output("P9_12", GPIO.LOW)
GPIO.setup("P9_13", GPIO.OUT)
GPIO.output("P9_13", GPIO.LOW)
rate = 0
rawrate = 0
# define a loop function to check hw_params every half second
def displayloop():
    while True:
        with open('/proc/asound/Botic/pcm0p/sub0/hw_params') as f:
            lines = f.readlines()
        try:
            rawrate = lines[4]
            rate =(int(rawrate[6:12])/1000)
        except IndexError:
            rate = 0
# display the sample rates being used - LED1=red, LED2=blue, LED3=green
# white=no play; blue=44; green=48; light blue=88/176; yellow(ish)=96/192
        if rate == 0:
            GPIO.output("P9_11", GPIO.HIGH)
            GPIO.output("P9_12", GPIO.HIGH)
            GPIO.output("P9_13", GPIO.HIGH)
        elif rate == 44:
            GPIO.output("P9_11", GPIO.LOW)
            GPIO.output("P9_12", GPIO.HIGH)
            GPIO.output("P9_13", GPIO.LOW)
        elif rate == 48:
            GPIO.output("P9_11", GPIO.LOW)
            GPIO.output("P9_12", GPIO.LOW)
            GPIO.output("P9_13", GPIO.HIGH)
        elif rate == 88 or rate == 176:
            GPIO.output("P9_11", GPIO.LOW)
            GPIO.output("P9_12", GPIO.HIGH)
            GPIO.output("P9_13", GPIO.HIGH)
        elif rate == 96 or rate == 192:
            GPIO.output("P9_11", GPIO.HIGH)
            GPIO.output("P9_12", GPIO.LOW)
            GPIO.output("P9_13", GPIO.HIGH)
        else:  time.sleep (.5)
displayloop()
