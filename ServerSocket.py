import sys
import SocketServer
import Queue
import random
import socket
import binascii
import struct

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
                print >>sys.stderr, 'sending "%s"' % binascii.hexlify(self.packed_data)
                self.request.sendall(self.packed_data)
                self.rQue.queue.clear()
                #self.request.send( self.responce )

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()