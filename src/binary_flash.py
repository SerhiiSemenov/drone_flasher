#!/usr/bin/python
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
import subprocess

sys.path.append(dirname(__file__) + '/external/esptool')
sys.path.append(dirname(__file__) + "/external")
from external.esptool import esptool

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

def upload_esp32_bf(baud, force:bool, erase:bool, file_name:str, firmware:str):
    port = serials_find.get_serial_port()
    if port == None:
        port = serials_find.get_serial_port()
    mode = 'upload'
    if force == True:
        mode = 'uploadforce'
    retval = BFinitPassthrough.main(['-p', port, '-b', str(baud), '-r', firmware, '-a', mode, '-t', 'ESP32'])
    if retval != ElrsUploadResult.Success:
        return retval
    try:
        esptool.main(['--passthrough', '--chip', 'esp32', '--port', port, '--baud', str(baud), '--before', 'no_reset', '--after', 'hard_reset', 'write_flash', '-z', '--flash_mode', 'dio', '--flash_freq', '40m', '--flash_size', 'detect', '0x10000', file_name])
    except:
        return ElrsUploadResult.ErrorGeneral
    return ElrsUploadResult.Success

def upload_rx_firmware(baud, force:bool, erase:bool, file_name:str, firmware:str):
    if firmware == "Unified_ESP8285_900_RX_via_BetaflightPassthrough":
        return upload_esp8266_bf(baud, force, erase, file_name, firmware)
    elif firmware == "Unified_ESP32_900_RX_via_BetaflightPassthrough":
        return upload_esp32_bf(baud, force, erase, file_name, firmware)
    else:
        print("Error: Unsupported target")
        return None

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
    if wait_for_uart_port(30, 1) == False:
        print(f"!Серіал порт не знайдено: {print_line_number()}")
        sys.exit()
    else:
        print("Serial port detected")

    time.sleep(1)
    port = serials_find.get_serial_port()
    if port == None:
        print(f"!Серіал порт не знайдено: {port}")
        wait_for_uart_port(30, 1)
        port = serials_find.get_serial_port()
        if port == None:
            print(f"!Серіал порт не знайдено з другої спроби: {port}")
            os._exit(1)

    try:
        ser = serial.Serial(port, baud_rate, timeout=1)
        print(f"Serial port found: {port}")
        time.sleep(0.3)
        ser.write("#\n".encode())
        ser.flush()
        ser.readlines()

    except serial.SerialException as e:
        print(f"Error occurred while communicating with the flight controller: {e}")
        sys.exit()
    return ser

def change_serial_config(bf_serial, uart_number_to_set, uart_number_to_reset):
    print("Changing serial cinfigurattion...")
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

def upload_fc_config(serial_port, config_file_path):
    i = 0
    with open(config_file_path, 'r') as conf_file:
        lines = conf_file.readlines()
        for line in lines:
            i = i+1
            line = line.strip()
            if line and not line.startswith('#'):
                serial_port.write((line + "\n").encode())
                time.sleep(0.3)
                if i % 10 == 0:
                    print(".")
    
    print("Configuration uploaded successfully!")
    serial_port.write(("save" + "\n").encode())
    time.sleep(0.3)
    serial_port.close()
    time.sleep(3)

def reboot_to_bootloader_fc(serial_port):
    serial_port.write(("bl"+ "\n").encode())

def print_line_number():
    # Get the frame object for the caller's stack frame
    frame = inspect.currentframe()
    # Get the line number where the function is called
    return frame.f_back.f_lineno

def main():
    is_rx1_updated = False
    is_rx2_updated = False
    upload_speed = 420000
    bf_serial_speed = 115200

    print("Starting binary flash")
    config = parse_config_file()
    rx1_port = config['rx1_port'] - 1
    rx2_port = config['rx2_port'] - 1
    target = config['target']
    is_dual_rx = config['dual_rx']
    is_config_upload = config['upload_config']
    is_upload_fc_firmware = config['upload_fc_firmware']

    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), config['config_file'])
    firmware_file_rx1 = os.path.join(os.path.dirname(os.path.dirname(__file__)), config['firmware_file_rx1'])
    firmware_file_rx2 = os.path.join(os.path.dirname(os.path.dirname(__file__)), config['firmware_file_rx2'])
    firmware_file_fc = os.path.join(os.path.dirname(os.path.dirname(__file__)), config['firmware_file_fc'])
    fc_flash_command = ["dfu-util", "-a", "0", "-D", firmware_file_fc, "-s", ":leave"]
    print("Config read done")

    if is_upload_fc_firmware == True:
        print("FC firmware loading...")
        bf_serial = int_serial(bf_serial_speed)
        reboot_to_bootloader_fc(bf_serial)
        time.sleep(2)
        subprocess.run(fc_flash_command, check=True)
    
    if is_config_upload == True:
        print("FC configuration loading...")
        bf_serial = int_serial(bf_serial_speed)
        upload_fc_config(bf_serial, config_file)
        time.sleep(2)
        #Waite for FC to reboot
        if wait_for_uart_port(30, 1) == False:
            print(f"!Серіал порт не знайдено: {print_line_number()}")
            sys.exit()

        print("RXs firmware loading...")
    if is_dual_rx == True:
        if rx2_port != 1:
            print("Не вірна конфігурація, rx2_port має дорівнювати 2")
            sys.exit()

        bf_serial = int_serial(bf_serial_speed)
        ports = get_betaflight_serial_config(bf_serial)
        if len(ports) > 1:
            reset_serial_config(bf_serial, ports)
        
        bf_serial = int_serial(bf_serial_speed)
        change_serial_config(bf_serial, rx2_port, rx1_port)

        print("======== Update RX2 ========")
        if wait_for_uart_port(30, 1) == False:
            print(f"!Серіал порт не знайдено: {print_line_number()}")
            sys.exit()
        else:
            print("Port detected")
        time.sleep(2)
        bf_serial = int_serial(bf_serial_speed)
        bf_serial.close
        time.sleep(1)
        if upload_rx_firmware(upload_speed, False, False, firmware_file_rx2, target) == ElrsUploadResult.Success:
            is_rx2_updated = True
            #input("Unplug USB cable and insert back, then press enter to continue...")
            input("\n!Витягніть і вставьте назад USB кабель...")
            time.sleep(7)
        else:
            print("Failed to update RX2")
            sys.exit()

        bf_serial = int_serial(bf_serial_speed)
        print("Set port to RX1")
        change_serial_config(bf_serial, rx1_port, rx2_port)

    print("======== Update RX1 ========")
    if wait_for_uart_port(30, 1) == False:
        print(f"!Серіал порт не знайдено: {print_line_number()}")
        sys.exit()
    else:
        print("Port detected")
    time.sleep(2)
    bf_serial = int_serial(bf_serial_speed)
    bf_serial.close()
    time.sleep(1)
    if upload_rx_firmware(upload_speed, False, False, firmware_file_rx1, target) == ElrsUploadResult.Success:
        print("Firmware updated successfully")
    else:
        print("Failed to update RX1")

    bf_serial.close()


if __name__ == '__main__':
    main()
