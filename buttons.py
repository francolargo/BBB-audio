#!/usr/bin/env python
import Adafruit_BBIO.GPIO as GPIO
import time
import os
GPIO.setup("P8_7", GPIO.OUT)
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
GPIO.setup("P8_9", GPIO.OUT)
GPIO.output("P8_9", GPIO.HIGH)
GPIO.setup("P8_10", GPIO.OUT)
GPIO.output("P8_10", GPIO.HIGH)
GPIO.setup("P8_13", GPIO.OUT)
GPIO.output("P8_13", GPIO.LOW)
GPIO.setup("P8_15", GPIO.OUT)
GPIO.output("P8_15", GPIO.LOW)
GPIO.setup("P8_17", GPIO.OUT)
GPIO.output("P8_17", GPIO.LOW)
GPIO.setup("P8_19", GPIO.OUT)
GPIO.output("P8_19", GPIO.HIGH)
def button8_11 (pin):
    GPIO.output("P8_10", GPIO.HIGH)  # Speaker LED
    GPIO.output("P8_13", GPIO.LOW)  # Headphone LED
    os.system("echo 'speaker' | nc -q .1 10.0.1.25 8194")
    print "did 8_11 speaker"
    time.sleep(1)
def button8_12 (pin):
    GPIO.output("P8_10", GPIO.LOW)  # Speaker LED
    GPIO.output("P8_13", GPIO.HIGH)  # Headphone LED
    os.system("echo 'phones' | nc -q .1 10.0.1.25 8194")
    print "did 8_12 phones"
    time.sleep(1)
def button8_14 (pin):
    GPIO.output("P8_15", GPIO.HIGH)  # SonyTV
    GPIO.output("P8_17", GPIO.LOW)  # AppleTV
    GPIO.output("P8_19", GPIO.LOW)  # BBB
    GPIO.output("P8_9", GPIO.LOW)  # turn on SPDIF switch
    GPIO.output("P8_7", GPIO.HIGH)  # select optical input
    os.system("echo 'SonyTV_in' | nc -q .1 10.0.1.25 8194")
    print "did 8_14 STV"
    time.sleep(1)
def button8_16 (pin):
    GPIO.output("P8_15", GPIO.LOW)  # SonyTV
    GPIO.output("P8_17", GPIO.HIGH)  # AppleTV
    GPIO.output("P8_19", GPIO.LOW)  # BBB
    GPIO.output("P8_9", GPIO.LOW)  # turn on SPDIF switch
    GPIO.output("P8_7", GPIO.LOW)  # select optical input
    os.system("echo 'AppleTV_in' | nc -q .1 10.0.1.25 8194")
    print "did 8_16 ATV"
    time.sleep(1)
def button8_18 (pin):
    GPIO.output("P8_15", GPIO.LOW)  # SonyTV
    GPIO.output("P8_17", GPIO.LOW)  # AppleTV
    GPIO.output("P8_19", GPIO.HIGH)  # BBB
    GPIO.output("P8_9", GPIO.HIGH)  # Otto off
    os.system("echo 'BBB_in' | nc -q .1 10.0.1.25 8194")
    print "did 8_18 BBB"
    time.sleep(1)
GPIO.add_event_callback("P8_11",button8_11)
GPIO.add_event_callback("P8_12",button8_12)
GPIO.add_event_callback("P8_14",button8_14)
GPIO.add_event_callback("P8_16",button8_16)
GPIO.add_event_callback("P8_18",button8_18)
# main function
def main():
      time.sleep(.5)

if __name__=="__main__":
    while True:
       main()

