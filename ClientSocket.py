import pygame
import sys
import socket
import threading
import Queue
import time
import struct
import select
import binascii

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

print "Driving Application"
print "Version 0.5"
print "License: the author hereby waives ALL claim of copyright in this work"
print ""

platform_windows = False
left = 0
right = 0
left_dir = 0
right_dir = 0
old_left_packed = 0
old_right_packed = 0
rev_limit = 15;
x_rev_limit = 4;
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

flush_receive_buffer = False
controller_detected = False

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

axis_0 = 0
axis_2 = -1
axis_5 = -1

sense_aux0 = 0
sense_aux1 = 0
sense_fwd = 255
sense_left_range = 178
sense_right_range = 178
sense_left = sense_left_range
sense_right = sense_right_range
sense_batt = 0
sense_gpio = 0

poll_timeout = True
poll_interval_ms = 50
poll_interval = float(poll_interval_ms) / 1000
poll_thread_exists = False
poll_latency_millis = 0

refresh_rate = 1.0 / 25

cq = Queue.Queue()

pygame.init()

screen = pygame.display.set_mode((500, 280))
pygame.display.set_caption('Merc bot 2015');
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
            print temp
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
        return False

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
        if poll == 1:
            print ""
            poll_time = current_milli_time()
            ready = select.select([s], [], [], 1)
            if ready[0]:
                #print "data"
                unpacker = struct.Struct('1s 1s 1s 1s 1s 1s 1s 1s')
                data = s.recv( unpacker.size )
                unpacked_data = unpacker.unpack(data)
                print >>sys.stderr, 'received "%s"' % binascii.hexlify(data)
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
            #print "connected"
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
    batt_display_min = 120
    batt_display_max = 170
    batt_range = batt_display_max - batt_display_min
    batt_warning_cutoff = float(141 - batt_display_min) / batt_range * 300
    batt_max_cutoff = float(154 - batt_display_min) / batt_range * 300
    global sense_left_range
    global sense_right_range

    color_off = pygame.Color(45, 45, 45)
    color_blue = pygame.Color(0, 0, 255)
    color_green = pygame.Color(0, 255, 0)
    color_white = pygame.Color(255, 255, 255)

    while running == True:
        background.fill((0, 0, 0))
        #text = myfont.render(str(int(left)) + " : " + str(int(right)), True, (65, 65, 65))
        #background.blit(text, (5,290))

        if connect == 0:
            text = myfont.render(str(ip) + ":" + str(port), True, (65, 65, 65))
        else:
            text = myfont.render(str(ip) + ":" + str(port), True, (255, 255, 255))
    
        textpos = text.get_rect()
        #background.blit(text, ((490-textpos.w), 10))
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
            screen.blit(img_title, pos)    
        else:
            screen.blit(img_title_on, pos)    

        pos = img_lights.get_rect()
        pos.centerx = 98 / 2
        pos.y = stat_pos_y
        if aux == 1 or aux_lock == 1:
            if aux_lock == 0:
                screen.blit(img_lights, pos)
            else:
                screen.blit(img_lights_lock, pos)
        else:
            screen.blit(img_lights_off, pos)

        pos = img_actuator.get_rect()
        pos.x = 98 / 2 - 5 - pos.w
        pos.y = stat_pos_y+35
        if actuator == 1:
            screen.blit(img_actuator, pos)
        else:
            screen.blit(img_actuator_off, pos)

        pos = img_laser.get_rect()
        pos.x = 98 / 2 + 5
        pos.y = stat_pos_y+35
        if laser == 1:
            screen.blit(img_laser, pos)
        else:
            screen.blit(img_laser_off, pos)

        pos = img_poll.get_rect()
        pos.x = 412+img_brake.get_rect().w+10
        pos.y = stat_pos_y
        if poll == 1:
            if poll_timeout == False:
                screen.blit(img_poll, pos)
            else:
                screen.blit(img_poll_timeout, pos)
        else:
            screen.blit(img_poll_off, pos)

        pos = img_brake.get_rect()
        pos.x = 412
        pos.y = stat_pos_y
        if brake == 1:
            screen.blit(img_brake, pos)
        else:
            screen.blit(img_brake_off, pos)

        if connect == 1 and brake == 0:
            curcolor = pygame.Color(185, 185, 185)
        else:
            curcolor = color_off

        posL = img_left_off.get_rect()
        posL.x = 98-5-posL.w
        posL.y = motorL_pos_y
        posR = img_left_off.get_rect()
        posR.x = 402+5
        posR.y = posL.y

        if inplace == 1:
            if left_dir != right_dir:
                if left_dir == 2:
                    screen.blit(img_left_on, posL)
                    screen.blit(img_right_standby, posR)
                else:
                    screen.blit(img_left_standby, posL)
                    screen.blit(img_right_on, posR)
            else:
                screen.blit(img_left_standby, posL)
                screen.blit(img_right_standby, posR)
        else:
            screen.blit(img_left_off, posL)
            screen.blit(img_right_off, posR)

        for i in range(0, 14):
            if rev_limit > 0:
                if i >= rev_limit:
                    curcolor = color_off
                elif i == (rev_limit - 1):
                    curcolor = color_blue
            pygame.draw.rect(screen, curcolor, (120+i*20, motorL_pos_y-4, 2, 2), 0)
            pygame.draw.rect(screen, curcolor, (120+i*20, motorR_pos_y+7, 2, 2), 0)
            if i == (x_rev_limit - 1):
                pygame.draw.rect(screen, color_white, (120+i*20, motorL_pos_y-10, 2, 4), 0)
                pygame.draw.rect(screen, color_white, (120+i*20, motorR_pos_y+11, 2, 4), 0)

        if x_rev_limit == 15:
                pygame.draw.rect(screen, color_white, (120+14*20, motorL_pos_y-10, 2, 4), 0)
                pygame.draw.rect(screen, color_white, (120+14*20, motorR_pos_y+11, 2, 4), 0)

        pygame.draw.rect(screen, (0, 0, 255), (98, motorL_pos_y, 2, 5), 0)
        pygame.draw.rect(screen, (0, 0, 255), (98, motorR_pos_y, 2, 5), 0)

        if rev_limit == 15:
            curcolor = color_blue
        else:
            curcolor = color_off        

        pygame.draw.rect(screen, curcolor, (400, motorL_pos_y, 2, 5), 0)
        pygame.draw.rect(screen, curcolor, (400, motorR_pos_y, 2, 5), 0)

        if connect == 1:
            curcolor = color_blue
        else:
            curcolor = color_off

        pygame.draw.rect(screen, curcolor, (98, sensor_display_y+199, 2, 5), 0)
        pygame.draw.rect(screen, curcolor, (400, sensor_display_y+199, 2, 5), 0)

    
        #pygame.draw.lines(screen, (0, 0, 255), False, ((128, 200),(128, 265)), 2)
        #pygame.draw.lines(screen, (0, 0, 255), False, ((371, 200),(371, 265)), 2)
        #pygame.draw.lines(screen, (0, 0, 255), False, ((225, 103),(275, 103)), 2)
        #pygame.draw.rect(screen, (45, 45, 45), (100, 304, 300, 5), 0)
        pygame.draw.lines(screen, (0, 0, 255), False, ((128, sensor_display_y+95),(128, sensor_display_y+160)), 2)
        pygame.draw.lines(screen, (0, 0, 255), False, ((371, sensor_display_y+95),(371, sensor_display_y+160)), 2)
        pygame.draw.lines(screen, (0, 0, 255), False, ((225, sensor_display_y-2),(275, sensor_display_y-2)), 2)
        pygame.draw.rect(screen, (45, 45, 45), (100, sensor_display_y+199, 300, 5), 0)

        img_bat_pos = img_batt.get_rect()

        if connected == 1:
            left_offset = 0
            right_offset = 0
            if sense_left > sense_left_range:
                left_offset = 90;
            else:
                left_offset = (float(sense_left) / sense_left_range) * 90

            if sense_right > sense_right_range:
                right_offset = 90;
            else:
                right_offset = (float(sense_right) / sense_right_range) * 90

            leftX = 130 + left_offset
            rightX = 370 - right_offset
            sense_fwd_adj = sense_fwd
            if sense_fwd_adj > 55:
                sense_fwd_adj = 55
            fwdY = sensor_display_y + float(55 - sense_fwd_adj) / 55 * 90
            battV = sense_batt
            battVolts = round(float(sense_batt) / 255 * 10, 1)
            if sense_batt > batt_display_max:
                battV = batt_display_max
            elif sense_batt < batt_display_min:
                battV = batt_display_min
            battX = float(battV - batt_display_min) / batt_range * 300
            screen.blit(img_bot_on, (225, sensor_display_y+95))

            if actuator == 0:
                screen.blit(img_act_set_disengaged, (20, 140))
            else:
                if actuator_setting == 0:
                    screen.blit(img_act_set_0, (20, 140))
                elif actuator_setting == 1:
                    screen.blit(img_act_set_1, (20, 140))
                elif actuator_setting == 2:
                    screen.blit(img_act_set_2, (20, 140))
                elif actuator_setting == 3:
                    screen.blit(img_act_set_3, (20, 140))
                elif actuator_setting == 4:
                    screen.blit(img_act_set_4, (20, 140))
                elif actuator_setting == 5:
                    screen.blit(img_act_set_5, (20, 140))
                elif actuator_setting == 6:
                    screen.blit(img_act_set_6, (20, 140))

            if poll_timeout == False and poll == 1:
                pygame.draw.rect(screen, (0, 255, 0), (100, sensor_display_y+199, battX, 5), 0)
                pygame.draw.rect(screen, (255, 0, 0), (100+batt_warning_cutoff, sensor_display_y+199, 2, 5), 0)
                pygame.draw.rect(screen, (255, 180, 0), (100+batt_max_cutoff, sensor_display_y+199, 2, 5), 0)
                if poll == 1 and poll_timeout == False:
                    curcolor = color_green;
                else:
                    curcolor = color_off;
                pygame.draw.lines(screen, curcolor, False, ((leftX, sensor_display_y+95),(leftX, sensor_display_y+160)), 2)
                pygame.draw.lines(screen, curcolor, False, ((rightX, sensor_display_y+95),(rightX, sensor_display_y+160)), 2)
                pygame.draw.lines(screen, curcolor, False, ((225, fwdY),(275, fwdY)), 2)
                
                if sense_fwd < 4:
                    fwd_dist = 0;
                else:
                    fwd_dist = round(5 + float(sense_fwd) * 5, 1)

                if fwd_dist >= 24:
                    text = myfont.render(str(fwd_dist) + " cm", True, (255, 255, 255))
                else:
                    text = myfont.render("<15 cm", True, (255, 255, 255))
                textpos = text.get_rect()
                textpos.centerx = background.get_rect().centerx
                textpos.y = sensor_display_y - 5 - textpos.h
                screen.blit(text, textpos)
                text = myfont.render(str(battVolts) + " V", True, (255, 255, 255))
                textpos = text.get_rect()
                screen.blit(text, (400-textpos.w, sensor_display_y+175))
                if sense_batt < 141:
                    screen.blit(img_batt, (430-img_bat_pos.w, sensor_display_y+180))
                else:
                    screen.blit(img_batt_off, (430-img_bat_pos.w, sensor_display_y+180))
                if sense_aux0 < 128:
                    #pygame.draw.lines(screen, (255, 0, 0), False, ((128, 200),(128, 265)), 2)
                    pygame.draw.lines(screen, (255, 0, 0), False, ((128, sensor_display_y+95),(128, sensor_display_y+160)), 2)
                if sense_aux1 < 128:
                    #pygame.draw.lines(screen, (255, 0, 0), False, ((371, 200),(371, 265)), 2)
                    pygame.draw.lines(screen, (255, 0, 0), False, ((371, sensor_display_y+95),(371, sensor_display_y+160)), 2)
                if sense_gpio == 0:
                    pygame.draw.lines(screen, (255, 0, 0), False, ((225, sensor_display_y-2),(275, sensor_display_y-2)), 2)

            else:
                screen.blit(img_batt_off, (430-img_bat_pos.w, sensor_display_y+180))

        elif connect == 1:
            screen.blit(img_bot_connecting, (225, sensor_display_y+95))
            screen.blit(img_batt_off, (430-img_bat_pos.w, sensor_display_y+180))

        else:
            screen.blit(img_bot_off, (225, sensor_display_y+95))
            screen.blit(img_batt_off, (430-img_bat_pos.w, sensor_display_y+180))
            screen.blit(img_act_set_off, (20, 140))

        if left_dir == 1:
            pygame.draw.rect(screen, (0, 255, 0), (100, motorL_pos_y, float(left) / 15 * 300, 5), 0)
        if left_dir == 2:
            pygame.draw.rect(screen, (255, 0, 0), (100, motorL_pos_y, float(left) / 15 * 300, 5), 0)
    
        if right_dir == 1:
            pygame.draw.rect(screen, (0, 255, 0), (100, motorR_pos_y, float(right) / 15 * 300, 5), 0)
        if right_dir == 2:
            pygame.draw.rect(screen, (255, 0, 0), (100, motorR_pos_y, float(right) / 15 * 300, 5), 0)

        for i in range(0, 14):
            pygame.draw.rect(screen, (0, 0, 0), (120+20*i, motorL_pos_y, 2, 12), 0)

        if first_connect == 0:
            text = bigfont.render("WIGGLE AXES BEFORE CONNECTING", 1, (255, 255, 255))
            textpos = text.get_rect()
            textpos.centerx = background.get_rect().centerx
            textpos.centery = 150
            screen.blit(text, textpos)
    
        pygame.display.flip()
        time.sleep(refresh_rate)

