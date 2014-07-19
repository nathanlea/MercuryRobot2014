import socket
import sys
import time

class clientController:

    def __init__(self):
        self.b = 1

    MESSAGE_DELAY = 1000

    HOST, PORT = "localhost", 9999
    data = '\x04\x0F\x0F\x00\x00\xEF'
    #data = 'aabbccdd'

    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Create function get get time from
    current_milli_time = lambda( self ): int(round(time.time() * 1000))
    timer = 0

    def processPKT( self, data_to_process):
        local_data = bytearray(data_to_process)
        print "Voltage:",
        print str(local_data[1])
        print "Amps in (mA):",
        print str(local_data[2])
        print "Something else:",
        print str(local_data[4])

    def isValidPKT( self ):
        byteArr = bytearray( self.received )
        #Check the checksum
        checksum = 0
        print sys.getsizeof(byteArr)
        for x in range(0, 8) :
            #print x
            if((x!=0) and (x!=7)):
                checksum = byteArr[ x ] +  checksum
        return( ( checksum & 0x0F ) == ( ( byteArr[7] & 0xF0 ) >> 4 ) ) 

    def main( self ):
        try:
            # Connect to server and send data
            self.sock.connect((self.HOST, self.PORT))

            while(1):
                if( (self.current_milli_time() - self.timer) > self.MESSAGE_DELAY):    
                    self.sock.sendall( self.data )

                    # Receive data from the server and shut down
                    self.received = self.sock.recv(1024)
                    if self.isValidPKT( ):
                        self.processPKT( self.received )
                    #print "Sent:     {}".format(data)
                    #print "Received: {}".format(received)
                    self.timer = self.current_milli_time()
                
        finally:
            self.sock.close()

if __name__ == "__main__":
    ClientMain = clientController()
    ClientMain.main(  )

