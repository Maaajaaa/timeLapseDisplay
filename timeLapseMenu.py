from time import sleep

class timeLapseMenu:
    currentItem = 0
    mode = 0
    def __init__(self, theItems, theChoices, theLcd):
        self.items =theItems
        self.choices = theChoices
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
            print('setting value -')
            self.setItemValue(currentItem, -1)
            #update the display
            self.printItem(currentItem)

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
            print('setting value +')
            self.setItemValue(currentItem, 1)
            #update the display
            self.printItem(currentItem)

    def goDown(self):
        global mode
        if mode > 1:  #if setting a value
            print('in set mode, going to the next value (right)')
            mode = mode + 1
        else:
            print('going down into set mode')
            #"delete" arrows
            self.lcd.cursor_pos = (0,0)
            self.lcd.write_string(' ')
            self.lcd.cursor_pos = (0,15)
            self.lcd.write_string(' ')
            mode = 1

    def goBack(self):
        global mode
        if mode > 1:
            mode = mode - 1

    def goUp(self):
        global mode, currentItem
        if mode >= 1:
            print('going into menu mode')
            self.lcd.cursor_pos = (0,0)
            self.lcd.write_string(self.items[currentItem])
            mode = 0
        if mode == 0:
            print('already in menu mode')

    def printItem(self, itemID):
        self.lcd.cursor_pos = (0,0)
        self.lcd.write_string(self.items[itemID])
        #show current/default setting
        self.lcd.cursor_pos = (1,0)
        self.lcd.write_string('                ')
        self.lcd.cursor_pos = (1,0)
        self.lcd.write_string(str(round(self.choices[itemID][1][3],1)))
        self.lcd.cursor_pos = (1,15-len(self.choices[itemID][0]))
        self.lcd.write_string(self.choices[itemID][0])

    def setItemValue(self, itemID, factor):
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
