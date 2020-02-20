#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import asyncore
import socket
import select
import Adafruit_BBIO.GPIO as GPIO
import time
from multiprocessing import Process 
import subprocess
import smbus
#import os
import logging
#set up logging
logger = logging.getLogger('Python_DAC_log')
logger.setLevel(logging.DEBUG)
# create file handler that logs even debug messages
fh = logging.FileHandler('Python_DAC.log')
fh.setLevel(logging.DEBUG) # can change to higher level later (INFO, WARN, ERROR, CRITICAL)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh) # add the handlers to logger

#    logger. example messages:
#    logger.debug('debug message')
#    logger.info('info message')
#    logger.warn('warn message')
#    logger.error('error message')
#    logger.critical('critical message')

# wait for DAC to fully initialize
time.sleep(3)
# misc. GPIO setup as needed to address LED pins
GPIO.setup("P8_7", GPIO.OUT)
GPIO.output("P8_7", GPIO.LOW)
GPIO.setup("P8_9", GPIO.OUT)
GPIO.output("P8_9", GPIO.LOW)
GPIO.setup("P8_10", GPIO.OUT)
GPIO.output("P8_10", GPIO.HIGH)
GPIO.setup("P8_13", GPIO.OUT)
GPIO.output("P8_13", GPIO.LOW)
GPIO.setup("P8_15", GPIO.OUT)
GPIO.output("P8_15", GPIO.LOW)
GPIO.setup("P8_17", GPIO.OUT)
GPIO.output("P8_17", GPIO.LOW)
GPIO.setup("P8_19", GPIO.OUT)
GPIO.output("P8_19", GPIO.LOW)
#set variable initial values
tweeter = 15 # 2/16/20 mods
midrange = 45 # 2/16/20 mods
woofers = 0 # 2/16/20  mods
initialize = 0
rate = 0
rawrate = 0
bus = smbus.SMBus(1)
muted = 0
volume = 5
mutebus = 0x61  # default mute setting
FIR = 0x60  # default filter shape - slow, linear
OSF = 0x80 # Oversampling system & filter is off by default
set6 = volume - int(midrange * 0.01 * volume)
set5 = volume - int(tweeter * 0.01 * volume)
set4 = volume - int(woofers * 0.01 * volume)
# setup I2C volume, DPLL bandwidth, other es9028 parameters 
def dacregister():
   bus.write_byte_data(0x48, 0x02, 0xfc)  # automute on
   bus.write_byte_data(0x48, 0x04, 0xff)  # automute time = 255
   bus.write_byte_data(0x48, 0x05, 96)    # automute level
   bus.write_byte_data(0x48, 0x0a, 0x10)  # enable 128*FSR mode
   bus.write_byte_data(0x48, 0x0c, 0x00)  # DPLL 1a = lowest bandwidth for I2S, 10 for DSD, 0x00 = off
   bus.write_byte_data(0x48, 0x0d, 0x20)  # THD and jitter eliminator disabled (default is 0x10 - THD 'on' & jitter 'on') 
   bus.write_byte_data(0x48, 0x0f, 0x0f)  # use stereo mode, channel 1 and latch volume
   bus.write_byte_data(0x48, 0x25, 0x80)  # bypass the FIR oversampling filter (default is 0x00)
   bus.write_byte_data(0x48, 0x3e, 0x00)  # be sure +18 db setting is off
   logger.debug('DAC register set')
def mute1():
   bus.write_byte_data(0x70, 0x40, 0x06)  # midrange address
   bus.write_byte_data(0x48, 0x07, mutebus)  # mute
   bus.write_byte_data(0x70, 0x40, 0x05)  # tweeter address
   bus.write_byte_data(0x48, 0x07, mutebus)  # mute
   bus.write_byte_data(0x70, 0x40, 0x04)  # woofer address
   bus.write_byte_data(0x48, 0x07, mutebus)  # mute
def unmute1():
   bus.write_byte_data(0x70, 0x40, 0x06)
   bus.write_byte_data(0x48, 0x07, FIR)
   bus.write_byte_data(0x48, 0x1b, set6)
   bus.write_byte_data(0x70, 0x40, 0x05)
   bus.write_byte_data(0x48, 0x07, FIR)
   bus.write_byte_data(0x48, 0x1b, set5)
   bus.write_byte_data(0x70, 0x40, 0x04)
   bus.write_byte_data(0x48, 0x07, FIR)
   bus.write_byte_data(0x48, 0x1b, set4)
