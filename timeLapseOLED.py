#!/usr/bin/env python3
#minmum version: Python 3.4
import threading
import string
import re
from time import sleep, monotonic as time
from os import statvfs, listdir, popen
from sys import exit
import signal
import sys

import Adafruit_SSD1306
import RPi.GPIO as GPIO
from picamera import PiCamera

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

import qrcode

import timeLapseMenu as lcdMenu

import socket
import fcntl
import struct

#---------------------DIR-&-FREE-STORAGE-&-IP-ADRESS-----------------
pictureDir = '/home/pi/Pictures/TimeLapse/'
st = statvfs(pictureDir)
freeSpace =  st.f_bavail * st.f_frsize / 1024 / 1024 #in MB
#ipv4 = popen('ip addr show eth1').read().split("inet ")[1].split("/")[0]
ipv4 = "192.168.178.22"

#---------------------------GPIO---------------------------
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
buttonEdge = GPIO.FALLING #FALLING: relase trigger, RISING: press trigger
#Quit, Left, Right, Back, Enter Buttons
gpioButtons = [27,23,4,22,17]
GPIO.setup([27,23,4,22,17], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

debug = True #show pressed buttons

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
image = Image.new('1', (width, height), "white")

# Create drawing object.
draw = ImageDraw.Draw(image)

# Load font
fontPath = '/usr/share/fonts/truetype/gentium-basic/GenBasR.ttf'
font = ImageFont.truetype(fontPath, 15)

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

# Create QR-Code and sow it
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=2,
    border=5,
)
qr.add_data('http://' + ipv4 + '/')
qr.make(fit=True)
qrImage = qr.make_image()
image.paste(qrImage, (0,0))
image.save("result.png", "PNG")
disp.image(image)
drawBuffer()
GPIO.wait_for_edge(gpioButtons[0], buttonEdge)
GPIO.cleanup(gpioButtons[4])
print(GPIO.VERSION)
GPIO.setup(gpioButtons[4], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#------------------------CAMERA---------------------------
camera = PiCamera()
previewOnStartup = True
if previewOnStartup: camera.start_preview()

#Camera Settings
pictureFormat = 'jpeg'
camera.resolution = '2592x1458'

#-----------------------TIMING--------------------------------
quitButtonPressTime = time()
quitButtonPressed = False
leftButtonPressTime = time()
leftButtonPressed = False
rightButtonPressTime = time()
rightButtonPressed = False

#-----------------------MENU-----------------------------------
def startTimeLapse(duration, interval, raw):
    global font, draw
    if(raw):
        estSize = 10.0
    else:
        estSize = 4.5
    amountOfPictures = 100000
    camera.shutter_speed = 18868
    camera.resolution = '2592x1458'
    clearBuffer()
    if int(interval) != 0:
        amountOfPictures = int(duration * 60 * 60 / interval)
        print('starting time-lapse')
        writeStringToBuffer(0,'Timelapsing')
        writeStringToBuffer(1, str(amountOfPictures) + '\n, est. ' + str(int(amountOfPictures * estSize/freeSpace*100))+ '%')
        writeStringToBuffer(2, str(round(amountOfPictures / 30,1)) + ' sec@30fps')
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
    #just for testing REMOVE IT
    #----------------
    sleep(5)

    textWidth, textHeight = draw.textsize('0123456789', font=font)
    thirdLineY = 2 * (textHeight + 2)
    for pic in range(0,amountOfPictures):
        clearBuffer()
        writeStringToBuffer(0, str(pic + 1) + '/' + str(amountOfPictures) + ' ' + str(round((pic + 1) / amountOfPictures * 100,1)) + '%')
        writeStringToBuffer(1, str(int((amountOfPictures - pic + 1) * interval / 60))  + 'min left')
        drawBuffer()
        camera.capture(pictureDir + fileName.format(pic), format=pictureFormat, bayer=raw)
        if int(interval) != 0:
            for i in range(0,interval):
                sleep(1)
                draw.rectangle((0, thirdLineY, textWidth, thirdLineY+textHeight), fill=0)
                writeStringToBuffer(2, str(interval-i))
                drawBuffer()
        else:
            while not GPIO.input(gpioButtons[1]):
                sleep(0.01)

    clearBuffer()
    font = ImageFont.truetype(fontPath, 50)
    writeStringToBuffer(0,'DONE.')
    font = ImageFont.truetype(fontPath, 15)
    drawBuffer()

    #should shut down when quit is helt
    while True:
        if GPIO.input(gpioButtons[0]):
            writeStringToBuffer(2.5,'shutting down.')
            drawBuffer()
            shutdown()

def startStopMotion(duration, interval, raw):
    startTimeLapse(duration, 0, raw)

menuItems = ['Duration', 'Interval', 'Shutter Speed','save raw data', 'start lapse', 'start stop-motion']
# unit, [min, step, max, default/current] (for float/int values)
# unit, [possibleString1, possibleString2, ...] (for string values)
# unit, [actionString, function] (for calling a function)
menuChoices = [ ['hrs', [1,1,48,1]], ['sec', [2,2,120,30]], ['sec', ['1/1000', '1/500','1/250', '1/125', '1/60', '1/60', '1/30', '1/15', '1/8', '1/4', '1/2', '1', '2', '4', 6]], ['', ['Yes','No', 0]], ['', ['I\'m ready', startTimeLapse]], ['', ['I\'m ready', startStopMotion]] ]
menu = lcdMenu.timeLapseMenu(menuItems, menuChoices, disp, draw, image, font, camera)
menu.home()

#--------------------INTERRUPTS (buttons)--------------------
def quitButton(channel = False):
    global quitButtonPressTime, quitButtonPressed
    if GPIO.input(gpioButtons[0]):
        #pressed
        quitButtonPressed = True
        quitButtonPressTime = time()
        if debug: print("gpioButtons[0] Pressed at", quitButtonPressTime)
    else:
        #released
        quitButtonPressed = False
        if debug: print("gpioButtons[0] released at", time())

def leftButton(channel = False):
    global leftButtonPressTime, leftButtonPressed
    if GPIO.input(gpioButtons[1]):
        #pressed
        leftButtonPressed = True
        if debug: print('< button pressed')
        leftButtonPressTime = time()
        if not menu.capturing():
            menu.goLeft()
    else:
        leftButtonPressed = False

def rightButton(channel = False):
    global rightButtonPressTime, rightButtonPressed
    if GPIO.input(gpioButtons[2]):
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

GPIO.add_event_detect(gpioButtons[0], GPIO.BOTH, callback=quitButton, bouncetime=300)
GPIO.add_event_detect(gpioButtons[1], GPIO.BOTH, callback=leftButton, bouncetime=300)
GPIO.add_event_detect(gpioButtons[2], GPIO.BOTH, callback=rightButton, bouncetime=300)
GPIO.add_event_detect(gpioButtons[3], buttonEdge, callback=backButton, bouncetime=300)
GPIO.add_event_detect(gpioButtons[4], buttonEdge, callback=enterButton, bouncetime=300)

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

class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.kill_now = True

#--------------------LOOP--------------------
try:
    print('Running...')
    killer = GracefulKiller()
    while(1):
        if leftButtonPressed and time() - leftButtonPressTime >= 0.2:
            leftButton()
        if rightButtonPressed and time() - rightButtonPressTime >= 0.2:
            rightButton()
        if quitButtonPressed and time() - quitButtonPressTime >= 3: #at least 3 seconds helt before release
            #raise SystemExit
            print('Time to quit')
            shutdown()
            break
        if killer.kill_now:
            print('timeLapseOLED died')
            break
        sleep(0.1)

except (KeyboardInterrupt, SystemExit):
    clearDisplay()
    GPIO.cleanup()       # clean up GPIO on CTRL+C exit

except FileNotFoundError as err:
    print('Error:' + err.message)
    print('Args:' + err.args)
    clearDisplay()
    GPIO.cleanup()
    camera.stop_preview()

camera.stop_preview()
clearDisplay()
GPIO.cleanup()
