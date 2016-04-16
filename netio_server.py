#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncore
import socket
import select
import Adafruit_BBIO.GPIO as GPIO
import time
import subprocess
import smbus
import os
# misc. GPIO setup as needed to address pins
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
# initialize for BBB -> speakers
os.chdir("/usr/script")
os.system("amixer -c miniStreamer cset numid=8 1") # set up miniStreamer for SPDIF input
os.system("pkill -f squeezelite")
os.system("pkill -f sox")
os.system("squeezelite -z -C 1 -o default -a 8192:2048::0") # start squeezelite as default
time.sleep(1)
# presets for gentle startup
balance = 20
volume = 5
tweeter = 40
midrange = 30
woofer = 0
rate = 0
rawrate = 0
bus = smbus.SMBus(1)
mutebus = 207
# setup I2C volume control
try:
   bus.write_byte_data(0x70, 0x40, 0x06)
   bus.write_byte_data(0x48, 0x17, volume)
   bus.write_byte_data(0x48, 0x0a, 206)
   bus.write_byte_data(0x70, 0x40, 0x05)
   bus.write_byte_data(0x48, 0x17, volume)
   bus.write_byte_data(0x48, 0x0a, 206)
   bus.write_byte_data(0x70, 0x40, 0x04)
   bus.write_byte_data(0x48, 0x17, volume)
   bus.write_byte_data(0x48, 0x0a, 206)
except IOError as err:
   print "DAC turned on?"
