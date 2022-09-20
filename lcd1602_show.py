#!/usr/bin/python3

import time
import datetime
import subprocess
from socket import AF_INET
try:
    from gpiozero.pins.data import pi_info
    from gpiozero.pins.local import get_pi_revision
except ImportError:
    raise ImportError("This doesn't appear to be a Raspberry Pi device!")

import psutil

from lcd1602 import (
    LCD_LINE_1, LCD_LINE_2, lcd_init, lcd_string, lcd_cleanup, lcd_custom_char
)


PI_BOARD_INFO = pi_info()
BOOT_TIME = psutil.boot_time()
DATETIME_BOOT_TIME = datetime.datetime(*time.localtime(BOOT_TIME)[:6])

def size_human_readable(int_size):
    """ 返回人类可读的文件大小 """
    if int_size < 1024:
        return "%sB" % (int_size, )
    if int_size < 1024 * 1024:
        return "%0.1fK" % (int_size / 1024, )
    if int_size < 1024 * 1024 * 1024:
        return "%0.1fM" % (int_size / 1024 / 1024, )
    return "%0.1fG" % (int_size / 1024 / 1024 / 1024, )

# Unused
def get_device_model():
    with open('/sys/firmware/devicetree/base/model', 'r') as f:
        device_model = f.read().strip()
        if device_model[-1] == '\x00':
            device_model = device_model[:-1]
        return device_model

# Unused
def get_revision_string():
    # rc, output = subprocess.getstatusoutput("cat /proc/cpuinfo | grep Revision | cut -d ':' -f2")
    # if rc != 0:
    #     return ""
    # return output.strip()
    return hex(get_pi_revision())[2:]

def get_cpu_temp():
    # return psutil.sensors_temperatures()["cpu_thermal"][0].current
    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
        return int(f.read()) / 1000

def get_hostname():
    with open('/etc/hostname', 'r') as f:
        return f.read().strip()

def get_kernel_name():
    with open('/proc/version', 'r') as f:
        return f.read().strip().split(' ')[2]

def get_bootloader_version():
    rc, output = subprocess.getstatusoutput('vcgencmd bootloader_version')
    if rc != 0:
        return "Unknown"
    return output.splitlines()[0]

def get_ips():
    ips_list = []
    for iface_name, iface_info in psutil.net_if_addrs().items():
        for item in iface_info:
            if item.family is AF_INET:
                iface_addr = item.address
                break
        else:
            iface_addr = "No ip addr"
        ips_list.append((iface_name, iface_addr))
    return ips_list

def get_partitions_info():
    partitions_info = []
    for partition in psutil.disk_partitions():
        partition_mountpoint = partition.mountpoint
        partition_usage = psutil.disk_usage(partition.mountpoint)
        partitions_info.append(
            # mount point, total, percent
            (partition_mountpoint, size_human_readable(partition_usage.total), partition_usage.percent)
        )
    return partitions_info

def get_boot_time_delta() -> datetime.timedelta:
    return datetime.datetime(*time.localtime(time.time())[:6]) - DATETIME_BOOT_TIME

