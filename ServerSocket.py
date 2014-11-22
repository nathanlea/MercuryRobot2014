#!/usr/bin/python

###########################
#
# Verson to be used on BBB
#       11/22/2014
#
###########################
import sys
import SocketServer
import threading
import Queue
import random
import socket
import binascii
import struct
import Adafruit_BBIO.GPIO as GPIO
#from multiprocessing import Process
#from VideoCapture import *
#from PIL import *

class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    responce = '\x06\x0F\x0F\x0F\x0F\x0C\x78\x0F'
    rQue = Queue.Queue()
    que = Queue.Queue()
    processQue = Queue.Queue()
    
    def processPKT(self):
        go = 0
        # print "valid"
        # print "Throttle:",
        # print str(self.processQue.get())
        # print "Left/Right:",
        # print str(self.processQue.get())
        # print "Something else:",
        # print str(self.processQue.get())
        # print "Last Something else",
        # print str(self.processQue.get())

    def isValidPKT(self):
        #Check the checksum
        checksum = 0
        Rchecksum = 0
        if( self.que.qsize() > 5 ):
            temp = self.que.get()
            if (((temp >> 4) ^ 0xFF) == 0xFF):
                for x in range(0,5):
                    #print x
                    if( x!=4 ):
                        read = self.que.get()
                        checksum += read
                        self.processQue.put(read)
                    else:
                        Rchecksum = self.que.get()
                if ( ( checksum & 0x0F ) == ( ( Rchecksum & 0xF0 ) >> 4 ) ):
                    self.processPKT()
                    return True
                else:
                    self.processQue.queue.clear()
                    return False
            else:                
                return False
        else:
            return False
            
    def randrequest( self ):
        sensor1 = 0
        sensor2 = 0
        sensor3 = 0
        sensor4 = 0
        volt    = 0
        amp     = 0
        footer  = 0
        #print "1"
        
        sensor1 = random.randint(0,80)
        sensor2 = random.randint(0,80)
        sensor3 = random.randint(0,20)
        sensor4 = random.randint(0,50)
        volt    = random.randint(0,12)
        amp     = random.randint(0,255)
        # sensor1 = 10
        # sensor2 = 10
        # sensor3 = 10
        # sensor4 = 10
        # volt    = 10
        # amp     = 10
        
        #print "2"
        
        footer = ( ( ( ( sensor1 + sensor2 + sensor3 + sensor4 + volt + amp ) << 4 ) & 0xF0 ) | 0x0F )
        
        #print str(footer)
        #self.responce = '\x06' + sensor1 + '' + sensor2 + '' + sensor3 + '' + sensor4 + '' + volt + '' + amp + '' + footer
        self.packed_data = struct.pack('BBBBBBBB', 6, sensor1, sensor2, sensor3, sensor4, volt, amp, footer)
        
        # self.rQue.put('\x06')
        # self.rQue.put( b'sensor1' )
        # self.rQue.put( b'sensor2' )
        # self.rQue.put( b'sensor3' )
        # self.rQue.put( b'sensor4' )
        # self.rQue.put( b'volt' )
        # self.rQue.put( b'amp' )
        # self.rQue.put( b'footer' )
        
        #print str(footer)
            

    def handle(self):
        try: 
            GPIO.output("P8_10", GPIO.HIGH)
            GPIO.output("P8_11", GPIO.LOW)
            print "Connected"
            while 1:
                self.data = self.request.recv(1024)
                self.data = self.data.strip()
                byteArr = bytearray(self.data)
                
                for x in range(0, len(self.data)):
                    self.que.put(byteArr[x])
                
                #print str(self.client_address[0]) + " wrote: "
                #print self.data
                #self.request.send(self.data.upper())
                if self.isValidPKT( ):
                    self.randrequest( )
                    #print >>sys.stderr, 'sending "%s"' % binascii.hexlify(self.packed_data)
                    self.request.sendall(self.packed_data)
                    self.rQue.queue.clear()
                    #self.request.send( self.responce )
        except:
            GPIO.output("P8_11", GPIO.HIGH)
            GPIO.output("P8_10", GPIO.LOW)
            print "Disconnected"
                
#def camera_thread( ):
#    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    server_socket.bind((socket.gethostname(),5000))
#    server_socket.listen(5)
#    while 1:
#        client_socket, address = server_socket.accept()        
#        image = camera.getImage().convert("RGB")
#        image = image.resize((640,480))
#        #image.save("webcam.jpg")
#        data = image.tostring()
#        client_socket.sendall(data)    
                
#class Camera(SocketServer.BaseRequestHandler):      
#    def handle( self ):
        #server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.request.bind("localhost")
        #self.listen(5)       
        
#        while 1:
#            try:
#                #client_socket, address = server_socket.accept()            
#                image = camera.getImage().convert("RGB")
#                image = image.resize((640,480))
#                #image.save("webcam.jpg")
#                self.data = image.tostring()
#                self.request.sendall(self.data)
#            except socket.error as e:
#                break
#                #print e.strerror 
        
def initServe( ):
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)
    server.serve_forever()
    
if __name__ == "__main__":
   # global camera
#    global image
    try:
        HOST, PORT = "192.168.137.233", 9999
    #    CHOST, CPORT = "localhost", 5000
        
        print "Your IP address is: ", socket.gethostbyname(socket.gethostname())
        print "Server Waiting for client on port 9999"
        GPIO.setup("P8_10",  GPIO.OUT)
        GPIO.setup("P8_11",  GPIO.OUT)
        #camera = Device()
    
        #image = camera.getImage()
        
        #camera = Device()
        #image = camera.getImage()
        
        #threading.Thread(target=camera_thread).start()    
        
        GPIO.output("P8_11",  GPIO.HIGH)
        server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        GPIO.output("P8_10", GPIO.LOW)
        GPIO.output("P8_11", GPIO.LOW)
        GPIO.cleanup()
    # server2 = SocketServer.TCPServer((CHOST, CPORT), Camera)
    # server2.serve_forever    
    
    
    # Create the server, binding to localhost on port 9999
    #server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    #server.serve_forever()
