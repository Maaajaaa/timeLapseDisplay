#!/usr/bin/env python3
#minmum version: Python 3.4
import threading
import string
import re
from time import sleep, monotonic as time
from os import statvfs, listdir
from sys import exit

import Adafruit_SSD1306
import RPi.GPIO as GPIO
from picamera import PiCamera

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

import timeLapseMenu as lcdMenu


#-------------------------DIR-&-FREE-STORAGE----------------------
pictureDir = '/home/pi/Pictures/TimeLapse/'
st = statvfs(pictureDir)
freeSpace =  st.f_bavail * st.f_frsize / 1024 / 1024 #in MB

#---------------------------GPIO---------------------------
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
buttonEdge = GPIO.FALLING #FALLING: relase trigger, RISING: press trigger

debug = False #show pressed buttons

#------------------------------OLED-----------------------------

# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst = 24)

# Initialize display/library
disp.begin()
disp.display()

# Get display width and height
width = disp.width
height = disp.height

# Create image buffer (1-bit color)
image = Image.new('1', (width, height))

# Create drawing object.
draw = ImageDraw.Draw(image)

# Load font
fontPath = '/usr/share/fonts/truetype/gentium-basic/GenBasR.ttf'
font = ImageFont.truetype(fontPath, 15)

#image = Image.open('/home/pi/Adafruit_Python_SSD1306/examples/happycat_oled_64.ppm').convert('1')

def drawBuffer():
    # Draw the image buffer.
    disp.image(image)
    disp.display()

def clearBuffer():
    # Clear image buffer by drawing a black filled box.
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    nextX = [0,0]

def writeStringToBuffer(line, text):
    textWidth, textHeight = draw.textsize(text, font=font)
    draw.text((0, line * (textHeight + 2)), text, font=font, fill=255)

def clearDisplay():
    clearBuffer()
    drawBuffer()


#------------------------CAMERA---------------------------
camera = PiCamera()
previewOnStartup = False
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
    global font, draw
    amountOfPictures = int(duration * 60 * 60 / interval)
    if(raw):
        estSize = 10.0
    else:
        estSize = 4.5
    print('starting time-lapse')
    clearBuffer()
    writeStringToBuffer(0,'Timelapsing')
    writeStringToBuffer(1, str(amountOfPictures) + '\n, est. ' + str(int(amountOfPictures * estSize/freeSpace*100))+ '%')
    writeStringToBuffer(2, str(round(amountOfPictures / 30,1)) + ' mins@30fps')
    drawBuffer()
    camera.start_preview()
    prefix = findPossibleFilePrefix(pictureDir)
    if prefix == False:
        clearBuffer()
        writeStringToBuffer(0,'ERROR: No possible')
        writeStringToBuffer(1,'prefix found')
        drawBuffer()
        raise FileNotFoundError('No possible prefix found', 'in: ' + pictureDir)
    fileName = prefix + '{0:0' + str(digits(amountOfPictures)) + 'd}.jpg'
    #just for testing REḾOVE IT
    #----------------
    sleep(5)

    textWidth, textHeight = draw.textsize('0123456789', font=font)
    thirdLineY = 2 * (textHeight + 2)
    for pic in range(0,amountOfPictures):
        clearBuffer()
        writeStringToBuffer(0, str(pic + 1) + '/' + str(amountOfPictures) + ' ' + str(round(pic + 1 / amountOfPictures * 100,1)) + '%')
        writeStringToBuffer(1, str(int((amountOfPictures - pic + 1) * interval / 60))  + 'min left')
        drawBuffer()
        camera.capture(pictureDir + fileName.format(pic), format=pictureFormat, bayer=raw)
        for i in range(0,interval):
            sleep(1)
            draw.rectangle((0, thirdLineY, textWidth, thirdLineY+textHeight), fill=0)
            writeStringToBuffer(2, str(interval-i))
            drawBuffer()

    clearBuffer()
    font = ImageFont.truetype(fontPath, 50)
    writeStringToBuffer(0,'DONE.')
    font = ImageFont.truetype(fontPath, 15)
    drawBuffer()

    #should shut down when quit is helt
    while True:
        if GPIO.input(27):
            writeStringToBuffer(2.5,'shutting down.')
            drawBuffer()
            shutdown()

menuItems = ['Duration', 'Interval', 'save raw data', 'start lapse']
# unit, [min, step, max, default/current] (for float/int values)
# unit, [possibleString1, possibleString2, ...] (for string values)
# unit, [actionString, function] (for calling (a) function)
menuChoices = [ ['hrs', [1,1,48,1]], ['sec', [2,2,120,30]], ['', ['Yes','No', 0]], ['', ['I\'m ready', startTimeLapse]] ]
menu = lcdMenu.timeLapseMenu(menuItems, menuChoices, disp, draw, image, font)
menu.home()

#--------------------INTERRUPTS (buttons)--------------------
def quitButton(channel = False):
    if GPIO.input(27):
        #pressed
        global quitButtonPressTime
        quitButtonPressTime = time()
        if debug: print("QUIT Pressed at", quitButtonPressTime)
    else:
        #released
        if debug: print("QUIT Released")
        if quitButtonPressTime <= time() - 3: #at least 3 seconds helt before release
            #raise SystemExit
            print('Time to quit')
        else:
            if debug: print("hold the button at least 2 seconds to quit the app")
            if debug: print("you pressed: ", time() - quitButtonPressTime)

def leftButton(channel = False):
    global leftButtonPressTime, leftButtonPressed
    if GPIO.input(17):
        #pressed
        leftButtonPressed = True
        if debug: print('< button pressed')
        leftButtonPressTime = time()
        menu.goLeft()
    else:
        leftButtonPressed = False

def rightButton(channel = False):
    global rightButtonPressTime, rightButtonPressed
    if GPIO.input(23):
        #pressed
        rightButtonPressed = True
        if debug: print('> button pressed')
        rightButtonPressTime = time()
        menu.goRight()
    else:
        rightButtonPressed = False

def backButton(channel = False):
    if debug: print('back button pressed')
    menu.goUp()

def enterButton(channel = False):
    if debug: print('enter button pressed')
    menu.goDown()

def shutdown():
    command = "/usr/bin/sudo /sbin/shutdown -h now"
    import subprocess
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)

#Quit, Left, Right, Back, Enter Buttons
GPIO.setup([23,18,17,22,27], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.add_event_detect(27, GPIO.BOTH, callback=quitButton, bouncetime=300)
GPIO.add_event_detect(17, GPIO.BOTH, callback=leftButton, bouncetime=300)
GPIO.add_event_detect(23, GPIO.BOTH, callback=rightButton, bouncetime=300)
GPIO.add_event_detect(18, buttonEdge, callback=backButton, bouncetime=300)
GPIO.add_event_detect(22, buttonEdge, callback=enterButton, bouncetime=300)

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
    #global leftButtonPressed, leftButtonPressTime
    while(1):
        if leftButtonPressed and time() - leftButtonPressTime >= 0.2:
            leftButton()
        if rightButtonPressed and time() - rightButtonPressTime >= 0.2:
            rightButton()
        sleep(0.1)
except (KeyboardInterrupt, SystemExit):
    clearDisplay()
    GPIO.cleanup()       # clean up GPIO on CTRL+C exit
except FileNotFoundError as err:
    print('Error:' + err.message)
    print('Args:' + err.args)
    clearDisplay()
    GPIO.cleanup()       # clean up GPIO on CTRL+C exit
clearDisplay()
GPIO.cleanup()
