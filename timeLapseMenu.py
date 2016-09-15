from time import sleep

class timeLapseMenu:
    currentItem = 0
    mode = 0
    debug = False
    def __init__(self, theItems, theChoices, theLcd):
        self.items =theItems
        self.choices = theChoices
        self.debug = False
        if len(self.choices) != len(self.items):
            print('choices list does not fit the items list')
        self.lcd = theLcd
        self.lcd.clear()      #0123456789abcdef0123456789abcdef
        self.lcd.write_string(' TimeLapsePhoto  Control  Panel ')

    def home(self):
        global currentItem, mode
        self.lcd.clear()
        self.printItem(0)
        currentItem = 0
        mode = 0

    def goLeft(self):
        global currentItem
        #Menu Mode
        if mode == 0:
            if currentItem == 0:
                next_Item = len(self.items) - 1
            else:
                next_Item = currentItem - 1
            currentItem = next_Item
            self.printItem(next_Item)
        #Value Mode
        else:
            if self.debug: print('setting value -')
            self.setItemValue(currentItem, -1)
            #update the display
            self.printItem(currentItem, False)

    def goRight(self):
        global currentItem
        #Menu Mode
        if mode == 0:
            if currentItem == len(self.items) - 1:
                next_Item = 0
            else:
                next_Item = currentItem + 1
            currentItem = next_Item
            self.printItem(next_Item)
        #Value Mode
        else:
            if self.debug: print('setting value +')
            self.setItemValue(currentItem, 1)
            #update the display
            self.printItem(currentItem, False)

    def goDown(self):
        global mode
        if mode >= 1:  #if setting a value
            if self.debug: print('in set mode, going to the next value (right)')
            mode = mode + 1
        else:
            if self.debug: print('going down into set mode')
            #"delete" arrows
            self.lcd.cursor_pos = (0,0)
            self.lcd.write_string(' ')
            self.lcd.cursor_pos = (0,15)
            self.lcd.write_string(' ')
            mode = 1

    def goBack(self):
        global mode
        if mode >= 1:
            mode = mode - 1

    def goUp(self):
        global mode, currentItem, debug
        if mode >= 1:
            if self.debug: print('going into menu mode')
            self.lcd.cursor_pos = (0,0)
            self.lcd.write_string(self.items[currentItem])
            mode = 0
        if mode == 0:
            if self.debug: print('already in menu mode')

    def printItem(self, itemID, showArrows = True):
        self.lcd.clear()
        self.lcd.cursor_pos = (0,0)
        if showArrows:
            self.lcd.cursor_pos = (0,0)
            self.lcd.write_string(self.items[itemID])
        else:
            self.lcd.cursor_pos = (0,1)
            arrowlessString = self.items[itemID][1:15]
            self.lcd.write_string(arrowlessString)

        self.lcd.cursor_pos = (1,0)
        if type(self.choices[itemID][1][0]) is str:
            if type(self.choices[itemID][1][1]) is str:
                currentElementID = len(self.choices[2][1]) - 1
                self.lcd.write_string(self.choices[itemID][1][self.choices[itemID][1][currentElementID]])
            if callable(self.choices[itemID][1][1]):
                self.lcd.write_string(self.choices[itemID][1][0])
        else:
            self.lcd.write_string(str(round(self.choices[itemID][1][3],1)))
        self.lcd.cursor_pos = (1,15-len(self.choices[itemID][0]))
        self.lcd.write_string(self.choices[itemID][0])

    def setItemValue(self, itemID, factor):
        if type(self.choices[itemID][1][1]) is str:
            lastStringElement = len(self.choices[itemID][1]) - 2
            currentElement = self.choices[itemID][1][lastStringElement + 1]
            if currentElement + factor <= lastStringElement   and currentElement + factor >= 0:
                self.choices[itemID][1][lastStringElement + 1] = currentElement + factor
            else:
                if currentElement + factor < 0:
                    self.choices[itemID][1][lastStringElement + 1] = lastStringElement
                if currentElement + factor > lastStringElement:
                    self.choices[itemID][1][lastStringElement + 1] = 0

        if type(self.choices[itemID][1][1]) is int or type(self.choices[itemID][1][1]) is float:
                minValue = self.choices[itemID][1][0]
                #make the step positive or negative depending on factor
                valueStep = self.choices[itemID][1][1] * factor
                maxValue = self.choices[itemID][1][2]
                currentValue = self.choices[itemID][1][3]
                if currentValue + valueStep <= maxValue and currentValue + valueStep >= minValue:
                    self.choices[itemID][1][3] += valueStep
                else:
                    if abs(currentValue - maxValue) <= 0.01:
                        self.choices[itemID][1][3] = minValue
                    if abs(currentValue - minValue) <= 0.01:
                        self.choices[itemID][1][3] = maxValue

        if callable(self.choices[itemID][1][1]):
            duration = self.choices[0][1][3]
            interval = self.choices[1][1][3]
            if self.choices[2][1][2] == 0:
                raw = True
            else:
                raw = False
            self.choices[itemID][1][1](duration, interval, raw)
