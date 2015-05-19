#!/usr/bin/python
import sys
import socket
import threading
import Queue
import time
import struct
import select
import binascii

#ip = sys.argv[1]
#port = sys.argv[2]

HOST, PORT = "192.168.182.31", 9999
data = '\x04\x0F\x0F\x00\x00\xEF'
#data = 'aabbccdd'


# Create function get get time from
current_milli_time = lambda: int(round(time.time() * 1000))
timer = 0
running = True

print "Driving Application"
print "Version 0.5"
print "License: the author hereby waives ALL claim of copyright in this work"
print ""

print ("IP to connect to: " + str(HOST))
print ("Port:             " + str(PORT))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

poll_timeout = True
poll_interval_ms = 50 #50
poll_interval = float(poll_interval_ms) / 1000
poll_thread_exists = False
poll_latency_millis = 0

first_connect = 1
connect = 0
disconnect = 0
connected = 0
aux_lock = 0
aux = 0
poll = 0
laser = 0
actuator = 0
brake = 0
inplace = 0

refresh_rate = 1.0 / 25

cq = Queue.Queue()


def isValidChecksum( recieved ):
    byteArr = bytearray( recieved )
    #Check the checksum
    checksum = 0
    #print sys.getsizeof(byteArr)
    for x in range(0, 8) :
        #print x
        if((x!=0) and (x!=7)):
            checksum = byteArr[ x ] +  checksum
    print str(checksum)
    return( ( checksum & 0x0F ) == ( ( byteArr[7] & 0xF0 ) >> 4 ) ) 
    
def isValidPKT( recieved ):
    #Check the checksum
    checksum = 0
    Rchecksum = 0
    byteArr = bytearray( recieved )
    #print str(byteArr[0])
    if( len(byteArr) > 7 ):
        temp = byteArr[0]
        #print temp
        if (((temp >> 4) ^ 0xFF) == 0xFF):
            #print temp
            for x in range(1,8):
                #print byteArr[x],
                #print " ",
                if( x!=7 ):
                    checksum += byteArr[x]
            #print (checksum)
            if ( ( checksum & 0x0F ) == ( ( byteArr[7] & 0xF0 ) >> 4 ) ):
                #print "true"
                return True
            else:
                #print "Checksum Failed"
                #print str( ( ( byteArr[7] - 48) & 0xF0 ) >> 4 )
                return False
        else:                
            return False
    else:
        return 
        
def poll_thread():
    global poll_timeout   
    global sense_aux0
    global sense_aux1
    global sense_fwd
    global sense_left
    global sense_right
    global sense_batt
    global sense_gpio
    global poll_interval
    global poll_thread_exists
    global poll_latency_millis
    global flush_receive_buffer
    
    while connect == 1:
        #print "connect"
        try: 
            if poll == 1:
                print "poll"
                poll_time = current_milli_time()
                ready = select.select([s], [], [], 1)
                if ready[0]:
                    #print "data"
                    unpacker = struct.Struct('1s 1s 1s 1s 1s 1s 1s 1s')
                    data = s.recv( unpacker.size )
                    unpacked_data = unpacker.unpack(data)
                    #print >>sys.stderr, 'received "%s"' % binascii.hexlify(data)
                    if len(data) == 8 and isValidPKT( unpacked_data ):
                        sense_aux0   = ord(data[1]) - 48 
                        sense_aux1   = ord(data[2]) - 48
                        sense_fwd    = ord(data[3]) - 48
                        sense_left   = ord(data[4]) - 48
                        sense_right  = ord(data[5]) - 48
                        sense_batt   = ord(data[6]) - 48
                        poll_timeout = False;
                    else:
                        poll_timeout = True
                else:
                    poll_timeout = True
                poll_latency_millis = current_milli_time()

            time.sleep(poll_interval)
        except:
            e = sus.exc_info()[0]
            print e.strerror
        
    poll_timeout = True
    poll_thread_exists = False
    
def client_thread():
    global connect
    global disconect
    global connected
    global s
    global poll_thread_exists

    try:
        # Create a socket (SOCK_STREAM means a TCP socket)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        s.connect((HOST, PORT))

        s.setblocking(0)

        if poll_thread_exists == False:
            poll_thread_exists = True
            threading.Thread(target=poll_thread).start()
        connected = 1

        while connect == 1:
            print "connected"
            try:
                if cq.qsize() > 0:
                    #print ("Sending " + str(cq.qsize()) + "bytes...")
                    while cq.qsize() > 0:
                        s.send(cq.get())
                cq.put('\x04')
                cq.put('\x0F')
                cq.put('\x0F')
                cq.put('\x00')
                cq.put('\x00')
                cq.put('\xEF')
            except socket.error as e:
                print e.strerror
                print "Error in socket: restarting sending"
                #print "ERROR HELP"
                #connect = 0
                #connected = 0
                cq.queue.clear()
            except: 
                e = sus.exc_info()[0]
                print e.strerror
                connect = 0
                connected = 0

            if disconnect == 1:
                dissconnect = 0
                connect = 0
                connected = 0

            time.sleep(poll_interval_ms) #.5

        cq.queue.clear()        
        s.close()
        print "Socket exiting"
        
    except socket.error as e:
        print e.strerror
        connect = 0
        connected = 0;
        cq.queue.clear()
    

#threading.Thread(target=update_screen).start()
set_act = False
motion = 0
try:
    while running == True:

        set_act = False
        cq.put('\x00')
        if first_connect == 1:
            print "First Connect"
            connect = 1
            poll = 1
            threading.Thread(target=client_thread).start()
            first_connect = 0
        
       # if event.type == QUIT:
       #     connect = 0
       #     running = False
except KeyboardInterrupt:
    running = False
    disconnect = 1