def initialize():   # initialize for default input: AppleTV -> speakers
#   global initialize
   mute1()
   subprocess.call("killall -9 squeezelite", shell=True)
   subprocess.call("killall -9 sox", shell=True)
   logger.debug("initialize() ran")
#   initialize = 1
def reset(): # LEDs flash a warning
   while True:
      GPIO.output("P8_10", GPIO.LOW)
      GPIO.output("P8_13", GPIO.LOW)
      GPIO.output("P8_15", GPIO.LOW)
      GPIO.output("P8_17", GPIO.LOW)
      GPIO.output("P8_19", GPIO.LOW)
      time.sleep(.5)
      GPIO.output("P8_10", GPIO.HIGH)
      GPIO.output("P8_13", GPIO.HIGH)
      GPIO.output("P8_15", GPIO.HIGH)
      GPIO.output("P8_17", GPIO.HIGH)
      GPIO.output("P8_19", GPIO.HIGH)
      time.sleep(.5)
mute1()
bus.write_byte_data(0x70, 0x40, 0x06)  # midrange address
dacregister()
time.sleep(.2)
bus.write_byte_data(0x70, 0x40, 0x05)  # tweeter address
dacregister()
time.sleep(.2)
bus.write_byte_data(0x70, 0x40, 0x04)  # woofer address
dacregister()
time.sleep(.2)
initialize()
subprocess.call("echo 'BBB_ready\n' | nc -n -q .2 -w 1 192.168.1.50 4323", shell=True)
time.sleep(1)
logger.debug("initialize ran in start sequence")

#  Setup asyncore client for NetIO
class Client(asyncore.dispatcher_with_send):
    def __init__(self, socket=None, pollster=None):
        asyncore.dispatcher_with_send.__init__(self, socket)
        self.data = ''
        if pollster:
            self.pollster = pollster
            pollster.register(self, select.EPOLLIN)

    def handle_close(self):
        if self.pollster:
            self.pollster.unregister(self)

    def handle_read(self):
        receivedData = self.recv(8192) #8192 = buffer size
        if not receivedData:
            self.close()
            return
        receivedData = self.data + receivedData
        while '\n' in receivedData:
            line, receivedData = receivedData.split('\n',1) # valid NetIO commands end with '\n'
            self.handle_command(line)
        self.data = receivedData
        #print (receivedData)
