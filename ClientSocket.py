import pygame
import sys
import socket
import threading
import Queue
import time
import struct
import select
from pygame.locals import *

HOST, PORT = "localhost", 9999
data = '\x04\x0F\x0F\x00\x00\xEF'
#data = 'aabbccdd'


# Create function get get time from
current_milli_time = lambda: int(round(time.time() * 1000))
timer = 0

DEADBAND = 0.18
TRIGGER_DEADBAND = 0.15
MAX_VAL = 16 

left = 0
right = 0
left_dir = 0
right_dir = 0
old_left_packed = 0
old_right_packed = 0
rev_limit = 15;
x_rev_limit = 7;
actuator_setting = 0;

first_connect = 0
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

running = True

img_brake = pygame.image.load("art/brake.png")
img_brake_off = pygame.image.load("art/brake-off.png")
img_lights = pygame.image.load("art/lights.png")
img_lights_off = pygame.image.load("art/lights-off.png")
img_lights_lock = pygame.image.load("art/lights-lock.png")
img_actuator = pygame.image.load("art/actuator.png")
img_actuator_off = pygame.image.load("art/actuator-off.png")
img_laser = pygame.image.load("art/laser.png")
img_laser_off = pygame.image.load("art/laser-off.png")
img_batt = pygame.image.load("art/batt.png")
img_batt_off = pygame.image.load("art/batt-off.png")
img_poll = pygame.image.load("art/poll.png")
img_poll_off = pygame.image.load("art/poll-off.png")
img_poll_timeout = pygame.image.load("art/poll-timeout.png")
img_bot_off = pygame.image.load("art/bot-off.png")
img_bot_on = pygame.image.load("art/bot-on.png")
img_bot_connecting = pygame.image.load("art/bot-error.png")
img_title = pygame.image.load("art/title.png")
img_title_on = pygame.image.load("art/title-on.png")

img_left_off = pygame.image.load("art/left-off.png")
img_left_on = pygame.image.load("art/left-on.png")
img_left_standby = pygame.image.load("art/left-standby.png")
img_right_off = pygame.image.load("art/right-off.png")
img_right_on = pygame.image.load("art/right-on.png")
img_right_standby = pygame.image.load("art/right-standby.png")

img_act_set_off = pygame.image.load("art/act-set-off.png")
img_act_set_disengaged = pygame.image.load("art/act-set-disengaged.png")
img_act_set_0 = pygame.image.load("art/act-set-0.png")
img_act_set_1 = pygame.image.load("art/act-set-1.png")
img_act_set_2 = pygame.image.load("art/act-set-2.png")
img_act_set_3 = pygame.image.load("art/act-set-3.png")
img_act_set_4 = pygame.image.load("art/act-set-4.png")
img_act_set_5 = pygame.image.load("art/act-set-5.png")
img_act_set_6 = pygame.image.load("art/act-set-6.png")

sense_1 = 0
sense_2 = 0
sense_3 = 255
sense_4 = 178
sense_volt = 0
sense_amp = 0

poll_timeout = True
poll_interval_ms = 50
poll_interval = float(poll_interval_ms) / 1000
poll_thread_exists = False
poll_latency_millis = 0

refresh_rate = 1.0 / 25

cq = Queue.Queue()

pygame.init()

screen = pygame.display.set_mode((500, 280))
pygame.display.set_caption('Mercury 2014')
myfont = pygame.font.SysFont("sans", 12)
bigfont = pygame.font.SysFont("Monospace", 25)

background = pygame.Surface(screen.get_size())
background = background.convert()

font = pygame.font.Font(None, 36)

old_axis_0 = 0
old_axis_2 = 0
old_axis_5 = 0

pressed_buttons_array = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
released_buttons_array = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

ip = sys.argv[1]
port = sys.argv[2]

print ("IP to connect to: " + str(ip))
print ("Port:             " + str(port))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def isValidChecksum( recieved ):
    byteArr = bytearray( received )
    #Check the checksum
    checksum = 0
    print sys.getsizeof(byteArr)
    for x in range(0, 8) :
        #print x
        if((x!=0) and (x!=7)):
            checksum = byteArr[ x ] +  checksum
    return( ( checksum & 0x0F ) == ( ( byteArr[7] & 0xF0 ) >> 4 ) ) 

