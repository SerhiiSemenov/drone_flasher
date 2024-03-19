#!/usr/bin/python

from enum import Enum
import shutil
import os

from elrs_helpers import ElrsUploadResult
import BFinitPassthrough
import serials_find
from firmware import DeviceType

import sys
from os.path import dirname

import serial
import time
import re
import json

sys.path.append(dirname(__file__) + '/external/esptool')

from external.esptool import esptool
import json
sys.path.append(dirname(__file__) + "/external")


def upload_esp8266_bf(baud, force:bool, erase:bool, file_name:str, firmware:str):
    port = serials_find.get_serial_port()
    if port == None:
        print("No serial port found")
        os._exit(1)
    mode = 'upload'
    if force == True:
        mode = 'uploadforce'
    retval = BFinitPassthrough.main(['-p', port, '-b', str(baud), '-r', firmware, '-a', mode])
    if retval != ElrsUploadResult.Success:
        return retval
    try:
        cmd = ['--passthrough', '--chip', 'esp8266', '--port', port, '--baud', str(baud), '--before', 'no_reset', '--after', 'soft_reset', 'write_flash']
        if erase: cmd.append('--erase-all')
        cmd.extend(['0x0000', file_name])
        esptool.main(cmd)
    except:
        return ElrsUploadResult.ErrorGeneral
    return ElrsUploadResult.Success

def upload_esp32_bf(args, options):
    print("Uploading via Betaflight")
    if args.port == None:
        args.port = serials_find.get_serial_port()
    mode = 'upload'
    if args.force == True:
        mode = 'uploadforce'
    retval = BFinitPassthrough.main(['-p', args.port, '-b', str(args.baud), '-r', options.firmware, '-a', mode])
    if retval != ElrsUploadResult.Success:
        return retval
    try:
        esptool.main(['--passthrough', '--chip', 'esp32', '--port', args.port, '--baud', str(args.baud), '--before', 'no_reset', '--after', 'hard_reset', 'write_flash', '-z', '--flash_mode', 'dio', '--flash_freq', '40m', '--flash_size', 'detect', '0x10000', file_name])
    except:
        return ElrsUploadResult.ErrorGeneral
    return ElrsUploadResult.Success

def upload_esp32_uart(port, baud, erase:bool, file_name:str):
    print("Uploading esp32 via UART")
    if port == None:
        port = serials_find.get_serial_port()
    try:
        dir = os.path.dirname(file_name)
        cmd = ['--chip', 'esp32', '--port', port, '--baud', str(baud), '--after', 'hard_reset', 'write_flash']
        if erase: cmd.append('--erase-all')
        cmd.extend(['-z', '--flash_mode', 'dio', '--flash_freq', '40m', '--flash_size', 'detect', '0x1000', os.path.join(dir, 'bootloader.bin'), '0x8000', os.path.join(dir, 'partitions.bin'), '0xe000', os.path.join(dir, 'boot_app0.bin'), '0x10000', file_name])
        esptool.main(cmd)
    except:

        return ElrsUploadResult.ErrorGeneral
    return ElrsUploadResult.Success