#  Define all commands executed by NetIO
    def handle_command(self, line):
        global tweeter
        global midrange
        global woofers 
        global volume
        global set4
        global set5
        global set6
        global rate
        global muted
        global mutebus
        global PIN13
        global PIN19
        global FIR
        global OSF
        global rate
        mutebus = 0x61  # default mute setting
        OSF = 0x80  # filter off
        FIR = 0x60  # default filter shape - slow, linear
        def mute():
            global muted
            bus.write_byte_data(0x70, 0x40, 0x06)
            bus.write_byte_data(0x48, 0x07, mutebus)
            bus.write_byte_data(0x70, 0x40, 0x05)
            bus.write_byte_data(0x48, 0x07, mutebus)
            bus.write_byte_data(0x70, 0x40, 0x04)
            bus.write_byte_data(0x48, 0x07, mutebus)
            muted = 1
            logger.debug("mute ran")
        def unmute():
            global muted
            bus.write_byte_data(0x70, 0x40, 0x06)
            bus.write_byte_data(0x48, 0x07, FIR)
            bus.write_byte_data(0x48, 0x1b, set6)
            bus.write_byte_data(0x70, 0x40, 0x05)
            bus.write_byte_data(0x48, 0x07, FIR)
            bus.write_byte_data(0x48, 0x1b, set5)
            bus.write_byte_data(0x70, 0x40, 0x04)
            bus.write_byte_data(0x48, 0x07, FIR)
            bus.write_byte_data(0x48, 0x1b, set4)
            muted = 0
            logger.debug("unmute ran")
        def flasha():
            GPIO.output("P8_17", GPIO.LOW)
            time.sleep(.5)
            GPIO.output("P8_17", GPIO.HIGH)
            time.sleep(.5)
        def flashs():
            GPIO.output("P8_15", GPIO.LOW)
            time.sleep(.5)
            GPIO.output("P8_15", GPIO.HIGH)
            time.sleep(.5)
        def flashb():
            GPIO.output("P8_19", GPIO.LOW)
            time.sleep(.5)
            GPIO.output("P8_19", GPIO.HIGH)
            time.sleep(.5)
        def flashsp():
            GPIO.output("P8_10", GPIO.LOW)
            time.sleep(.5)
            GPIO.output("P8_10", GPIO.HIGH)
            time.sleep(.5)
        def flashp():
            GPIO.output("P8_13", GPIO.LOW)
            time.sleep(.5)
            GPIO.output("P8_13", GPIO.HIGH)
            time.sleep(.5)  
        def conFIR():
            bus.write_byte_data(0x70, 0x40, 0x06)
            bus.write_byte_data(0x48, 0x25, 0x00)  # activate oversampling filter 
            bus.write_byte_data(0x48, 0x07, FIR)
            bus.write_byte_data(0x70, 0x40, 0x05)
            bus.write_byte_data(0x48, 0x25, 0x00)  # activate oversampling filter 
            bus.write_byte_data(0x48, 0x07, FIR)
            bus.write_byte_data(0x70, 0x40, 0x04)
            bus.write_byte_data(0x48, 0x25, 0x00)  # activate oversampling filter 
            bus.write_byte_data(0x48, 0x07, FIR)
            OSF = 0x00
            print FIR
            time.sleep (.1)
        if  line.startswith("set it to"):
            volume = int(line[10:13])
            print (line)
            set6 = volume - int(midrange * 0.01 * volume)
            set4 = volume - int(woofers * 0.01 * volume)
            set5 = volume - int(tweeter * 0.01 * volume)
            bus.write_byte_data(0x70, 0x40, 0x06)
            bus.write_byte_data(0x48, 0x1b, set6)
            bus.write_byte_data(0x70, 0x40, 0x05)
            bus.write_byte_data(0x48, 0x1b, set5)
            bus.write_byte_data(0x70, 0x40, 0x04)
            bus.write_byte_data(0x48, 0x1b, set4)
            self.send("ok\n")
        elif line == 'initialize':
            initialize()
            time.sleep(1)
            self.send("ok\n")
#            print 'initialize ran from netcat'
        elif line == 'shutdown':
            subprocess.call("systemctl poweroff", shell=True)
            time.sleep(1)
            self.send("ok\n")
        elif line == 'BBB_in':
            self.send('BBB_in\n')
            mute()
            GPIO.output("P8_15", GPIO.LOW)  # SonyTV
            GPIO.output("P8_17", GPIO.LOW)  # AppleTV
            GPIO.output("P8_19", GPIO.HIGH)  # BBB
            initialize()
            flashb() # sox needs a pause to finish the kill
            GPIO.output("P8_9", GPIO.HIGH)  # Otto off
            with open('/sys/class/gpio/gpio23/value') as f:
                 lines = f.readlines()
            try:
                 PIN13 = int(lines[0])
            except IndexError:
                 PIN13 = 0
            print (PIN13)
            if PIN13 == 1:
               subprocess.call("nice -n -19 squeezelite -z -C 1 -o hw:0,0 -a 4096:1024:32:0", shell=True)  # no crossover
            else:
               subprocess.call("nice -n -19 squeezelite -z -C 1 -o plug:filter4 -a 4096:1024:32:0", shell=True)  # with crossover
            flashb()
            print "squeezelite started?"
            volume = 5
            midrange = 45
            tweeter = 15
            set6 = volume - int(midrange * 0.01 * volume)
            set5 = volume - int(tweeter * 0.01 * volume)
            set4 = volume - int(woofers * 0.01 * volume)
            unmute()