def calc_motor_vals():
    global left
    global right
    global left_dir
    global right_dir
    global old_left_packed
    global old_right_packed
    global rev_limit
    global x_rev_limit
    left = 0
    right = 0
    magnitude = 0
    left_dir = 0
    right_dir = 0

    if not platform_windows:
        axis_5_pos = axis_5 + 1;
        axis_2_pos = axis_2 + 1;
    else:
        axis_2_pos = abs(axis_2)

    if not platform_windows and axis_5_pos > TRIGGER_DEADBAND:
        magnitude = (axis_5_pos-TRIGGER_DEADBAND)/(2-TRIGGER_DEADBAND) * MAX_VAL;
        left_dir = 1
        right_dir = 1

    elif axis_2_pos > TRIGGER_DEADBAND:
        if not platform_windows:
            magnitude = (axis_2_pos-TRIGGER_DEADBAND)/(2-TRIGGER_DEADBAND) * MAX_VAL;
        else:
            magnitude = (axis_2_pos-TRIGGER_DEADBAND)/(1-TRIGGER_DEADBAND) * MAX_VAL;

        if not platform_windows or (platform_windows and axis_2 > 0):
            left_dir = 2
            right_dir = 2
        else:
            left_dir = 1
            right_dir = 1

    rescale = (abs(axis_0)-DEADBAND)/(1-DEADBAND)
    if axis_0 < (-1 * DEADBAND):
        if magnitude == 0 and inplace == 1:
            left_dir = 2
            right_dir = 1
            left = rescale * MAX_VAL
            right = rescale * MAX_VAL
        else:
            left = (1-rescale) * magnitude
            right = magnitude
    elif axis_0 > DEADBAND:
        if magnitude == 0 and inplace == 1:
            left_dir = 1
            right_dir = 2
            left = (abs(axis_0)-DEADBAND)/(1-DEADBAND) * MAX_VAL
            right = (abs(axis_0)-DEADBAND)/(1-DEADBAND) * MAX_VAL
        else:
            right = (1-rescale) * magnitude
            left = magnitude
    else:
        right = magnitude
        left = magnitude

    left = round(left, 0)
    right = round(right, 0)
    if left > 15:
        left = 15
    if right > 15:
        right = 15

    if rev_limit > 0:
        if left > rev_limit:
            left = rev_limit
        if right > rev_limit:
            right = rev_limit

    if inplace == 1: # and left_dir == right_dir:
        if left > x_rev_limit:
            left = x_rev_limit 
        if right > x_rev_limit:
            right = x_rev_limit

    left_packed = struct.pack('B', int(left) | 0x80 | int(left_dir) << 4)
    right_packed = struct.pack('B', int(right) | 0xC0 | int(right_dir) << 4)

    if connect == 1 and brake == 0:
        if left_packed != old_left_packed or right_packed != old_right_packed:
            cq.put(left_packed)
            cq.put(right_packed)

    old_left_packed = left_packed
    old_right_packed = right_packed
        
