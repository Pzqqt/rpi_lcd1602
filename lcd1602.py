#!/usr/bin/python3

try:
    import RPi.GPIO as GPIO
except ImportError:
    raise ImportError("This doesn't appear to be a Raspberry Pi device!")
import time


# Define GPIO to LCD mapping
LCD_RS = 16
LCD_E  = 12
LCD_D4 = 25
LCD_D5 = 24
LCD_D6 = 23
LCD_D7 = 18

# 背光电源引脚 (如果背光常亮请设置为None)
LCD_BL_POW = 17

# Define some device constants
LCD_WIDTH = 16  # Maximum characters per line
LCD_DAT = True
LCD_CMD = False

LCD_LINE_1 = 0x80  # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0  # LCD RAM address for the 2nd line

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005


def lcd_toggle_enable():
    # Toggle enable
    time.sleep(E_DELAY)
    GPIO.output(LCD_E, True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_E, False)
    time.sleep(E_DELAY)

def lcd_byte(bits, mode):
    # Send byte to data pins
    # bits = data
    # mode = True    for character
    #                False for command

    GPIO.output(LCD_RS, mode)  # RS

    # High bits
    GPIO.output(LCD_D4, bits & 0x10 == 0x10)
    GPIO.output(LCD_D5, bits & 0x20 == 0x20)
    GPIO.output(LCD_D6, bits & 0x40 == 0x40)
    GPIO.output(LCD_D7, bits & 0x80 == 0x80)

    # Toggle 'Enable' pin
    lcd_toggle_enable()

    # Low bits
    GPIO.output(LCD_D4, bits & 0x01 == 0x01)
    GPIO.output(LCD_D5, bits & 0x02 == 0x02)
    GPIO.output(LCD_D6, bits & 0x04 == 0x04)
    GPIO.output(LCD_D7, bits & 0x08 == 0x08)

    # Toggle 'Enable' pin
    lcd_toggle_enable()

def lcd_init():
    # Main program block
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)        # Use BCM GPIO numbers
    GPIO.setup(LCD_E,  GPIO.OUT)  # E
    GPIO.setup(LCD_RS, GPIO.OUT)  # RS
    GPIO.setup(LCD_D4, GPIO.OUT)  # DB4
    GPIO.setup(LCD_D5, GPIO.OUT)  # DB5
    GPIO.setup(LCD_D6, GPIO.OUT)  # DB6
    GPIO.setup(LCD_D7, GPIO.OUT)  # DB7
    if LCD_BL_POW is not None:
        GPIO.setup(LCD_BL_POW, GPIO.OUT)

    # Initialise display
    lcd_byte(0x33, LCD_CMD)  # 110011 Initialise
    lcd_byte(0x32, LCD_CMD)  # 110010 Initialise
    lcd_byte(0x06, LCD_CMD)  # 000110 Cursor move direction
    lcd_byte(0x0C, LCD_CMD)  # 001100 Display On, Cursor Off, Blink Off
    lcd_byte(0x28, LCD_CMD)  # 101000 Data length, number of lines, font size
    lcd_byte(0x01, LCD_CMD)  # 000001 Clear display
    time.sleep(E_DELAY)

def lcd_toggle_backlight(enable: bool):
    if LCD_BL_POW is not None:
        GPIO.output(LCD_BL_POW, enable)

def lcd_string(message: str, line, scrolling=False):
    # Send string to display

    def _lcd_string(_message: str):
        lcd_byte(line, LCD_CMD)
        for j in range(LCD_WIDTH):
            lcd_byte(ord(_message[j]), LCD_DAT)

    message_len = len(message)
    if message_len > LCD_WIDTH and scrolling:
        # 字符串长度大于LCD_WIDTH, 且scrolling为True时, 在同一行"滚动"显示.
        # 注意此时整个程序是阻塞的.
        # 这意味着, 如果你的程序是先显示第一行字符串再显示第二行字符串, 且第一行字符串长度大于LCD_WIDTH,
        # 那么只有第一行字符串滚动完毕了才会开始显示第二行字符串.
        # 此时你应该让你的程序先显示第二行字符串, 再显示第一行,
        # 同时也意味着这个函数尚不支持两行同时滚动.
        for i in range(message_len-LCD_WIDTH+1):
            _lcd_string(message[i:i+LCD_WIDTH])
            # 字符串滚动完之后不再sleep
            if i == message_len - LCD_WIDTH:
                break
            if i == 0:
                time.sleep(1.25)  # 滚动前额外停留1.25秒, 加上下面的0.75秒, 总计停留两秒
            # 每次滚动停留0.75秒 (停留时间太短的话字符串滚动得太快, 导致字符串难以辨识, 而且很费眼睛)
            time.sleep(0.75)
    else:
        message = message.ljust(LCD_WIDTH, " ")
        _lcd_string(message)

# https://github.com/T-622/RPI-PICO-I2C-LCD/blob/997b35940bda3addb473dea38c6c10e3cf48855c/lcd_api.py#L153
def lcd_custom_char(location, charmap):
    # Write a character to one of the 8 CGRAM locations,
    # available as chr(0) through chr(7).
    location &= 0x7
    lcd_byte(0x40 | (location << 3), LCD_CMD)
    time.sleep(E_DELAY)
    for i in range(8):
        lcd_byte(charmap[i], LCD_DAT)
        time.sleep(E_DELAY)

def lcd_cleanup():
    lcd_byte(0x01, LCD_CMD)
    lcd_string("Goodbye!", LCD_LINE_1)
    GPIO.cleanup()