#            subprocess.call("echo 'BBBin' | nc -n -q .2 10.0.1.130 4323", shell=True)
        elif line == 'speakers_out':
            self.send('speakers_out\n')
            print 'heard speakers_out'
            GPIO.output("P8_10", GPIO.HIGH)  # Speaker LED
            GPIO.output("P8_13", GPIO.LOW)  # Headphone LED
            initialize()
            flashsp()
            # subprocess.call("echo 'Amps_on' | nc -n -q .2 10.0.1.130 4323", shell=True)
            time.sleep(1)
            with open('/sys/class/gpio/gpio22/value') as f:
                 lines = f.readlines()
            try:
                 PIN19 = int(lines[0])
            except IndexError:
                 PIN19 = 0
            print(PIN19)
            if PIN19 == 1:
               subprocess.call("nice -n -19 squeezelite -z -C 1 -o plug:filter4 -a 4096:1024:32:0", shell=True)
               flashsp()
            else:
               subprocess.call("amixer -c miniStreamer cset numid=8 1", shell=True)
               subprocess.call("chrt -f 45 sox --buffer 512 -r 48000 -c 2 -t alsa hw:1,0 -t alsa plug:filter4 &", shell=True)
               #os.system("chrt -f 45 sox --buffer 512 -r 48000 -c 2 -t alsa hw:1,0 -t alsa plug:pre-eq5 &")
                                     # gain -h fir /usr/filter/fir2peak48mild.txt &")
               flashsp()
            volume = 5
            tweeter = 15
            midrange = 45
            woofers = 0 
            set6 = volume - int(midrange * 0.01 * volume)
            set4 = volume - int(woofers * 0.01 * volume)
            set5 = volume - int(tweeter * 0.01 * volume)
            subprocess.call("echo 'speakers\n' | nc -n -q .1 -w 1 192.168.1.50 4323", shell=True)
            time.sleep(1)
            unmute()
        elif line == 'phones_out':
            self.send('phones_out\n')
            print 'heard phones_out'
            GPIO.output("P8_10", GPIO.LOW)  # Speaker LED
            GPIO.output("P8_13", GPIO.HIGH)  # Headphone LED
            initialize()
            flashp() 
            subprocess.call("amixer -c miniStreamer cset numid=8 1", shell=True)
            with open('/sys/class/gpio/gpio22/value') as f:
                 lines = f.readlines()
            try:
                 PIN19 = int(lines[0])
            except IndexError:
                 PIN19 = 0
            print(PIN19)
            if PIN19 == 1:
               subprocess.call("nice -n -19 squeezelite -z -C 1 -o hw:0,0 -a 4096:1024:32:0", shell=True)
               flashp()
            else:
               subprocess.call("amixer -c miniStreamer cset numid=8 1", shell=True)
               subprocess.call("chrt -f 45 sox --buffer 512 -r 48000 -c 2 -t alsa hw:1,0 -t alsa plug:TV-inhw &", shell=True)
               flashp()
            volume = 5
            woofers = 100
            tweeter = 100
            midrange = 0
            set6 = volume
            set4 = volume - int(woofers * 0.01 * volume)
            set5 = volume - int(tweeter * 0.01 * volume)
            subprocess.call("echo 'headphones\n' | nc -n -q .1 -w 1 192.168.1.50 4323", shell=True)   
            unmute()
        elif line == 'AppleTV_in':
            self.send('AppleTV_in\n')
            mute()
            GPIO.output("P8_15", GPIO.LOW)  # SonyTV
            GPIO.output("P8_17", GPIO.HIGH)  # AppleTV
            GPIO.output("P8_19", GPIO.LOW)  # BBB
            initialize()
            flasha()
            subprocess.call("amixer -c miniStreamer cset numid=8 1", shell=True)
            GPIO.output("P8_9", GPIO.LOW)  # turn on SPDIF switch - otto
            GPIO.output("P8_7", GPIO.LOW)  # select optical input
            with open('/sys/class/gpio/gpio23/value') as f:
                 lines = f.readlines()
            try:
                 PIN13 = int(lines[0])
            except IndexError:
                 PIN13 = 0
            # print(PIN13)
            if PIN13 == 1: # headphone option
                subprocess.call("chrt -f 45 sox --buffer 512 -r 48000 -c 2 -t alsa hw:1,0 -t alsa plug:TV-inhw &", shell=True)
            else:
                subprocess.call("chrt -f 45 sox --buffer 512 -r 48000 -c 2 -t alsa hw:1,0 -t alsa plug:filter4 &", shell=True)
