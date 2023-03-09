# A collection of various text-based displays
# Currently supports 4-digit seven-segment displays - both with a tm1637 backpack
# and without (using PIO)
# And also LCD 1602 displays - both using an i2c backpack as well as GPIO
# Only supports number and basic text displays - PIO 7 seg only supports number

from machine import Pin, I2C, SPI
import rp2
import time
from rp2 import PIO
import tm1637
from gpio_lcd import *
from pico_i2c_lcd import I2cLcd
from ssd1306 import SSD1306_I2C
import max7219

"""
The Display Base class - might not actually be needed
But here to ensure we do not have a duckTyping problem
"""
class Display:

    def reset(self):
        print(f"reset NOT IMPLEMENTED in {type(self).__name__}")

    def showNumber(self, number):
        print(f"showNumber NOT IMPLEMENTED! in {type(self).__name__}")

    def showText(self, text):
        print(f"showText NOT IMPLEMENTED! in {type(self).__name__}")

    def scroll(self, text, speed=250):
        print(f"Scroll NOT IMPLEMENTED! in {type(self).__name__}")


"""
Seven Segment Display class - implements a 4-digit seven segment display
Decimal points not supported - colon can be used when showing two numbers
"""
class SevenSegmentDisplay(Display):
    def __init__(self, clk=16, dio=17):
        self._tm = tm1637.TM1637(clk=Pin(clk), dio=Pin(dio))

    """ 
    clear the display screen
    """
    def reset(self):
        self._tm.write([0, 0, 0, 0])

    """
    show a single number
    """
    def showNumber(self, number):
        self._tm.number(number)

    """
    Show two numbers optionally separated by a colon
    by default, the colon is shown
    """
    def showNumbers(self, num1, num2, colon=True):
        self._tm.numbers(num1, num2, colon)

    """
    Show a string - only first 4 characters will be shown
    for anything bigger than 4 characters.
    """
    def showText(self, text):
        self._tm.show(text)

    """
    Scroll a longer text - note that this will use a sleep
    call to pause between movements.
    """
    def scroll(self, text, speed=250):
        self._tm.scroll(text, speed)