def print_boot_time_delta(timedelta: datetime.timedelta):
    time_delta_seconds = timedelta.seconds
    time_delta_days = timedelta.days if timedelta.days <= 999 else 999
    return "%sd %sh %sm %ss" % (
        str(time_delta_days).rjust(3),
        str(int(time_delta_seconds // 60 // 60)).zfill(2),
        str(int(time_delta_seconds // 60 % 60)).zfill(2),
        str(int(time_delta_seconds % 60)).zfill(2),
    )

KERNEL_NAME = get_kernel_name()
RAM_TOTAL_HUMAN_READABLE = size_human_readable(psutil.virtual_memory().total)
BOOTLOADER_VERSION = get_bootloader_version()

def main():
    # Initialise display
    lcd_init()

    custom_chars = [
        # bell
        bytearray([0x04, 0x0e, 0x0e, 0x0e, 0x1f, 0x00, 0x04, 0x00]),
        # note
        bytearray([0x02, 0x03, 0x02, 0x0e, 0x1e, 0x0c, 0x00, 0x00]),
        # clock
        bytearray([0x00, 0x0e, 0x15, 0x17, 0x11, 0x0e, 0x00, 0x00]),
        # heart
        bytearray([0x00, 0x0a, 0x1f, 0x1f, 0x0e, 0x04, 0x00, 0x00]),
        # duck
        bytearray([0x00, 0x0c, 0x1d, 0x0f, 0x0f, 0x06, 0x00, 0x00]),
        # check
        bytearray([0x00, 0x01, 0x03, 0x16, 0x1c, 0x08, 0x00, 0x00]),
        # cross
        bytearray([0x00, 0x1b, 0x0e, 0x04, 0x0e, 0x1b, 0x00, 0x00]),
        # ret arrow
        bytearray([0x01, 0x01, 0x05, 0x09, 0x1f, 0x08, 0x04, 0x00]),
    ]
    for i, byte_array in enumerate(custom_chars):
        lcd_custom_char(i, byte_array)

    for i in [[0x10*i, 0x10*(i+1)] for i in range(0x00, 0x0f+1, 2)]:
        sl_1 = "".join([chr(j) for j in range(i[0], i[0]+16)])
        sl_2 = "".join([chr(j) for j in range(i[1], i[1]+16)])
        lcd_string(sl_1, LCD_LINE_1)
        lcd_string(sl_2, LCD_LINE_2)
        time.sleep(0.75)

    lcd_string("Raspberry Pi", LCD_LINE_1)
    lcd_string("%s Rev %s" % (PI_BOARD_INFO.model, PI_BOARD_INFO.pcb_revision), LCD_LINE_2, scrolling=True)
    time.sleep(3)

    lcd_string("Revision:", LCD_LINE_1)
    lcd_string(PI_BOARD_INFO.revision, LCD_LINE_2, scrolling=True)
    time.sleep(3)

    lcd_string("Released:", LCD_LINE_1)
    lcd_string(PI_BOARD_INFO.released, LCD_LINE_2, scrolling=True)
    time.sleep(3)

    lcd_string("Manufacturer:", LCD_LINE_1)
    lcd_string(PI_BOARD_INFO.manufacturer, LCD_LINE_2, scrolling=True)
    time.sleep(3)

    lcd_string("Bootloader ver:", LCD_LINE_1)
    lcd_string(BOOTLOADER_VERSION, LCD_LINE_2, scrolling=True)
    time.sleep(3)

    lcd_string("Kernel:", LCD_LINE_1)
    lcd_string(KERNEL_NAME, LCD_LINE_2, scrolling=True)
    time.sleep(3)

    while True:
        datetime_now = datetime.datetime.now()
        lcd_string(datetime_now.strftime("%Y-%m-%d %a"), LCD_LINE_1)
        for _ in range(5):
            if (datetime_now.hour, datetime_now.minute, datetime_now.second) == (0, 0, 0):
                lcd_string(datetime_now.strftime("%Y-%m-%d %a"), LCD_LINE_1)
            lcd_string(datetime_now.strftime(" %I:%M:%S  %p"), LCD_LINE_2)
            datetime_now += datetime.timedelta(seconds=1)
            time.sleep(1)

        for _ in range(5):
            lcd_string("CPU used: %0.1f%%" % psutil.cpu_percent(), LCD_LINE_1)
            # chr(0xdf) == '°'
            lcd_string("CPU temp: %0.1f" % get_cpu_temp() + chr(0xdf) + "C", LCD_LINE_2)
            time.sleep(1)

        lcd_string("RAM total: %s" % RAM_TOTAL_HUMAN_READABLE, LCD_LINE_1)
        for _ in range(3):
            lcd_string("RAM used: %s" % size_human_readable(psutil.virtual_memory().used), LCD_LINE_2)
            time.sleep(1)
        for _ in range(3):
            lcd_string("RAM used: %0.1f%%" % psutil.virtual_memory().percent, LCD_LINE_2)
            time.sleep(1)

        boot_time_delta = get_boot_time_delta()
        for i in range(5):
            lcd_string("Boot time:", LCD_LINE_1)
            lcd_string(
                print_boot_time_delta(boot_time_delta + datetime.timedelta(seconds=i)), LCD_LINE_2
            )
            time.sleep(1)

        for mount_point, total_size, used_percent in get_partitions_info():
            lcd_string("Mount: " + mount_point, LCD_LINE_1)
            lcd_string("Total: " + total_size, LCD_LINE_2)
            time.sleep(3)
            lcd_string(" Used: %0.1f%%" % used_percent, LCD_LINE_2)
            time.sleep(3)

        lcd_string("Hostname:", LCD_LINE_1)
        lcd_string(get_hostname(), LCD_LINE_2, scrolling=True)
        time.sleep(3)

        for iface_name, ip_ in get_ips():
            lcd_string("iface: " + iface_name, LCD_LINE_1)
            lcd_string(ip_, LCD_LINE_2)
            time.sleep(3)

if __name__ == '__main__':
    try:
        main()
    finally:
        lcd_cleanup()
