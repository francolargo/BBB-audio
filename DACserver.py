#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import asyncore
import socket
import select
#import Adafruit_BBIO.GPIO as GPIO
import time
from multiprocessing import Process 
import subprocess
import smbus
import os
bus = smbus.SMBus(1)
state = 0
volume = 5
mute = 0x03  # default mute setting
FIR = 0x02  # default filter shape
#deemph = 0x40
#softeq = 3  # was 255 for eq button
# setup I2C volume, DPLL bandwidth, other es9028 parameters 
def dacregister(): # enter desired register values for initialization - these are twluke's
    bus.write_byte_data(0x48, 0x07, mute)  # mute
    bus.write_byte_data(0x48, 0x01, 0x04) # 00000100 automatically select serial/DSD
    bus.write_byte_data(0x48, 0x02, 0x3c)  # automute off
    bus.write_byte_data(0x48, 0x04, 0x00)  # automute time = 0 = disable automute
    bus.write_byte_data(0x48, 0x05, 0x68) # 01101000 default
    bus.write_byte_data(0x48, 0x06, 0x4a) # 01001010 default
    #bus.write_byte_data(0x48, 0x07, FIR) # 50k@44.1 00000010 for reference - would unmute if executed here
    bus.write_byte_data(0x48, 0x08, 0x80) # automute status 10000000
    bus.write_byte_data(0x48, 0x09, 0x18) # lock status 00011000
    bus.write_byte_data(0x48, 0x0a, 0x10) # 128fs enabled 00010000
    bus.write_byte_data(0x48, 0x0c, 0x5a) # default 01010101
    bus.write_byte_data(0x48, 0x0d, 0x20) # enable (default) 00100000
    bus.write_byte_data(0x48, 0x0e, 0x8a) # default 10001010
    bus.write_byte_data(0x48, 0x0f, 0x0f) # use stereo mode, channel 1 and latch volume
    bus.write_byte_data(0x48, 0x10, 0x00) # individual volume registers - no attenuation
    bus.write_byte_data(0x48, 0x11, 0x00)
    bus.write_byte_data(0x48, 0x12, 0x00)
    bus.write_byte_data(0x48, 0x13, 0x00)
    bus.write_byte_data(0x48, 0x14, 0x00)
    bus.write_byte_data(0x48, 0x15, 0x00)
    bus.write_byte_data(0x48, 0x16, 0x00)
    bus.write_byte_data(0x48, 0x17, 0x00)
    bus.write_byte_data(0x48, 0x18, 0xff) 
    bus.write_byte_data(0x48, 0x19, 0xff)
    bus.write_byte_data(0x48, 0x1a, 0xff)
    bus.write_byte_data(0x48, 0x1b, volume) # Master volume - starts low
    bus.write_byte_data(0x48, 0x25, 0x80) # OSF disabled 10000000
    #bus.write_byte_data(0x48, 0x26, 0d10) # CHECK THIS! All Ch 1 = 0d00 ?; All Ch 2 = 0d11 ?
    bus.write_byte_data(0x48, 0x07, FIR)   # unmute

class Client(asyncore.dispatcher_with_send):
#    print "checkpoint 1"
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
#        print (receivedData)
        receivedData = self.data + receivedData
#        print (self.data) 
        while '\n' in receivedData:
            line, receivedData = receivedData.split('\n',1)
            self.handle_command(line)
        self.data = receivedData

    def handle_command(self, line):
        # 'global' variables can be read outside of the 'handle_command' function
        global volume
        global mute
        global FIR
        global rate
        global state  
        global kill
        def mute():
            bus.write_byte_data(0x48, 0x07, mute)
            # print "mute ran"
        def unmute():
            bus.write_byte_data(0x48, 0x07, FIR)
        def conFIR():
            bus.write_byte_data(0x48, 0x07, FIR)
        if  line.startswith("set volume"):
            volume = int(line[11:14])