#                 os.system("chrt -f 45 sox --buffer 512 -r 48000 -c 2 -t alsa hw:1,0 -t alsa plug:filter1 &")
                 # os.system("chrt -f 45 sox --buffer 1024 -r 48000 -c 2 -t alsa hw:1,0 -t alsa plug:pre-eq5 &")
                                    # gain -h fir /usr/filter/fir2peak48mild.txt &")
            flasha()
            volume = 5
            midrange = 45
            tweeter = 15
            set6 = volume - int(midrange * 0.01 * volume)
            set4 = volume - int(woofers * 0.01 * volume)
            set5 = volume - int(tweeter * 0.01 * volume)
            unmute()

        elif line == 'SonyTV_in':
            self.send('SonyTV_in\n')
            GPIO.output("P8_15", GPIO.HIGH)  # SonyTV
            GPIO.output("P8_17", GPIO.LOW)  # AppleTV
            GPIO.output("P8_19", GPIO.LOW)  # BBB
            initialize()
            flashs()
            subprocess.call("amixer -c miniStreamer cset numid=8 1", shell=True)
            GPIO.output("P8_9", GPIO.LOW)  # turn on SPDIF switch
            GPIO.output("P8_7", GPIO.HIGH)  # select optical input
            with open('/sys/class/gpio/gpio23/value') as f:
                 lines = f.readlines()
            try:
                 PIN13 = int(lines[0])
            except IndexError:
                 PIN13 = 0
            print(PIN13)
            if PIN13 == 1:
               subprocess.call("chrt -f 45 sox --buffer 512 -r 48000 -c 2 -t alsa hw:1,0 -t alsa plug:TV-inhw &", shell=True)
            else:
               subprocess.call("chrt -f 45 sox --buffer 512 -r 48000 -c 2 -t alsa hw:1,0 -t alsa plug:filter4 &", shell=True) # gain -h fir /usr/filter/fir2peak48mild.txt &")
               # os.system("chrt -f 45 sox --buffer 1024 -r 48000 -c 2 -t alsa hw:1,0 -t alsa plug:pre-eq1 &")
                                      # gain -h fir /usr/filter/fir2peak48mild.txt &")
 #           flashs()
            volume = 5
            midrange = 45
            tweeter = 15
            set6 = volume - int(midrange * 0.01 * volume)
            set4 = volume - int(woofers * 0.01 * volume)
            set5 = volume - int(tweeter * 0.01 * volume)
            unmute()
        elif line.startswith("tweeterset"):
            tweeter = int(line[11:14])
            print (tweeter)
            set5 = volume - int(tweeter * 0.01 * volume)
            bus.write_byte_data(0x70, 0x40, 0x05)
            bus.write_byte_data(0x48, 0x1b, set5)
            self.send("ok\n")
        elif line.startswith("midrangeset"):
            midrange = int(line[12:15])
            print (midrange)
            set6 = volume - int(midrange * 0.01 * volume)
            bus.write_byte_data(0x70, 0x40, 0x06)
            bus.write_byte_data(0x48, 0x1b, set6)
            self.send("ok\n")
        elif line.startswith("woofersset"):
            woofers = int(line[11:14])
            print (woofers)
            set4 = volume - int(woofers * 0.01 * volume)
            bus.write_byte_data(0x70, 0x40, 0x04)
            bus.write_byte_data(0x48, 0x1b, set4)
            self.send("ok\n")
        elif line == 'toggle mute':
            #bus.write_byte_data(0x70, 0x40, 0x06)   
            #try:
             #  muted = bus.read_byte_data(0x48, 0x07) # % 2 = remainder after division by 2
            #except IOError as err:
             #  logger.debug("mute read error")      
            if muted  == 0:
               mute()
               logger.debug("muted")
            else:
               unmute()
               logger.debug("unmuted")
            self.send("ok\n")
        elif line == 'mute on': # return for toggle mute
            #muted = bus.read_byte_data(0x48, 0x07)
            if muted  == 1:
                 self.send("UNMUTE\n")
            else:
                 self.send("MUTE\n")
        elif line == 'function1':
            FIR = 0x60
            mutebus = 0x61
            conFIR()
            self.send("ok\n")
        elif line == 'fcn1':
            if bus.read_byte_data(0x48, 0x07) == 0x60 and bus.read_byte_data(0x48, 0x25) == 0x00:
                 self.send("SLO-MIN ON\n")
            else:
                 self.send("Slo-Min\n")
        elif line == 'function3':
