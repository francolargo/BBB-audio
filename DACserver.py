#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import asyncore
import socket
import select
import time
from multiprocessing import Process 
import subprocess
import smbus
import os
mutebus = 0x61  # default mute setting
FIR = 0x60  # unmute plus default filter shape
# The following routines run once to initialize the DAC
# setup I2C volume, DPLL bandwidth, other es9028 parameters 
def dacregister(): # enter desired register values for initialization
   bus.write_byte_data(0x48, 0x07, mutebus)  # mute
   bus.write_byte_data(0x48, 0x02, 0xfc)  # automute on
   bus.write_byte_data(0x48, 0x04, 0xff)  # automute time = 255
   bus.write_byte_data(0x48, 0x05, 96)    # automute level
   bus.write_byte_data(0x48, 0x0c, 0x1a)  # DPLL = lowest bandwidth for I2S, 10 for DSD
   bus.write_byte_data(0x48, 0x0f, 0x07)  # use stereo mode, channel 1 and latch volume
   bus.write_byte_data(0x48, 0x07, FIR)   # unmute, FIR filter normal, slow rolloff; fast rolloff = 40
def mayday(): #this function is optional
   #print "mayday called"
   try:
      bus.write_byte_data(0x48, 0x00, 0x01)  # reset DAC
   except IOError as err:
      print "soft reset exception"
   time.sleep(.2)
   dacregister()
dacregister()
print "DAC ready"
# This begins the server function to listen for control commands
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
            line, receivedData = receivedData.split('\n',1)
            self.handle_command(line)
        self.data = receivedData

def handle_command(self, line): #commands for remote control go here
        global mutebus
        global FIR
        global rate  
        def mute():
            bus.write_byte_data(0x48, 0x07, mutebus)
        def unmute():
            bus.write_byte_data(0x48, 0x07, FIR)
        if  line.startswith("set it to"): #volume command = "set it to XXX"
            volume = int(line[10:13])
            bus.write_byte_data(0x48, 0x1b, volume)
        elif line == 'mute':
            mute()
        elif line == 'unmute':
            unmute()
        elif line == 'function1':
            FIR = 0x60
            mutebus = 0x61
            bus.write_byte_data(0x48, 0x07, FIR)
        elif line == 'function3':
            FIR = 0x80
            mutebus = 0x81
            bus.write_byte_data(0x48, 0x07, FIR)
        elif line == 'function2':
            FIR = 0x40
            mutebus = 0x41
            bus.write_byte_data(0x48, 0x07, FIR)
        elif line == 'function4':
            FIR = 0x20
            mutebus = 0x21
            bus.write_byte_data(0x48, 0x07, FIR)
        elif line == 'function5':
            FIR = 0x00
            mutebus = 0x01
            bus.write_byte_data(0x48, 0x07, FIR)
        elif line == 'function6':
            FIR = 0xe0
            mutebus = 0xe1
            bus.write_byte_data(0x48, 0x07, FIR)
        elif line == 'get freq':
            with open('/proc/asound/Botic/pcm0p/sub0/hw_params') as f:
                 lines = f.readlines()
                 try:   
                     rawrate = lines[4]
                     rate =(int(rawrate[6:12])/1000) 
                 except IndexError:
                     rate = 0
            print(rate)

class Server(asyncore.dispatcher):
    def __init__(self, listen_to, pollster):
        asyncore.dispatcher.__init__(self)
        self.pollster = pollster
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(listen_to)
        self.listen(5)

    def handle_accept(self):
        newSocket, address = self.accept()
        print "Connected from", address
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
   while True:
      try:
         DACok = bus.read_byte_data(0x48, 0x0f)  # in stereo mode?
         bus.write_byte_data(0x70, 0x40, 0x05)  # tweeter address
         tweetok = bus.read_byte_data(0x48, 0x0f)  # in stereo mode?
         bus.write_byte_data(0x70, 0x40, 0x04)  # woofer address
         woofok = bus.read_byte_data(0x48, 0x0f)  # in stereo mode?
      except IOError as err:
         os.system("killall -9 squeezelite")
         os.system("killall -9 sox")         
         print "reset ran from point 1"
         reset()
      if DACok != 0x07:
         mayday()
      time.sleep(.3)
         # print "tick"
def netio():
    while True:
        evt = pollster.poll()
        for obj, flags in evt:
            readwrite(obj, flags)
class EPoll(object):
    # print "chekpoint 3"
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
        # print "checkpoint 8"
        evt = self.epoll.poll()
        for fd, flags in evt:
            yield self.fdmap[fd], flags


if __name__ == "__main__":
    # print "checkpoint 4"
    pollster = EPoll()
    pollster.register(Server(("",8192),pollster), select.EPOLLIN) #iPad Old
    #pollster.register(Server(("",8193),pollster), select.EPOLLIN) #F iPhoneX
    #pollster.register(Server(("",8194),pollster), select.EPOLLIN) #front panel
    #pollster.register(Server(("",8195),pollster), select.EPOLLIN) #iPad New
    p1 = Process(target = police)
    p1.start()
    p2 = Process(target = netio)
    p2.start()

