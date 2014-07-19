import sys
import SocketServer

class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def processPKT(self, data_to_process):
        local_data = bytearray(data_to_process)
        print "Throttle:",
        print str(local_data[1])
        print "Left/Right:",
        print str(local_data[2])
        print "Something else:",
        print str(local_data[4])

    def isValidPKT(self):
        byteArr = bytearray(self.data)
        #Check the checksum
        checksum = 0
        #print sys.getsizeof(byteArr)
        for x in range(0, 6) :
            #print x
            if((x!=0) and (x!=5)):
                checksum = byteArr[ x ] +  checksum
        return( ( checksum & 0x0F ) == ( ( byteArr[5] & 0xF0 ) >> 4 ) )    

    def handle(self):
        while 1:
            self.data = self.request.recv(1024)
            if not self.data:
                break
            self.data = self.data.strip()
            #print str(self.client_address[0]) + " wrote: "
            #print self.data
            self.request.send(self.data.upper())
            if self.isValidPKT( ):
                self.processPKT( self.data )
    

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
