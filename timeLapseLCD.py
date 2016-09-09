#!/usr/bin/env python3
import threading
import RPi.GPIO as GPIO
from time import sleep, monotonic as time
import RPLCD
from os import statvfs
from picamera import PiCamera
from sys import exit
import timeLapseMenu as lcdMenu

#-------------------------DIR-&-FREE-STORAGE----------------------
pictureDir = '/'
st = statvfs(pictureDir)
freeSpace =  st.f_bavail * st.f_frsize / 1024 / 1024 #in MB

#-------------------------GPIO-&-LCD------------------------
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
buttonEdge = GPIO.FALLING #FALLING: relase trigger, RISING: press trigger

debug = False #show pressed buttons

# Initialize display. All values have default values and are therefore
# optional.
lcd = RPLCD.CharLCD(pin_rs=7, pin_rw=None, pin_e=8, pins_data=[11, 24, 25, 4],
              numbering_mode=GPIO.BCM, cols=16, rows=2, dotsize=8)

#------------------------CAMERA---------------------------
#camera = PiCamera()
previewOnStartup = False
#if previewOnStartup: camera.start_preview()

#-----------------------TIMING--------------------------------
quitButtonPressTime = time()

#-----------------------MENU-----------------------------------
menuItems = ['    Duration   >', '<   Interval   >', '< save raw data>']
# name, [min, step, max, default/current]
menuChoices = [ ['hrs', [1,1,48,3]], ['sec', [0.5,0.5,60,1]], ['yes/no', [0,1,1,1]] ]
menu = lcdMenu.timeLapseMenu(menuItems, menuChoices,lcd)
 #0123456789abcdef0123456789abcdef
#'< save raw data>'
menu.home()

#--------------------INTERRUPTS (buttons)--------------------
def quitButton(channel):
    if GPIO.input(23):
        #pressed
        menu.goUp()
        global quitButtonPressTime
        quitButtonPressTime = time()
        if debug: print("Pressed at", quitButtonPressTime)
    else:
        #released
        if debug: print("Released")
        if quitButtonPressTime <= time() - 3: #at least 3 seconds helt before release
            exit()
        else:
            if debug: print("hold the button at least 2 seconds to quit the app")
            if debug: print("you pressed: ", time() - quitButtonPressTime)

def leftButton(channel):
    if debug: print('< button pressed')
    menu.goLeft()

def rightButton(channel):
    if debug: print('> button pressed')
    menu.goRight()

def downButton(channel):
    if debug: print('back button pressed')
    menu.goBack()

def enterButton(channel):
    if debug: print('enter button pressed')
    menu.goDown()

#Quit, Left, Right, Back, Enter Buttons
GPIO.setup([23,18,17,22,27], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.add_event_detect(23, GPIO.BOTH, callback=quitButton)
GPIO.add_event_detect(18, buttonEdge, callback=leftButton, bouncetime=300)
GPIO.add_event_detect(17, buttonEdge, callback=rightButton, bouncetime=300)
GPIO.add_event_detect(22, buttonEdge, callback=downButton, bouncetime=300)
GPIO.add_event_detect(27, buttonEdge, callback=enterButton, bouncetime=300)


try:
    print('Running...')
    while(1):
        sleep(60)
except (KeyboardInterrupt, SystemExit):
    lcd.clear()
    GPIO.cleanup()       # clean up GPIO on CTRL+C exit
#lcd.clear()
GPIO.cleanup()
