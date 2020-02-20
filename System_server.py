#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import asyncore
import socket
import select
import RPi.GPIO as GPIO
import time
from multiprocessing import Process
import subprocess

#Initial GPIO-setup
GPIO.setwarnings(False)
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
# misc. GPIO setup as needed to address pins
GPIO.setup(16, GPIO.OUT) # green wire = BBB
GPIO.output(16, GPIO.LOW)
GPIO.setup(19, GPIO.OUT) # blue wire = BBB
GPIO.output(19, GPIO.LOW)
GPIO.setup(26, GPIO.OUT) # DAC
GPIO.output(26, GPIO.LOW)
GPIO.setup(20, GPIO.OUT) # DAC
GPIO.output(20, GPIO.LOW)
GPIO.setup(21, GPIO.OUT) # DAC
GPIO.output(21, GPIO.LOW)
timeout = 3 # TCP socket timeout
#print "checkpoint 1"
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
        receivedData = self.recv(8192)
        if not receivedData:
            self.close()
            return
        receivedData = self.data + receivedData
        while '\n' in receivedData:
            line, receivedData = receivedData.split('\n',1)
            self.handle_command(line)
        self.data = receivedData
        print 'receivedData =', receivedData
    def handle_command(self, line):
        print line
        if line == 'BBB_ready':
             # this is the entry point for 1st amp power-on
             # this means the DAC is initialized and netio_server is launched on BBB
             # so it's OK to start amps and then start an I2S source
#             print "checkpoint 2"
             time.sleep(4) #tweak for BBB readiness
             GPIO.output(20, GPIO.HIGH)
             time.sleep(.5)
             GPIO.output(21, GPIO.HIGH)
             time.sleep(4) # tweak
#             print "checkpoint 2.1"
             try:
                subprocess.call("echo 'AppleTV_in\n' | nc -n -q .2 -w 2 192.168.1.53 8194", shell=True)
             except IOError as a:
                print(a)
                print "AppleTV echo exception"
             except socket.error as j:
                print(j)
#                print "socket.error"
             print "checkpoint 2.2"
        elif line == 'DAC_start': # from remote 'on' button
             print "checkpoint 3"
             try:
                GPIO.output(26, GPIO.HIGH)
             except IOError as b:
                print(b)
                print "DAC_start failed"
             except socket.error as f:
                print(f)
                print "DAC_start failed"
        elif line == 'speakers': # nc return from netio_server startup
             try:
                GPIO.output(20, GPIO.HIGH)
                time.sleep(.5)
                GPIO.output(21, GPIO.HIGH)
             except:
                print "amp startup via speakers failed"
        elif line == 'headphones': # nc return from netio_server startup
             try:
#                speakers = 0
                GPIO.output(20, GPIO.LOW)
                time.sleep(.5)
                GPIO.output(21, GPIO.LOW)             #print "speakers = 0"
             except:
                print "amp shutdown via headphones failed"
        elif line == 'All_off':
             self.send('All_off\n')
             print "shutdown called"
             try:
                subprocess.call("echo 'initialize\n' | nc -n -q .2 -w 1 192.168.1.53 8194", shell=True)
                time.sleep(1)
#                subprocess.call("echo 'shutdown\n' | nc -n -q .2 -w 1 192.168.1.53 8194", shell=True)
             except IOError as g:
                print(g)
#                print "IOError"
             except socket.error as h:
                print(h)
#                print "socket.error"
             try:
                GPIO.output(21, GPIO.LOW)
                time.sleep(.5)
                GPIO.output(20, GPIO.LOW)
                time.sleep(12)
                GPIO.output(26, GPIO.LOW)
                time.sleep(5)
             except IOError as d:
                print(d)
#                print "GPIO error"
             except socket.error as c:
                print(c)
#                obj.handle_close
        else:
             self.send('unknown command\n')
             print 'Unknown command:', line

class Server(asyncore.dispatcher):
    def __init__(self, listen_to, pollster):
        asyncore.dispatcher.__init__(self)
        self.pollster = pollster
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(timeout) # F addition to manage sockets
        self.bind(listen_to)
        self.listen(50)

    def handle_accept(self):
        newSocket, address = self.accept()
#        print "Connected from", address
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
    pollster.register(Server(("",4321),pollster), select.EPOLLIN) #iPad Old
    pollster.register(Server(("",4322),pollster), select.EPOLLIN) #F iPhoneX
    pollster.register(Server(("",4323),pollster), select.EPOLLIN) #network
    pollster.register(Server(("",4324),pollster), select.EPOLLIN) #iPad New
    pollster.register(Server(("",4325),pollster), select.EPOLLIN) #iPhone6
    while True:
       try:
          evt = pollster.poll()
          for obj, flags in evt:
              readwrite(obj, flags)
       except socket.error, e:
          print "socket error main"