def poll():

    global poll_timeout
    global sense_1
    global sense_2
    global sense_3
    global sense_4
    global sense_volt
    global sense_amp
    global poll_interval
    global poll_thread_exists
    global poll_latency_millis
    
    while connected:
        if poll:
            poll_time = current_milli_time()
            #cq.put('p')
            ready = select.select([s], [], [], 1)
            if ready:
                data = s.recv( 8 );
                if len(data) == 8 and isValidChecksum( data ):
                    sense_1 = org(data[1]);
                    sense_2 = org(data[2]);
                    sense_3 = org(data[3]);
                    sense_4 = org(data[4]);
                    sense_volt = org(data[5]);
                    sense_amp  = org(data[6]);
                    poll_timeout = False;
                else:
                    poll_timeout = True
            else:
                poll_timeout = True
            poll_latency_millis = current_milli_time()

        time.sleep(poll_interval)
        
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
            threading.Thread(target=poll).start()
        connected = 1

        while connect == 1:
            try:
                if cq.qsize() > 0:
                    print ("Sending " + str(cq.qsize()) + "bytes...")
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
                connect = 0
                connected = 0
                cq.queue.clear()

            if disconnect == 1:
                dissconnect = 0
                connect = 0
                connected = 0

            time.sleep(0.05)

        cq.queue.clear()        
        s.close()
        print "Socket exiting"
        
    except socket.error as e:
		print e.strerror
		connect = 0
		connected = 0;
		cq.queue.clear()
    
    
def update_screen():
    global poll_timeout
    global myfont
    stat_pos_y = 60
    motorL_pos_y = 15
    motorR_pos_y = 22
    sensor_display_y = 70
    volt_display_min = 120
    volt_display_max = 170
    amp_display_min = 120
    amp_display_max = 170
    volt_range = volt_display_max - volt_display_min
    volt_warning_cutoff = float(141 - volt_display_min) / volt_range * 300
    volt_max_cutoff = float(154 - volt_display_min) / volt_range * 300

    while running:
        background.fill((0,0,0))

        if connect == 0:
            text = myfont.render(str(ip) + ":" + str(port), True, (65,65,65))
        else:
            text = myfont.render(str(ip) + ":" + str(port), True, (255, 255, 255))

        textpos = text.get_rect()
        background.blit(text, (100, sensor_display_y+175))

        
        if poll_timeout == False:
            text = myfont.render(str(poll_latency_millis) + " ms", True, (255, 255, 255))
	else:
            text = myfont.render("No data", True, (255, 255, 255))

        textpos = text.get_rect()
	background.blit(text, ((490-textpos.w), stat_pos_y+30+textpos.h))

	text = myfont.render(str(poll_interval) + " s int.", True, (255, 255, 255))
        textpos = text.get_rect()
	background.blit(text, ((490-textpos.w), stat_pos_y+30))
	                                                                    
        screen.blit(background, (0,0))

	pos = img_title.get_rect()
	pos.y = 275 - pos.h
	pos.centerx = 49
	
	if connected == 0:
            #screen.blit(img_title, pos)	
		battV = 0
	else:
		battV = sense_volt
		battVolts = round(float(sense_volt) / 255 * 10, 1)
		if sense_volt > volt_display_max:
			battV = volt_display_max
		elif sense_volt < volt_display_min:
			battV = volt_display_min
		battX = float(battV - volt_display_min) / volt_range * 300
	
		if poll_timeout == False and poll == 1:
			if sense_volt < 141:
				screen.blit(img_batt, (430-img_bat_pos.w, sensor_display_y+180))
			else:
				screen.blit(img_batt_off, (430-img_bat_pos.w, sensor_display_y+180))
        
    pygame.display.flip()
    time.sleep(refresh_rate)

        
threading.Thread(target=update_screen).start()

print ("Initiating DRAGON CONNECTION")
connect = 1
first_connect = 1
cq.put('1')
threading.Thread(target=client_thread).start()