def wait_for_uart_port(timeout=30, interval=1):
    """
    Wait for a UART port to become available.
    :param port_name: Name of the UART port (e.g., '/dev/ttyUSB0')
    :param timeout: Maximum time to wait (in seconds)
    :param interval: Interval between checks (in seconds)
    :return: True if port becomes available within the timeout, False otherwise
    """
    print("Waiting for UART port to become available...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        if serials_find.get_serial_port() != None:
            return True
        time.sleep(interval)
    return False

def int_serial(baud_rate):
    wait_for_uart_port(30, 1)
    time.sleep(1)
    port = serials_find.get_serial_port()
    if port == None:
        print("No serial port found")
        os._exit(1)

    try:
        print(".", end="")
        ser = serial.Serial(port, baud_rate, timeout=1)
        print(".", end="")
        time.sleep(0.3)
        print(".", end="")
        ser.write("#\n".encode())
        ser.flush()
        ser.readlines()
        print(".")

    except serial.SerialException as e:
        print(f"Error occurred while communicating with the flight controller: {e}")
        sys.exit()
    return ser

def change_serial_config(bf_serial, uart_number_to_set, uart_number_to_reset):

    bf_serial.write((f"serial {uart_number_to_set} 64 115200 57600 0 115200" + "\n").encode())
    time.sleep(0.3)
    bf_serial.write((f"serial {uart_number_to_reset} 0 115200 57600 0 115200" + "\n").encode())
    time.sleep(0.3)
    bf_serial.write(("save" + "\n").encode())
    bf_serial.close()
    time.sleep(1)

    print("Serial configuration changed successfully!")

def reset_serial_config(bf_serial, ports):

    for port in ports:
        bf_serial.write((f"serial {port} 0 115200 57600 0 115200" + "\n").encode())
        time.sleep(0.3)

    bf_serial.write(("save" + "\n").encode())
    bf_serial.close()
    time.sleep(3)

    print("Serial configuration reset successfully!")

def get_betaflight_serial_config(bf_serial):
    """
    Get the serial configuration from Betaflight.
    Return CRSF port number.
    """
    port = []

    bf_serial.write(b'serial\r\n')  # Send 'serial' command
    time.sleep(0.1)
    response = bf_serial.readlines()  # Read response lines
    # Parse the response to extract serial configurations
    for line in response:
        line = line.decode('utf-8').strip()
        match = re.match(r'serial (\d+) (\d+) (\d+) \d+ \d+ \d+', line)
        if match:
            device = int(match.group(2))
            if device == 64:
                port.append(int(match.group(1)))
            baud_rate = int(match.group(3))

    return port

def parse_config_file():
    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'conf.json')
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config


if __name__ == '__main__':
    is_rx1_updated = False
    is_rx2_updated = False
    upload_speed = 420000
    bf_serial_speed = 115200

    print("Starting binary flash")
    config = parse_config_file()
    rx1_port = config['rx1_port'] - 1
    rx2_port = config['rx2_port'] - 1
    target = config['target']
    firmware_file_rx1 = os.path.join(os.path.dirname(os.path.dirname(__file__)), config['firmware_file_rx1'])
    firmware_file_rx2 = os.path.join(os.path.dirname(os.path.dirname(__file__)), config['firmware_file_rx2'])
    print("config read")

    if rx2_port != 1:
        print("Incorrect configuration, rx1_port should be 2")
        sys.exit()

    bf_serial = int_serial(bf_serial_speed)
    ports = get_betaflight_serial_config(bf_serial)
    if len(ports) > 1:
        reset_serial_config(bf_serial, ports)
    
    bf_serial = int_serial(bf_serial_speed)
    change_serial_config(bf_serial, rx2_port, rx1_port)

    print("======== Update RX2 ========")
    if wait_for_uart_port(30, 1) == False:
        print("Failed to open the serial port")
        sys.exit()
    time.sleep(2)
    bf_serial = int_serial(bf_serial_speed)
    bf_serial.close
    time.sleep(1)
    if upload_esp8266_bf(upload_speed, False, False, firmware_file_rx2, target) == ElrsUploadResult.Success:
        is_rx2_updated = True
        #input("Unplug USB cable and insert back, then press enter to continue...")
        input("Витягніть і вставьте назад USB кабель...")
        time.sleep(7)
    else:
        print("Failed to update RX2")
        sys.exit()


    bf_serial = int_serial(bf_serial_speed)

    print("Set port to RX1")
    change_serial_config(bf_serial, rx1_port, rx2_port)

    print("======== Update RX1 ========")
    if wait_for_uart_port(30, 1) == False:
        print("Failed to open the serial port")
        sys.exit()
    time.sleep(2)
    bf_serial = int_serial(bf_serial_speed)
    bf_serial.close()
    time.sleep(1)
    if upload_esp8266_bf(upload_speed, False, False, firmware_file_rx1, target) == ElrsUploadResult.Success:
        print("Firmware updated successfully")
    else:
        print("Failed to update RX1")

    bf_serial.close()