threading.Thread(target=update_screen).start()
set_act = False
motion = 0
while running == True:
    set_act = False
    event = pygame.event.wait()
    cq.put('\x00')
    if event.type == QUIT:
        pygame.quit()
        connect = 0
        running = False

    elif event.type == JOYAXISMOTION:
        print event.type

        axis_0 = controller.get_axis(0)
        axis_2 = controller.get_axis(2)

        if not platform_windows:
            axis_5 = controller.get_axis(5)

        if brake == 1:
            left = 0
            right = 0
            left_dir = 0
            right_dir = 0

        elif not platform_windows:
            if axis_0 != old_axis_0 or axis_2 != old_axis_2 or axis_5 != old_axis_5:
                calc_motor_vals()

        elif platform_windows:
            if axis_0 != old_axis_0 or axis_2 != old_axis_2:
                calc_motor_vals()

        old_axis_0 = axis_0
        old_axis_2 = axis_2

        if not platform_windows:
            old_axis_5 = axis_5

    elif event.type == JOYBUTTONDOWN:
        it = 0
        for i in range(0, controller.get_numbuttons()):
            pressed_buttons_array[it] = controller.get_button(i)
            if pressed_buttons_array[it] != released_buttons_array[it]:
                if it == 5:
                    if inplace == 0 and connect == 1 and aux_lock == 0:
                        aux = 1
                        cq.put('2')
                    elif inplace == 1:
                        if x_rev_limit < 15:
                            x_rev_limit = x_rev_limit + 1;
                elif it == 4:
                    if inplace == 0 and connect == 1:
                        aux_lock ^= 1
                        if aux_lock == 1 and connect == 1:
                            cq.put('2')
                        elif connect == 1:
                            cq.put('3')
                        if aux_lock == 0:
                            aux = 0
                    elif inplace == 1:
                        if x_rev_limit > 1:
                            x_rev_limit = x_rev_limit - 1;
                elif it == 1:
                    brake ^= 1
                    if brake == 1 and connect == 1:
                        cq.put('1')
                    elif connect == 1:
                        cq.put('0')
                elif it == 0:
                    if inplace == 0:
                        poll ^= 1
                        if poll == 0:
                            sense_aux0 = 0
                            sense_aux1 = 0    
                            sense_fwd = 255
                            sense_left = sense_left_range
                            sense_right = sense_right_range
                            sense_batt = 0
                    else:
                        flush_receive_buffer = True;
                    
                elif it == 2:
                    inplace = 1
                elif it == 3 and connect == 1:
                    laser ^= 1;
                    if laser == 1 and connect == 1:
                        cq.put('6')
                        cq.put('[')
                    elif connect == 1:
                        cq.put('7')
                        cq.put(']')
                elif it == 6 and connect == 1:
                    actuator ^= 1
                    if actuator == 1 and connect == 1:
                        cq.put('4')
                    elif connect == 1:
                        cq.put('5')

                # Reset the robot to a known state on connection and disconnect
                elif it == 7 and connect == 0:
                    print ("Initiating DRAGON CONNECTION")
                    connect = 1
                    first_connect = 1
                    brake = 1
                    cq.put('5')
                    cq.put('3')
                    cq.put('7')
                    cq.put(']')
                    cq.put('1')
                    cq.put('a')
                    threading.Thread(target=client_thread).start()
                elif it == 7 and connect == 1:
                    cq.put('5')
                    cq.put('3')
                    cq.put('7')
                    cq.put(']')
                    cq.put('1')
                    cq.put('a')
                    cq.put('q')
                    disconnect = 1
                    brake = 1
                    actuator = 0
                    actuator_setting = 0
                    laser = 0
                    aux = 0
                    aux_lock = 0
                elif not platform_windows and it == 10 and connect == 1 and actuator == 1:
                    set_act = True
                    if actuator_setting < 6:
                        actuator_setting = actuator_setting + 1
                elif it == 9 and connect == 1 and actuator == 1:
                    set_act = True
                    if not platform_windows and actuator_setting > 0:
                        actuator_setting = actuator_setting - 1
                    if platform_windows and actuator_setting < 6:
                        actuator_setting = actuator_setting + 1
                        
                elif platform_windows and it == 8:
                    set_act = True
                    if actuator_setting > 0:
                        actuator_setting = actuator_setting - 1;
            it+=1
        
    elif event.type == JOYBUTTONUP:
        it = 0
        for i in range(0, controller.get_numbuttons()):
            released_buttons_array[it] = controller.get_button(i)
            if pressed_buttons_array[it] != released_buttons_array[it]:
                if it == 5 and aux_lock != 1 and inplace == 0:
                    aux = 0
                    if connect == 1:
                        cq.put('3')
                elif it == 2:
                    inplace = 0
            it+=1

        if brake == 1:
            left = 0
            right = 0
            left_dir = 0
            right_dir = 0

    ### KEYBOARD CONTROL ###

    elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_q:
            connect = 0
            running = False
            pygame.quit()

        elif event.key == pygame.K_f:
            flush_receive_buffer = True

        elif event.key == pygame.K_c:
            if connect == 0:    
                print ("Initiating DRAGON CONNECTION")
                connect = 1
                first_connect = 1
                brake = 1
                cq.put('0')
                #cq.put('3')
                #cq.put('7')
                #cq.put(']')
                #cq.put('1')
                #cq.put('a')
                threading.Thread(target=client_thread).start()
            else:
                #cq.put('5')
                #cq.put('3')
                #cq.put('7')
                #cq.put(']')
                #cq.put('1')
                #cq.put('a')
                #cq.put('q')
                disconnect = 1
                brake = 1
                actuator = 0
                actuator_setting = 0
                laser = 0
                aux = 0
                aux_lock = 0

        elif event.key == pygame.K_p:
            poll ^= 1
            if poll == 0:
                sense_aux0 = 0
                sense_aux1 = 0    
                sense_fwd = 255
                sense_left = sense_left_range
                sense_right = sense_right_range
                sense_batt = 0
                sense_gpio = 1

        elif event.key == pygame.K_b:
            brake ^= 1
            if brake == 1 and connect == 1:
                connect = 1
            elif connect == 1:
                connect = 1
                #cq.put('0')

        elif event.key == pygame.K_o:
            actuator ^= 1
            if actuator == 1 and connect == 1:
                #cq.put('4')
                connect = 1
            elif connect == 1:
                #cq.put('5')
                connect = 1

        elif event.key == pygame.K_l:
            aux_lock ^= 1
            if aux_lock == 1 and connect == 1:
                #cq.put('2')
                connect = 1
            elif connect == 1:
                #cq.put('3')
                connect = 1
            if aux_lock == 0:
                aux = 0

        elif event.key == pygame.K_w and motion == 0:
            motion = 1
            #cq.put(struct.pack('B', 0xCF))
            #cq.put(struct.pack('B', 0x8F))
            left = 15
            right = 15
            left_dir = 1
            right_dir = 1
        elif event.key == pygame.K_s and motion == 0:
            motion = 2
            #cq.put(struct.pack('B', 0xEF))
            #cq.put(struct.pack('B', 0xAF))
            left = 15
            right = 15
            left_dir = 2
            right_dir = 2
        elif event.key == pygame.K_a and motion == 0:
            motion = 3
            #cq.put(struct.pack('B', 0xCF))
            #cq.put(struct.pack('B', 0xAF))
            left = 15
            right = 15
            left_dir = 2
            right_dir = 1
        elif event.key == pygame.K_d and motion == 0:
            motion = 4
            #cq.put(struct.pack('B', 0xEF))
            #cq.put(struct.pack('B', 0x8F))
            left = 15
            right = 15
            left_dir = 1
            right_dir = 2
            
        elif event.key == pygame.K_LEFT:
            if rev_limit > 1:
                rev_limit -= 1
        elif event.key == pygame.K_RIGHT:
            if rev_limit < 15:
                rev_limit += 1
        elif event.key == pygame.K_UP:
            if poll_interval_ms < 100:
                poll_interval_ms += 10
            else:
                poll_interval_ms += 50
            poll_interval = float(poll_interval_ms) / 1000
        elif event.key == pygame.K_DOWN:
            if poll_interval_ms > 50:
                if poll_interval_ms > 100:
                    poll_interval_ms -= 50
                else:
                    poll_interval_ms -= 10
            poll_interval = float(poll_interval_ms) / 1000
        elif event.key == pygame.K_0:
            actuator_setting = 0
            #cq.put('a')
        elif event.key == pygame.K_1:
            actuator_setting = 1
            #cq.put('s')
        elif event.key == pygame.K_2:
            actuator_setting = 2
            #cq.put('d')
        elif event.key == pygame.K_3:
            actuator_setting = 3
            #cq.put('f')
        elif event.key == pygame.K_4:
            actuator_setting = 4
            #cq.put('g')
        elif event.key == pygame.K_5:
            actuator_setting = 5
            #cq.put('h')
        elif event.key == pygame.K_6:
            actuator_setting = 6
            #cq.put('j')


    elif event.type == pygame.KEYUP:
        if motion == 1 and pygame.K_w:
            print "up released"
            motion = 0
            #cq.put(struct.pack('B', 0xC0))
            #cq.put(struct.pack('B', 0x80))
            left = 0
            right = 0
        elif motion == 2 and pygame.K_s:
            print "down released"
            motion = 0
            #cq.put(struct.pack('B', 0xC0))
            #cq.put(struct.pack('B', 0x80))
            left = 0
            right = 0
        elif motion == 3 and pygame.K_a:
            print "left released"
            motion = 0
            #cq.put(struct.pack('B', 0xC0))
            #cq.put(struct.pack('B', 0x80))
            left = 0
            right = 0
        elif motion == 4 and pygame.K_d:
            print "right released"
            motion = 0
            #cq.put(struct.pack('B', 0xC0))
            #cq.put(struct.pack('B', 0x80))
            left = 0
            right = 0

    # if set_act == True:
        # if actuator_setting == 0:
            # #cq.put('a')
        # elif actuator_setting == 1:
            # #cq.put('s')
        # elif actuator_setting == 2:
            # #cq.put('d')
        # elif actuator_setting == 3:
            # #cq.put('f')
        # elif actuator_setting == 4:
            # #cq.put('g')
        # elif actuator_setting == 5:
            # #cq.put('h')
        # elif actuator_setting == 6:
            # #cq.put('j')
