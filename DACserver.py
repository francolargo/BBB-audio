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
mute = 0x03  # default mute setting
FIR = 0x02  # unmute plus default filter shape
# The following routines run once to initialize the DAC
# setup I2C volume, DPLL bandwidth, other es9028 parameters 
def dacregister(): # enter desired register values for initialization - these are mine
   bus.write_byte_data(0x48, 0x07, mute)  # mute
   bus.write_byte_data(0x48, 0x01, 0x04) # 00000100 automatically select serial/DSD
   bus.write_byte_data(0x48, 0x02, 0x3c)  # automute off
   bus.write_byte_data(0x48, 0x04, 0x00)  # automute time = 0 = disable automute
   bus.write_byte_data(0x48, 0x05, 0x68) # 01101000 default
   bus.write_byte_data(0x48, 0x06, 0x4a) # 01001010 default
   #bus.write_byte_data(0x48, 0x07, 0x02) # 50k@44.1 00000010 for reference - would unmute if executed here
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
   bus.write_byte_data(0x48, 0x18, 0xff) # Master volume - no attenuation
   bus.write_byte_data(0x48, 0x19, 0xff)
   bus.write_byte_data(0x48, 0x1a, 0xff)
   bus.write_byte_data(0x48, 0x1b, 0x7f)
   bus.write_byte_data(0x48, 0x25, 0x80) # OSF disabled 10000000
   #bus.write_byte_data(0x48, 0x26, 0d10) # CHECK THIS! All Ch 1 = 0d00?; All Ch 2 = 0d11?
   bus.write_byte_data(0x48, 0x07, FIR)   # unmute
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
            bus.write_byte_data(0x48, 0x07, mute)
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
            mute = 0x61
            bus.write_byte_data(0x48, 0x07, FIR)
        elif line == 'function3':
            FIR = 0x80
            mute = 0x81
            bus.write_byte_data(0x48, 0x07, FIR)
        elif line == 'function2':
            FIR = 0x40
            mute = 0x41
            bus.write_byte_data(0x48, 0x07, FIR)
        elif line == 'function4':
            FIR = 0x20
            mute = 0x21
            bus.write_byte_data(0x48, 0x07, FIR)
        elif line == 'function5':
            FIR = 0x00
            mute = 0x01
            bus.write_byte_data(0x48, 0x07, FIR)
        elif line == 'function6':
            FIR = 0xe0
            mute = 0xe1
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
      except IOError as err:
         #os.system("killall -9 squeezelite")
         #os.system("killall -9 sox")         
         print "reset ran from police"
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
    # print "checkpoint 4"
    pollster = EPoll()
    pollster.register(Server(("",8192),pollster), select.EPOLLIN) #iPad Old
    #pollster.register(Server(("",8193),pollster), select.EPOLLIN) #F iPhoneX
    #pollster.register(Server(("",8194),pollster), select.EPOLLIN) #front panel
    #pollster.register(Server(("",8195),pollster), select.EPOLLIN) #iPad New
    p1 = Process(target = netio)
    p1.start()
    #p2 = Process(target = police)
    #p2.start()