else:
   print "DAC ready"
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

    def handle_command(self, line):
        global tweeter
        global midrange
        global woofer  # woofer controls not used - set at full volume
        global volume
        global balance
        global set4
        global set5
        global set6
        global rate
        global mutebus
        global PIN13
        global PIN19
        def mute():
            bus.write_byte_data(0x70, 0x40, 0x06)
            bus.write_byte_data(0x48, 0x17, 0x00)
            bus.write_byte_data(0x48, 0x17, 0xcf)
            bus.write_byte_data(0x70, 0x40, 0x05)
            bus.write_byte_data(0x48, 0x17, 0x00)
            bus.write_byte_data(0x48, 0x17, 0xcf)
            bus.write_byte_data(0x70, 0x40, 0x04)
            bus.write_byte_data(0x48, 0x17, 0x00)
            bus.write_byte_data(0x48, 0x17, 0xcf)
        def unmute():
            bus.write_byte_data(0x70, 0x40, 0x06)
            bus.write_byte_data(0x48, 0x17, 0xce)
            bus.write_byte_data(0x48, 0x17, set6)
            bus.write_byte_data(0x70, 0x40, 0x05)
            bus.write_byte_data(0x48, 0x17, 0xce)
            bus.write_byte_data(0x48, 0x17, set5)
            bus.write_byte_data(0x70, 0x40, 0x04)
            bus.write_byte_data(0x48, 0x17, 0xce)
            bus.write_byte_data(0x48, 0x17, set4)
    
        if line == 'BBB_in':
            self.send('BBB_in\n')
            mute()
            GPIO.output("P8_15", GPIO.LOW)  # SonyTV
            GPIO.output("P8_17", GPIO.LOW)  # AppleTV
            GPIO.output("P8_19", GPIO.HIGH)  # BBB
            time.sleep(1)
            os.system("pkill -f squeezelite")
            #time.sleep(.1)
            os.system("pkill -f sox")
            GPIO.output("P8_9", GPIO.HIGH)  # Otto off
            with open('/sys/class/gpio/gpio23/value') as f:
                 lines = f.readlines()
            try:
                 PIN13 = int(lines[0])
            except IndexError:
                 PIN13 = 0
            print(PIN13)
            if PIN13 == 1:
               os.system("squeezelite -z -C 1 -o hw:0,0 -a 8192:2048::0")  # no crossover
            else:
               os.system("squeezelite -z -C 1 -o default -a 8192:2048::0")  # with crossover
            time.sleep(1)
            volume = 5
            set6 = volume - int(midrange * 0.01 * volume)
            set5 = volume - int(woofer * 0.01 * volume)
            set4 = volume - int(tweeter * 0.01 * volume)
            unmute()
        elif line == 'speakers':
            self.send('speakers_out\n')
            GPIO.output("P8_10", GPIO.HIGH)  # Speaker LED
            GPIO.output("P8_13", GPIO.LOW)  # Headphone LED
            mute()
            time.sleep(1)
            os.system("pkill -f squeezelite")
            os.system("pkill -f sox")
            with open('/sys/class/gpio/gpio22/value') as f:
                 lines = f.readlines()
            try:
                 PIN19 = int(lines[0])
            except IndexError:
                 PIN19 = 0
            print(PIN19)
            if PIN19 == 1:
               os.system("squeezelite -z -C 1 -o default -a 8192:2048::0")
               time.sleep(1)
            else:
               os.system("chrt -f 45 sox --buffer 512  -c 2 -t alsa hw:1,0 -t alsa plug:TV-in &")
            volume = 5
            set6 = volume - int(midrange * 0.01 * volume)
            set5 = volume - int(woofer * 0.01 * volume)
            set4 = volume - int(tweeter * 0.01 * volume)
            unmute()
        elif line == 'phones':
            self.send('phones_out\n')
            GPIO.output("P8_10", GPIO.LOW)  # Speaker LED
            GPIO.output("P8_13", GPIO.HIGH)  # Headphone LED
            mute()
            time.sleep(1)
            os.system("pkill -f squeezelite")
            os.system("pkill -f sox")
            with open('/sys/class/gpio/gpio22/value') as f:
                 lines = f.readlines()
            try:
                 PIN19 = int(lines[0])
            except IndexError:
                 PIN19 = 0
            print(PIN19)
            if PIN19 == 1:
               os.system("squeezelite -z -C 1 -o hw:0,0 -a 8192:2048::0")
               time.sleep(1)
            else:
               os.system("chrt -f 45 sox --buffer 512  -c 2 -t alsa hw:1,0 -t alsa plug:TV-inhw &")
            volume = 5
            set6 = volume - int(midrange * 0.01 * volume)
            set5 = volume - int(woofer * 0.01 * volume)
            set4 = volume - int(tweeter * 0.01 * volume)
            unmute()
        elif line == 'AppleTV_in':
            self.send('AppleTV_in\n')
            mute()
            GPIO.output("P8_15", GPIO.LOW)  # SonyTV
            GPIO.output("P8_17", GPIO.HIGH)  # AppleTV
            GPIO.output("P8_19", GPIO.LOW)  # BBB
            time.sleep(1)
            os.system("pkill -f squeezelite")
            os.system("pkill -f sox")
            GPIO.setup("P8_7", GPIO.OUT) 
            GPIO.output("P8_9", GPIO.LOW)  # turn on SPDIF switch
            GPIO.output("P8_7", GPIO.LOW)  # select optical input
            with open('/sys/class/gpio/gpio23/value') as f:
                 lines = f.readlines()
            try:
                 PIN13 = int(lines[0])
            except IndexError:
                 PIN13 = 0
            print(PIN13)
            if PIN13 == 1:
               os.system("chrt -f 45 sox --buffer 512  -c 2 -t alsa hw:1,0 -t alsa plug:TV-inhw &")
            else:
               os.system("chrt -f 45 sox --buffer 512  -c 2 -t alsa hw:1,0 -t alsa plug:TV-in &")
            volume = 5
            set6 = volume - int(midrange * 0.01 * volume)
            set5 = volume - int(woofer * 0.01 * volume)
            set4 = volume - int(tweeter * 0.01 * volume)
            unmute()
        elif line == 'SonyTV_in':
            self.send('SonyTV_in\n')
            mute()
            GPIO.output("P8_15", GPIO.HIGH)  # SonyTV
            GPIO.output("P8_17", GPIO.LOW)  # AppleTV
            GPIO.output("P8_19", GPIO.LOW)  # BBB
            time.sleep(1)
            os.system("pkill -f squeezelite")
            os.system("pkill -f sox")
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
               os.system("chrt -f 45 sox --buffer 512  -c 2 -t alsa hw:1,0 -t alsa plug:TV-inhw &")
            else:
               os.system("chrt -f 45 sox --buffer 512  -c 2 -t alsa hw:1,0 -t alsa plug:TV-in &")
            volume = 5
            set6 = volume - int(midrange * 0.01 * volume)
            set5 = volume - int(woofer * 0.01 * volume)
            set4 = volume - int(tweeter * 0.01 * volume)
            unmute()
        elif line.startswith("set it to"):
	    volume = int(line[10:13])
            #print (line)
            set6 = volume - int(midrange * 0.01 * volume)
            set5 = volume - int(woofer * 0.01 * volume)
            set4 = volume - int(tweeter * 0.01 * volume)
            bus.write_byte_data(0x70, 0x40, 0x06)
            bus.write_byte_data(0x48, 0x17, set6)
            bus.write_byte_data(0x70, 0x40, 0x05)
            bus.write_byte_data(0x48, 0x17, set5)
            bus.write_byte_data(0x70, 0x40, 0x04)
            bus.write_byte_data(0x48, 0x17, set4)
            self.send("ok\n")
        elif line.startswith("tweeterset"):
            tweeter = int(line[11:14])
            #print (line)
            set4 = volume - int(tweeter * 0.01 * volume)
            bus.write_byte_data(0x70, 0x40, 0x04)
            bus.write_byte_data(0x48, 0x17, set4)
            self.send("ok\n")
        elif line.startswith("midrangeset"):
            midrange = int(line[12:15])
            #print (line)
            set6 = volume - int(midrange * 0.01 * volume)
            bus.write_byte_data(0x70, 0x40, 0x06)
            bus.write_byte_data(0x48, 0x17, set6)
            self.send("ok\n")
        elif line.startswith("balanceset"):
            balance = int(line[11:14]) # for balance range 0-40, 20 = centered
            #print (balance)
            if balance >= 20:
                bus.write_byte_data(0x70, 0x40, 0x06)
                bus.write_byte_data(0x48, 0x00, balance - 20)
                bus.write_byte_data(0x48, 0x04, balance - 20)
                bus.write_byte_data(0x48, 0x01, 0)
                bus.write_byte_data(0x48, 0x05, 0)
                bus.write_byte_data(0x70, 0x40, 0x05)
                bus.write_byte_data(0x48, 0x00, balance - 20)
                bus.write_byte_data(0x48, 0x04, balance - 20)
                bus.write_byte_data(0x48, 0x01, 0)
                bus.write_byte_data(0x48, 0x05, 0)
                bus.write_byte_data(0x70, 0x40, 0x04)
                bus.write_byte_data(0x48, 0x00, balance - 20)
                bus.write_byte_data(0x48, 0x04, balance - 20)
                bus.write_byte_data(0x48, 0x01, 0)
                bus.write_byte_data(0x48, 0x05, 0)
            else:
                bus.write_byte_data(0x70, 0x40, 0x06)
                bus.write_byte_data(0x48, 0x01, 20 - balance)
                bus.write_byte_data(0x48, 0x05, 20 - balance)
                bus.write_byte_data(0x48, 0x00, 0)
                bus.write_byte_data(0x48, 0x04, 0)
                bus.write_byte_data(0x70, 0x40, 0x05)
                bus.write_byte_data(0x48, 0x01, 20 - balance)
                bus.write_byte_data(0x48, 0x05, 20 - balance)
                bus.write_byte_data(0x48, 0x00, 0)
                bus.write_byte_data(0x48, 0x04, 0) 
                bus.write_byte_data(0x70, 0x40, 0x04)
                bus.write_byte_data(0x48, 0x01, 20 - balance)
                bus.write_byte_data(0x48, 0x05, 20 - balance)
                bus.write_byte_data(0x48, 0x00, 0)
                bus.write_byte_data(0x48, 0x04, 0) 
            self.send("ok\n") 
        elif line == 'toggle mute':
            bus.write_byte_data(0x70, 0x40, 0x06)   
            mutebus = bus.read_byte_data(0x48, 0x0a)
            if mutebus == 206:
                 bus.write_byte_data(0x70, 0x40, 0x06)
                 bus.write_byte_data(0x48, 0x0a, 207)
                 bus.write_byte_data(0x70, 0x40, 0x05)
                 bus.write_byte_data(0x48, 0x0a, 207)
                 bus.write_byte_data(0x70, 0x40, 0x04)
                 bus.write_byte_data(0x48, 0x0a, 207)
            else:
                 bus.write_byte_data(0x70, 0x40, 0x06)
                 bus.write_byte_data(0x48, 0x0a, 206)
                 bus.write_byte_data(0x70, 0x40, 0x05)
                 bus.write_byte_data(0x48, 0x0a, 206)
                 bus.write_byte_data(0x70, 0x40, 0x04)
                 bus.write_byte_data(0x48, 0x0a, 206)
            self.send("ok\n")
        elif line == 'mute on':
            if mutebus == 207:
                 self.send("MUTE\n")
                 print("unmuted")
            elif mutebus == 206:
                 self.send("UNMUTE\n")
                 print("muted")
            #self.send("ok\n")
        elif line == 'get freq':
            with open('/proc/asound/Botic/pcm0p/sub0/hw_params') as f:
                 lines = f.readlines()
                 try:   
                     rawrate = lines[4]
                     rate =(int(rawrate[6:12])/1000) 
                 except IndexError:
                     rate = 0
            # print(rate)
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
        elif line == 'volume':
               volstring = str(volume)
               self.send(volstring + '\n')
        elif line == 'tweeter':
               twstring = str(tweeter)
               print (twstring)
               self.send(twstring + '\n')
        elif line == 'midrange':
               print (midrange)
               midstring = str(midrange)       
               print (midstring)
               self.send(midstring + '\n') 
        elif line == 'balance':
               balstring = str(balance)        
               print (balstring)
               self.send(balstring + '\n') 
        else:
            self.send('unknown command\n')
            print 'Unknown command:', line


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
    pollster.register(Server(("",8192),pollster), select.EPOLLIN) #iPad
    pollster.register(Server(("",8193),pollster), select.EPOLLIN) #F iPhone6
    pollster.register(Server(("",8194),pollster), select.EPOLLIN) #front panel
    pollster.register(Server(("",8195),pollster), select.EPOLLIN) #LR iPhone5
    while True:
        evt = pollster.poll()
        for obj, flags in evt:
            readwrite(obj, flags)