#            FIR = 0x80
#            mutebus = 0x81
#            conFIR()
            self.send("ok\n")
            mute()
            GPIO.output("P8_15", GPIO.LOW)  # SonyTV
            GPIO.output("P8_17", GPIO.LOW)  # AppleTV
            GPIO.output("P8_19", GPIO.HIGH)  # BBB
            initialize()
            flashb() # sox needs a pause to finish the kill
            GPIO.output("P8_9", GPIO.HIGH)  # Otto off
            with open('/sys/class/gpio/gpio23/value') as f:
                 lines = f.readlines()
            try:
                 PIN13 = int(lines[0])
            except IndexError:
                 PIN13 = 0
            print (PIN13)
            if PIN13 == 1:
               subprocess.call("nice -n -19 squeezelite -z -C 1 -o hw:0,0 -a 4096:1024:32:0", shell=True)  # no crossover
            else:
               subprocess.call("nice -n -19 squeezelite -z -C 1 -o plug:pre-eq1 -a 4096:1024:32:0", shell=True)  # with crossover
            flashb()
            set6 = volume - int(midrange * 0.01 * volume)
            set5 = volume - int(tweeter * 0.01 * volume)
            set4 = volume - int(woofers * 0.01 * volume)
            unmute()
        elif line == 'fcn3':
#            if bus.read_byte_data(0x48, 0x07) == 0x80 and bus.read_byte_data(0x48, 0x25) == 0x00:
#                 self.send("APODIZE ON\n")
#            else:
#                 self.send("Apodizing\n")
            self.send("XO pre-eq1\n") 
        elif line == 'function2':
            FIR = 0x40
            mutebus = 0x41
            conFIR()
            self.send("ok\n")
        elif line == 'fcn2':
            if bus.read_byte_data(0x48, 0x07) == 0x40 and bus.read_byte_data(0x48, 0x25) == 0x00:
                 self.send("FAST-MIN ON\n")
            else:
                 self.send("Fast-Min\n")
        elif line == 'function4':
            FIR = 0x20
            mutebus = 0x21
            conFIR()
            self.send("ok\n")
        elif line == 'fcn4':
            if bus.read_byte_data(0x48, 0x07) == 0x20 and bus.read_byte_data(0x48, 0x25) == 0x00:
                 self.send("SLO-LIN ON\n")
            else:
                 self.send("Slo-Lin\n")
        elif line == 'function5':
            FIR = 0x00
            mutebus = 0x01
            conFIR()
            self.send("ok\n")
        elif line == 'fcn5':
            if bus.read_byte_data(0x48, 0x07) == 0x00 and bus.read_byte_data(0x48, 0x25) == 0x00:
                 self.send("FAST-LIN ON\n")
            else:
                 self.send("Fast-Lin\n")
        elif line == 'function6':
#            FIR = 0xe0 
#            mutebus = 0xe1
#            conFIR()
            self.send("ok\n")
            mute()
            GPIO.output("P8_15", GPIO.LOW)  # SonyTV
            GPIO.output("P8_17", GPIO.LOW)  # AppleTV
            GPIO.output("P8_19", GPIO.HIGH)  # BBB
            initialize()
            flashb() # sox needs a pause to finish the kill
            GPIO.output("P8_9", GPIO.HIGH)  # Otto off
            with open('/sys/class/gpio/gpio23/value') as f:
                 lines = f.readlines()
            try:
                 PIN13 = int(lines[0])
            except IndexError:
                 PIN13 = 0
            print (PIN13)
            if PIN13 == 1:
               subprocess.call("nice -n -19 squeezelite -z -C 1 -o hw:0,0 -a 4096:1024:32:0", shell=True)  # no crossover
            else:
               subprocess.call("nice -n -19 squeezelite -z -C 1 -o plug:filter3 -a 4096:1024:32:0", shell=True)  # with crossover
            flashb()
            set6 = volume - int(midrange * 0.01 * volume)
            set5 = volume - int(tweeter * 0.01 * volume)
            set4 = volume - int(woofers * 0.01 * volume)
            unmute()
        elif line == 'fcn6':
