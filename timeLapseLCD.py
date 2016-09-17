#!/usr/bin/env python3
#minmum version: Python 3.4
import threading
import RPi.GPIO as GPIO
from time import sleep, monotonic as time
import RPLCD
from os import statvfs, listdir
from picamera import PiCamera
from sys import exit
import timeLapseMenu as lcdMenu
import string
import re


#-------------------------DIR-&-FREE-STORAGE----------------------
pictureDir = '/home/pi/Pictures/TimeLapse/'
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
camera = PiCamera()
previewOnStartup = True
if previewOnStartup == True: camera.start_preview()

#Camera Settings
pictureFormat = 'jpeg'
camera.resolution = (2592, 1944)

#-----------------------TIMING--------------------------------
quitButtonPressTime = time()
leftButtonPressTime = time()
leftButtonPressed = False
rightButtonPressTime = time()
rightButtonPressed = False

#-----------------------MENU-----------------------------------
def startTimeLapse(duration, interval, raw):
    amountOfPictures = int(duration * 60 * 60 / interval)
    if(raw):
        estSize = 10.0
    else:
        estSize = 4.5
    print('starting time-lapse')
    lcd.clear()
    lcd.write_string('Timelapsing\n\r'+ str(amountOfPictures) + ' ' +
    str(int(amountOfPictures * estSize/freeSpace*100))+ '% ' +
    str(round(amountOfPictures / 30,1)))
    camera.start_preview()
    prefix = findPossibleFilePrefix(pictureDir)
    if prefix == False :
        lcd.clear()
        lcd.write_string('ERROR: No possible prefix found')
        exit()
    fileName = prefix + '{0:0' + str(digits(amountOfPictures)) + 'd}.jpg'
    sleep(5)
    for pic in range(0,amountOfPictures):
        lcd.clear()
        lcd.write_string(str(pic + 1) + '/' + str(amountOfPictures) + ' ' + str(round(pic + 1 / amountOfPictures * 100,1)) + '%')
        lcd.write_string('\r\n' + str(int((amountOfPictures - pic + 1) * interval / 60))  + 'min ')
        camera.capture(pictureDir + fileName.format(pic), format=pictureFormat, bayer=raw)
        sleep(interval)
    lcd.clear()
    lcd.write_string('done.')
    exit()
menuItems = ['    Duration   >', '<   Interval   >', '< save raw data>', '< start lapse   ']
# unit, [min, step, max, default/current] (for float/int values)
# unit, [possibleString1, possibleString2, ...] (for string values)
# unit, [actionString, function] (for calling (a) function)
menuChoices = [ ['hrs', [1,1,48,1]], ['sec', [2,2,120,30]], ['', ['Yes','No', 0]], ['', ['I\'m ready', startTimeLapse]] ]
menu = lcdMenu.timeLapseMenu(menuItems, menuChoices,lcd)
 #0123456789abcdef0123456789abcdef
#
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
    global leftButtonPressTime, leftButtonPressed
    if GPIO.input(18):
        #pressed
        leftButtonPressed = True
        if debug: print('< button pressed')
        leftButtonPressTime = time()
        menu.goLeft()
    else:
        leftButtonPressed = False

def rightButton(channel):
    global rightButtonPressTime, rightButtonPressed
    if GPIO.input(17):
        #pressed
        rightButtonPressed = True
        if debug: print('> button pressed')
        rightButtonPressTime = time()
        menu.goRight()
    else:
        rightButtonPressed = False

def downButton(channel):
    if debug: print('back button pressed')
    menu.goBack()

def enterButton(channel):
    if debug: print('enter button pressed')
    menu.goDown()

#Quit, Left, Right, Back, Enter Buttons
GPIO.setup([23,18,17,22,27], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.add_event_detect(23, GPIO.BOTH, callback=quitButton)
GPIO.add_event_detect(18, GPIO.BOTH, callback=leftButton, bouncetime=300)
GPIO.add_event_detect(17, GPIO.BOTH, callback=rightButton, bouncetime=300)
GPIO.add_event_detect(22, buttonEdge, callback=downButton, bouncetime=300)
GPIO.add_event_detect(27, buttonEdge, callback=enterButton, bouncetime=300)

def digits(n):
    x = 0
    while n >= 10**x:
        x += 1
    return x

def findPossibleFilePrefix(filesdir):
    #put files in one string
    files = ''.join(item + ' ' for item in listdir(filesdir))
    #check allowed prefixes
    for i in range(0,len(string.ascii_letters)):
        prefix = string.ascii_letters[i]
        chexpression = re.compile(prefix + '\d*\.jpg')
        if chexpression.findall(files) == []:
            return prefix
    return False
try:
    print('Running...')
    findPossibleFilePrefix(pictureDir)
    #global leftButtonPressed, leftButtonPressTime
    while(1):
        if leftButtonPressed and time() - leftButtonPressTime >= 0.2:
            leftButton(True)
        if rightButtonPressed and time() - rightButtonPressTime >= 0.2:
            rightButton(True)
        sleep(0.1)
except (KeyboardInterrupt, SystemExit):
    lcd.clear()
    GPIO.cleanup()       # clean up GPIO on CTRL+C exit
#lcd.clear()
GPIO.cleanup()