"""
A Raw 7 segment display that uses RPi PIO along with internal StateMachine
to poll 4 digits into the display. All digits are shown always so there will be
leading zeros for numbers under 4 digits
"""
class SevenSegmentDisplayRaw(Display):
    def __init__(self, pinstart=2, digstart=10):
        self._digits = [
            0b11000000, # 0
            0b11111001, # 1
            0b10100100, # 2 
            0b10110000, # 3
            0b10011001, # 4
            0b10010010, # 5
            0b10000010, # 6
            0b11111000, # 7
            0b10000000, # 8
            0b10011000, # 9
            ]
        self._sm = rp2.StateMachine(0, sevseg, freq=2000, out_base=Pin(pinstart), sideset_base=Pin(digstart))
        self._sm.active(1)
  
    def _segmentize(self, num):
        return (
            self._digits[num % 10] | self._digits[num // 10 % 10] << 8
            | self._digits[num // 100 % 10] << 16 
            | self._digits[num // 1000 % 10] << 24 
        )

    def showNumber(self, n):
        self._sm.put(self._segmentize(n))
        
    def reset(self):
        self._sm.put(self._segmentize(0))

"""
LCD Display class - currently supports displays with an I2C backpack
as well as displays directly driven via the d4-d7 pins
"""
class LCDDisplay(Display):
    """
    constructor for the direct-driven displays
    """
    def __init__(self, rs=5, e=4, d4=3, d5=2, d6=1, d7=0):
        print("LCDDisplay Constructor")
        self._lcd = GpioLcd(rs_pin=Pin(rs),
              enable_pin=Pin(e),
              d4_pin=Pin(d4),
              d5_pin=Pin(d5),
              d6_pin=Pin(d6),
              d7_pin=Pin(d7),
              num_lines=2, num_columns=16)

    """
    Constructor for the I2C displays
    """
    def __init__(self, sda=0, scl=1):
        print("LCDDisplay (I2C) Constructor")
        i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
        I2C_ADDR = i2c.scan()[0]
        self._lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

    """ 
    clear the display screen
    """
    def reset(self):
        print("LCDDisplay: reset")
        self._lcd.clear()

    """
    show a single number
    """
    def showNumber(self, number, row=0, col=0):
        print(f"LCDDisplay - showing number {number} at {row},{col}")
        self._lcd.move_to(col, row)
        self._lcd.putstr(f"{number}")

    """
    Show two numbers optionally separated by a colon
    by default, the colon is shown
    """
    def showNumbers(self, num1, num2, colon=True, row=0, col=0):
        print(f"LCDDisplay - showing numbers {num1}, {num2} at {row},{col}")
        self._lcd.move_to(col, row)
        colsym = ":" if colon else " "
        self._lcd.putstr(f"{num1}{colsym}{num2}")

    """
    Show a string - only first 4 characters will be shown
    for anything bigger than 4 characters.
    """
    def showText(self, text, row=0, col=0):
        print(f"LCDDisplay - showing text {text} at {row},{col}")
        self._lcd.move_to(col, row)
        self._lcd.putstr(text)

    """
    Scroll a longer text - note that this will use a sleep
    call to pause between movements.
    """
    def scroll(self, text, speed=250):
        print("LCDDisplay: Scroll - Not yet implemented")

"""
An implementation of the MAX7219 Dot Matrix display
Fairly simplistic implementation - tested only with simulator so far 
"""
class DotMatrixDisplay(Display):

    def __init__(self, sck=18, mosi=19, cs=17):
        self._spi = SPI(0, baudrate=10000000, polarity=1, phase=0, sck=Pin(sck), mosi=Pin(mosi))
        # Create matrix display instant, which has four MAX7219 devices.
        self._dot = max7219.Matrix8x8(self._spi, Pin(cs, Pin.OUT), 4)
        self._dot.brightness(10)
        self.reset()

    def reset(self):
        #Clear the display.
        self._dot.fill(0)
        self._dot.show()

    def showNumber(self, number):
        self._dot.text(str(number), 0, 0, 1)
        self._dot.show()

    def showText(self, text):
        self._dot.text(text, 0, 0, 1)
        self._dot.show()

    def scroll(self, text, speed=50):
        #Get the message length
        length = len(text)
        column = (length * 8)
        for x in range(32, -column, -1):     
            #Clear the display
            self._dot.fill(0)
            # Write the scrolling text in to frame buffer
            self._dot.text(text,x,0,1)
            #Show the display
            self._dot.show()
      
            #Set the Scrolling speed. Here it is 50mS.
            time.sleep(speed/1000)

"""
OLEDDisplay class - implements an OLED display
"""
class OLEDDisplay(Display):

    def __init__(self, sda=26, scl=27, width=128, height=64):
        self._i2c = I2C(1, sda=Pin(sda), scl=Pin(scl), freq=400000)
        self._oled = SSD1306_I2C(width, height, self._i2c)
        self.reset()

    def reset(self):
        self._oled.fill(0)
        self._oled.show()
        
    def showNumber(self, number):
        self._oled.text(str(number), 0, 0, 1)
        self._oled.show()

    def showText(self, text):
        self._oled.text(text, 0, 0, 1)
        self._oled.show()

# Internals used by the PIO state machine
@rp2.asm_pio(out_init=[PIO.OUT_LOW]*8, sideset_init=[PIO.OUT_LOW]*4)
def sevseg():
    wrap_target()
    label("0")
    pull(noblock)           .side(0)      # 0
    mov(x, osr)             .side(0)      # 1
    out(pins, 8)            .side(1)      # 2
    out(pins, 8)            .side(2)      # 3
    out(pins, 8)            .side(4)      # 4
    out(pins, 8)            .side(8)      # 5
    jmp("0")                .side(0)      # 6
    wrap()