#            if bus.read_byte_data(0x48, 0x07) == 0xe0 and bus.read_byte_data(0x48, 0x25) == 0x00:
#                 self.send("BRICK ON\n")
#            else:
#                 self.send("Brickwall\n")
            self.send('XO filter3\n')
        elif line == 'function7':
            bus.write_byte_data(0x70, 0x40, 0x06)
            bus.write_byte_data(0x48, 0x25, 0x80)  # deactivate oversampling filter 
            bus.write_byte_data(0x70, 0x40, 0x05)
            bus.write_byte_data(0x48, 0x25, 0x80)  # deactivate oversampling filter 
            bus.write_byte_data(0x70, 0x40, 0x04)
            bus.write_byte_data(0x48, 0x25, 0x80)  # deactivate oversampling filter 
            time.sleep (.1)
            OSF = 0x80
            self.send("ok\n")
        elif line == 'fcn7':
            OSFa = bus.read_byte_data(0x48, 0x25)
            if OSFa == 0x80:
                 self.send("OSF OFF\n")
            else:
                 self.send("OSF ON\n")
        elif line == 'get freq':
            with open('/proc/asound/Botic/pcm0p/sub0/hw_params') as f:
                 lines = f.readlines()
                 try:   
                     rawrate = lines[4]
                     rate =(int(rawrate[6:12])/1000) 
                 except IndexError:
                     rate = 0
            if rate == 0:
               self.send('no signal\n')
            elif rate == 44:
               self.send('44 kHz\n')
            elif rate == 48:
               self.send('48 kHz\n')
            elif rate == 88:
               self.send('88 kHz\n')
            elif rate == 96:
               self.send('96 kHz\n')
            elif rate == 176:
               self.send('176 kHz\n')
            elif rate == 192:
               self.send('192 kHz\n')
#  for reads back to netIO panel
        elif line == 'volnum':
               volstring = str(volume)
               self.send(volstring + '\n')
        elif line == 'tweeter':
               twstring = str(tweeter)
               self.send(twstring + '\n')
        elif line == 'midrange':
               midstring = str(midrange)       
               self.send(midstring + '\n')
        elif line == 'woofers':
               woofstring = str(woofers)
               self.send(woofstring + '\n')
        else:
            self.send('unknown command\n')
            logger.debug('Unknown command:', line)

class Server(asyncore.dispatcher):
    def __init__(self, listen_to, pollster):
        asyncore.dispatcher.__init__(self)
        self.pollster = pollster
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(listen_to)
        self.listen(5)
 
    def handle_accept(self):
        newSocket, address = self.accept()
        print("Connected from", address)
        Client(newSocket,self.pollster)

def readwrite(obj, flags):
    try:
        if flags & select.EPOLLIN:
            obj.handle_read_event()
        if flags & select.EPOLLOUT:
            obj.handle_write_event()
        if flags & select.EPOLLPRI:
            obj.handle_expt_event()
        if flags & (select.EPOLLHUP | select.EPOLLERR | select.POLLNVAL):
            obj.handle_close()
    except socket.error, e:
        if e.args[0] not in asyncore._DISCONNECTED:
            obj.handle_error()
        else:
            obj.handle_close()
    except asyncore._reraised_exceptions:
        raise
    except:
        obj.handle_error()
def police():
   global midok
   global tweetok
   global woofok
   midok = 0
   tweetok = 0
   woofok = 0
   def dacjam():
       bus.write_byte_data(0x48, 0x07, mutebus)  # mute
#       bus.write_byte_data(0x48, 0x02, 0xfc)  # automute on
#       bus.write_byte_data(0x48, 0x04, 0xff)  # automute time = 255
#       bus.write_byte_data(0x48, 0x05, 96)    # automute level
#       bus.write_byte_data(0x48, 0x0a, 0x10)  # enable 128*FSR mode
#       bus.write_byte_data(0x48, 0x0c, 0x00)  # DPLL 1a = lowest bandwidth for I2S, 10 for DSD; 0x00 is DPLL off
#       bus.write_byte_data(0x48, 0x0d, 0x20)  # THD and jitter eliminator disabled (default is 0x10 - THD 'on' & jitter 'on') 
       bus.write_byte_data(0x48, 0x0f, 0x0f)  # use stereo mode, channel 1 and latch volume
