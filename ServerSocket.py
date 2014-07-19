import socket
import sys
import time

MESSAGE_DELAY = 1000

HOST, PORT = "localhost", 9999
data = " ".join(sys.argv[1:])

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Create function get get time from
current_milli_time = lambda: int(round(time.time() * 1000))
timer = 0

try:
    # Connect to server and send data
    sock.connect((HOST, PORT))

    while(1)
        if( (current_milli_time() - timer) > MESSAGE_DELAY)    
            sock.sendall("HI" + "\n")

            # Receive data from the server and shut down
            received = sock.recv(1024)
            print "Sent:     {}".format(data)
            print "Received: {}".format(received)
            time.strftime("%S")
            timer = current_milli_time()
        
finally:
    sock.close()