#            print (line)
#            print (volume)
            bus.write_byte_data(0x48, 0x1b, volume)
        elif  line == '+':
            Volm = bus.read_byte_data(0x48, 0x1b)    # read volume
            volume = Volm + 10                       # add 10 to volume setting
            if volume > 127:
                volume = 127
            bus.write_byte_data(0x48, 0x1b, volume)
        elif  line == '-':
            Volm = bus.read_byte_data(0x48, 0x1b)    # read volume
            volume = Volm - 10                       # minus 10 from volume setting
            if volume < 0:
                volume = 0
            bus.write_byte_data(0x48, 0x1b, volume)
        elif 'slow-min'in line:
            FIR = 0x62
            mute = 0x63
            conFIR()
        elif line == 'apodize':
            FIR = 0x82
            mute = 0x83
            conFIR()
        elif line == 'fast-min':
            FIR = 0x42
            mute = 0x43
            conFIR()
        elif line == 'slow-linear':
            FIR = 0x22
            mute = 0x23
            conFIR()
        elif line == 'fast-linear':
            FIR = 0x02
            mute = 0x03
            conFIR()
        elif line == 'brick':
            FIR = 0xe2
            mute = 0xe3
            conFIR()
        elif line == 'freq':
            with open('/proc/asound/Botic/pcm0p/sub0/hw_params') as f:
                 lines = f.readlines()
                 try:   
                     rawrate = lines[4]
                     rate =(int(rawrate[6:12])/1000) 
                 except IndexError:
                     rate = 0
            print(rate)
#        elif line == 'example':
#            os.system("killall -9 squeezelite")
#            time.sleep(.6)
#            with open('/sys/class/gpio/gpio23/value') as f:
#                 lines = f.readlines()
#            try:
#                 state = int(lines[0])
#            except IndexError:
#                 state = 0
#            print (state)
#            if state == 1:
#               os.system("nice -n -19 squeezelite -z -C 1 -o hw:0,0 -a 8192:2048::0")  # no crossover
#            else:
#               os.system("nice -n -19 squeezelite -z -C 1 -o plug:filter1 -a 8192:2048::0")  # with crossover 
    
class Server(asyncore.dispatcher):
#    print "checkpoint 2"
    def __init__(self, listen_to, pollster):
        asyncore.dispatcher.__init__(self)
        self.pollster = pollster
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(listen_to)
        self.listen(5)
#        print "checkpoint 7"
 
    def handle_accept(self):
        newSocket, address = self.accept()
        print "Connected from", address
        Client(newSocket,self.pollster)

def readwrite(obj, flags):
#    print "checkpoint 9"
    try:
        if flags & select.EPOLLIN:
#            print "option 1"
            obj.handle_read_event()
        if flags & select.EPOLLOUT:
#            print "option 2"
            obj.handle_write_event()
        if flags & select.EPOLLPRI:
#            print "option 3"
            obj.handle_expt_event()
            obj.handle_close()
    except socket.error, e:
        if e.args[0] not in asyncore._DISCONNECTED:
            obj.handle_error()
#            print "option 5"
        else:
            obj.handle_close()
    except asyncore._reraised_exceptions:
        raise
    except:
        obj.handle_error()
def police():
   while True:
#      if kill == 1:
#         bus.write_byte_data(0x48, 0x1b, volume) # restore volume to previous setting
#         os.system("nice -n -19 squeezelite -z -C 1 -o plug:filter1 -a 8192:2048::0")  # restart the source
#         time.sleep(.5)
#         kill = 0
      try:
         DACok = bus.read_byte_data(0x48, 0x0f)  # in stereo mode?
      except IOError as err:
         print "I2C communication failure"
#         kill = 1
#         os.system("killall -9 squeezelite")  # kill the source if I2C is frozen
#         time.sleep(.5)
      if DACok != 0x0f:
          dacregister()
#          bus.write_byte_data(0x48, 0x1b, 5) # reset volume low
      time.sleep(.3)

def netio():
    while True:
        evt = pollster.poll()
#        print "checkpoint 5"
        for obj, flags in evt:
            readwrite(obj, flags)

class EPoll(object):
#    print "chekpoint 3"
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
#        print "checkpoint 8"
        evt = self.epoll.poll()
        for fd, flags in evt:
            yield self.fdmap[fd], flags


if __name__ == "__main__":
    pollster = EPoll()
    pollster.register(Server(("",8192),pollster), select.EPOLLIN) # control source 1
    pollster.register(Server(("",8193),pollster), select.EPOLLIN) # control source 2
    pollster.register(Server(("",8194),pollster), select.EPOLLIN) # control source 3
    pollster.register(Server(("",8195),pollster), select.EPOLLIN) # control source 4
    p1 = Process(target = netio)
    p1.start()
    p2 = Process(target = police)
    p2.start()