#       bus.write_byte_data(0x48, 0x25, 0x80)  # bypass the FIR oversampling filter (default is 0x00)
       bus.write_byte_data(0x48, 0x07, FIR)   # unmute, FIR filter normal, slow rolloff; fast rolloff = 40
       logger.warn('DAC register 15 reset by dacjam')
   def dacscan():
       bus.write_byte_data(0x70, 0x40, 0x06)  # midrange address
       midok = bus.read_byte_data(0x48, 0x0f)  # in stereo mode?
       pvol6 = bus.read_byte_data(0x48, 0x1b)
       if pvol6 >= 0x70:
           bus.write_byte_data(0x48, 0x1b, set6)
           logger.warn("mid volume reset by police()")
       bus.write_byte_data(0x70, 0x40, 0x05)  # tweeter address
       tweetok = bus.read_byte_data(0x48, 0x0f)  # in stereo mode?
       pvol5 = bus.read_byte_data(0x48, 0x1b)
       if pvol5 >= 0x70:
           bus.write_byte_data(0x48, 0x1b, set5)
           logger.warn("tweet volume reset by police()")
       bus.write_byte_data(0x70, 0x40, 0x04)  # woofer address
       woofok = bus.read_byte_data(0x48, 0x0f)  # in stereo mode?
       pvol4 = bus.read_byte_data(0x48, 0x1b)
       if pvol4 >= 0x70:
           bus.write_byte_data(0x48, 0x1b, set4)
           logger.warn("woof volume reset by police()")
   while initialize == 1:
      try:
         dacscan()
      except IOError as err:
#         subprocess.call("killall -9 squeezelite", shell=True)
#         subprocess.call("killall -9 sox", shell=True)      
         logger.warn("I2C read error detected by police()")
#  need way to reset busy netio ports
      if midok != 0x0f:
         bus.write_byte_data(0x70, 0x40, 0x06)
         dacjam()
#         print('midok = ', midok)
         logger.warn('midrange DAC reg 15 alert')  
      if tweetok != 0x0f:
         bus.write_byte_data(0x70, 0x40, 0x05)
         dacjam()
#         print('tweetok = ', tweetok)
         logger.warn('tweeter DAC reg 15 alert')  
      if woofok != 0x0f:
         bus.write_byte_data(0x70, 0x40, 0x04)
         dacjam()
#         print('woofok = ', woofok)
         logger.warn('woofer DAC reg 15 alert')
      time.sleep(1)

def netio():
    while True:
        evt = pollster.poll()
        for obj, flags in evt:
            readwrite(obj, flags)

def buttons():
    # configure button inputs
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
    #configure socket
    buttonsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    buttonsocket.connect(('192.168.1.53', 8194))
    # define callback behavior
    def button8_11():
        buttonsocket.sendall('speakers_out\n')
        time.sleep(1.5)
        logger.debug("did 8_11 speaker")
    def button8_12():
        buttonsocket.sendall('phones_out\n')
        time.sleep(1.5)
        logger.debug("did 8_12 phones")
    def button8_14():
        buttonsocket.sendall('SonyTV_in\n')
        time.sleep(1.5)
        logger.debug("did 8_14 STV")
    def button8_16():
        buttonsocket.sendall('AppleTV_in\n')
        time.sleep(1.5)
        logger.debug("did 8_16 ATV")
    def button8_18():
        buttonsocket.sendall('BBB_in\n')
        time.sleep(1.5)
        logger.debug("did 8_18 BBB")
   # run continuously
    while True:
        if GPIO.event_detected("P8_11"):
           button8_11()
        elif GPIO.event_detected("P8_12"):
           button8_12()
        elif GPIO.event_detected("P8_14"):
           button8_14()
        elif GPIO.event_detected("P8_16"):
           button8_16()
        elif GPIO.event_detected("P8_18"):
           button8_18()
        time.sleep(1.5)

class EPoll(object):
    def __init__(self):
        self.epoll = select.epoll()
        self.fdmap = {}
    def register(self, obj, flags):
        fd = obj.fileno()
        self.epoll.register(fd, flags)
        self.fdmap[fd] = obj
    def unregister(self, obj):
        fd = obj.fileno()
        del self.fdmap[fd]
        self.epoll.unregister(fd)
    def poll(self):
        evt = self.epoll.poll()
        for fd, flags in evt:
            yield self.fdmap[fd], flags

if __name__ == "__main__":
    pollster = EPoll()
    pollster.register(Server(("",8192),pollster), select.EPOLLIN) #iPad Old
    pollster.register(Server(("",8193),pollster), select.EPOLLIN) #F iPhoneX
    pollster.register(Server(("",8194),pollster), select.EPOLLIN) #front panel & network
    pollster.register(Server(("",8195),pollster), select.EPOLLIN) #iPad New
    pollster.register(Server(("",8196),pollster), select.EPOLLIN) #iPad New
    p1 = Process(target = netio)
    p1.start()
    p2 = Process(target = buttons)
    p2.start()
#    p3 = Process(target = police)
#    p3.start()
