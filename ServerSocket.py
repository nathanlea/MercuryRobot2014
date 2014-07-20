import sys
import SocketServer
import Queue

class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    responce = '\x06\x0F\x0F\x0F\x0F\x0C\x78\x0F'
    que = Queue.Queue()
    processQue = Queue.Queue()
    
    def processPKT(self):
        print "Throttle:",
        print str(self.processQue.get())
        print "Left/Right:",
        print str(self.processQue.get())
        print "Something else:",
        print str(self.processQue.get())
        print "Last Something else",
        print str(self.processQue.get())

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
                    self.processQue.clear()
                    return False
            else:                
                return False
        else:
            return False

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
                self.request.send( self.responce )
    

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
