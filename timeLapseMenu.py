from time import sleep
from fractions import Fraction

class timeLapseMenu:
    currentItem = 0
    mode = 0
    debug = True
    width = 128
    height = 64
    classWideCapturing = False
    items = []

    def drawBuffer(self):
        # Draw the image buffer.
        self.disp.image(self.image)
        self.disp.display()

    def clearBuffer(self):
        # Clear image buffer by drawing a black filled box.
        global width, height
        self.draw.rectangle((0,0,width,height), outline=0, fill=0)
        self.nextX = [0,0]

    def writeStringToBuffer(self, line, text, instantDisplay = False, aligment = 'left', arrows = (False, False)):
        global width, height
        effectiveWidth = width
        textWidth, textHeight = self.draw.textsize(text, font=self.font)
        if arrows[0]:
            effectiveWidth -= self.draw.textsize('<', font=self.font)[0]
            self.nextX[line] = self.draw.textsize('< ', font=self.font)[0]
            self.draw.text( (0, line * (textHeight + 5) ), '<', font=self.font, fill=255)
        if arrows[1]:
            effectiveWidth -= self.draw.textsize('>', font=self.font)[0]
            self.draw.text( (width - self.draw.textsize('>', font=self.font)[0], line * (textHeight + 5) ), '>', font=self.font, fill=255)
        if aligment == 'centered':
            self.draw.text(((width - textWidth) / 2, line * (textHeight + 5)), text, font=self.font, fill=255)
            self.nextX[line] += (width - textWidth) / 2 + self.draw.textsize(text, font=self.font)[0]
        elif aligment == 'left':
            self.draw.text((0, line * (textHeight + 5)), text, font=self.font, fill=255)
            self.nextX[line] += self.draw.textsize(text, font=self.font)[0]
        elif aligment == 'next':
            self.draw.text((nextX[line], line * (textHeight + 5)), text, font=self.font, fill=255)
            self.nextX[line] += self.draw.textsize(text, font=self.font)[0]
        elif aligment == 'right':
            self.draw.text((width-textWidth, line * (textHeight + 5)), text, font=self.font, fill=255)
        if instantDisplay:
            self.drawBuffer()

    def clearDisplay(self):
        self.clearBuffer()
        self.drawBuffer()

    def __init__(self, theItems, theChoices, theDisplay, theDrawObject, theImage, theFont, theCamera):
        global width, height, items
        items = theItems
        self.choices = theChoices
        self.font = theFont
        self.image = theImage
        self.camera = theCamera
        self.debug = True
        if len(self.choices) != len(items):
            print('choices list does not fit the items list')
        self.disp = theDisplay
        self.draw = theDrawObject
        self.nextX = [0,0]
        width = self.disp.width
        height = self.disp.height
        #self.lcd = theLcd
        #self.lcd.clear()      #0123456789abcdef0123456789abcdef
        self.writeStringToBuffer(0, 'TimeLapsePhoto', aligment = 'centered')
        self.writeStringToBuffer(1, 'Control Panel', instantDisplay = True, aligment = 'centered')

    def home(self):
        global currentItem, mode
        #self.lcd.clear()
        currentItem = 0
        self.setMode(0)

    def leftPressed(self):
        global currentItem
        if not self.classWideCapturing:
            if mode == 0:
                self.goToLastItem(printUpdate=True)
            #Value Mode
            else:
                if self.debug: print('setting value -')
                self.setItemValue(currentItem, -1)
                #update the display
                self.updateItem()

    def rightPressed(self):
        global currentItem, mode
        if not self.classWideCapturing:
            if mode == 0:
                self.goToNextItem(printUpdate=True)
            #Value Mode
            else:
                if self.debug: print('setting value +')
                self.setItemValue(currentItem, 1)
                #update the display
                self.updateItem()

    def goToNextItem(self, printUpdate=False):
        global currentItem, items
        if currentItem == len(items) - 1:
            next_Item = 0
        else:
            next_Item = currentItem + 1
        currentItem = next_Item
        if printUpdate: self.updateItem()

    def goToLastItem(self, printUpdate=False):
        global currentItem, items
        if currentItem == 0:
            next_Item = len(items) - 1
        else:
            next_Item = currentItem - 1
        currentItem = next_Item
        if printUpdate: self.updateItem()

    def enterPressed(self):
        global mode
        if not self.classWideCapturing:
            if mode is 1:
                if self.debug: print('in set mode, going to the next value AFTER IMPLEMENTED (right)')
                #self.goToNextItem(printUpdate=True)
            else:
                if self.debug: print('going down into set mode')
                #"delete" arrows
                self.updateItem()
                self.setMode(1)

    def goBack(self):
        global mode
        if not self.classWideCapturing:
            if mode is 1:
                self.setMode(0)
                updateItem()


    def backPressed(self):
        global mode, currentItem, debug
        if not self.classWideCapturing:
            if mode is 1:
                if self.debug: print('going into menu mode')
                self.setMode(0)
            elif mode is 0:
                if self.debug: print('already in menu mode')

    def updateItem(self):
        global items, currentItem, mode
        self.clearBuffer()
        if mode is 0:
            showArrows = True
        else:
            showArrows = False

        if currentItem != 0 and showArrows:
            showLeftArrow = True
        else:
            showLeftArrow = False

        if currentItem == len(items) - 1 or showArrows == False:
            showRightArrow = False
        else:
            showRightArrow = True

        self.writeStringToBuffer(0, items[currentItem], aligment = 'centered', arrows = (showLeftArrow, showRightArrow), instantDisplay=False)
        #self.lcd.cursor_pos = (1,0)
        if type(self.choices[currentItem][1][0]) is str:
            if type(self.choices[currentItem][1][1]) is str:
                currentElementID = len(self.choices[currentItem][1]) - 1
                self.writeStringToBuffer(1,self.choices[currentItem][1][self.choices[currentItem][1][currentElementID]], aligment = 'left')
            if callable(self.choices[currentItem][1][1]):
                useless = True
                self.writeStringToBuffer(1,self.choices[currentItem][1][0], aligment = 'left')
        else:
            self.writeStringToBuffer(1,str(round(self.choices[currentItem][1][3],1)), aligment = 'left')
        self.writeStringToBuffer(1,self.choices[currentItem][0], aligment = 'right', instantDisplay = True)

    def setItemValue(self, currentItem, factor):
        if type(self.choices[currentItem][1][1]) is str:
            lastStringElement = len(self.choices[currentItem][1]) - 2
            currentElement = self.choices[currentItem][1][lastStringElement + 1]
            if currentElement + factor <= lastStringElement   and currentElement + factor >= 0:
                self.choices[currentItem][1][lastStringElement + 1] = currentElement + factor
            else:
                if currentElement + factor < 0:
                    self.choices[currentItem][1][lastStringElement + 1] = lastStringElement
                if currentElement + factor > lastStringElement:
                    self.choices[currentItem][1][lastStringElement + 1] = 0
            if currentItem == 2:
                currentStringValue = self.choices[currentItem][1][ self.choices[currentItem][1][lastStringElement + 1] ]
                self.camera.shutter_speed = int(float(sum(Fraction(s) for s in currentStringValue.split())) * 10**6)

        if type(self.choices[currentItem][1][1]) is int or type(self.choices[currentItem][1][1]) is float:
                minValue = self.choices[currentItem][1][0]
                #make the step positive or negative depending on factor
                valueStep = self.choices[currentItem][1][1] * factor
                maxValue = self.choices[currentItem][1][2]
                currentValue = self.choices[currentItem][1][3]
                if currentValue + valueStep <= maxValue and currentValue + valueStep >= minValue:
                    self.choices[currentItem][1][3] += valueStep
                else:
                    if abs(currentValue - maxValue) <= 0.01:
                        self.choices[currentItem][1][3] = minValue
                    if abs(currentValue - minValue) <= 0.01:
                        self.choices[currentItem][1][3] = maxValue

        if callable(self.choices[currentItem][1][1]):
            duration = self.choices[0][1][3]
            interval = self.choices[1][1][3]
            if self.choices[3][1][2] == 0:
                raw = True
            else:
                raw = False
            classWideCapturing = True
            self.choices[currentItem][1][1](duration, interval, raw)
    def capturing(self):
        return self.classWideCapturing

    def getMode(self):
        global mode
        return mode

    def setMode(self, newMode, updateItem = True):
        global mode
        mode = newMode
        if updateItem: self.updateItem()
