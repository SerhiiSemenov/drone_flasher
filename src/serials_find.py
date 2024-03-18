import serial
import sys, glob


def serial_ports(debug=False):
    """ Lists serial port names

        :raises Exception:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    result = []
    ports = []

    try:
        from serial.tools.list_ports import comports
        if comports:
            if debug:
                print("  ** Searching flight controllers **")
            __ports = list(comports())
            for port in __ports:
                if (port.manufacturer and port.manufacturer in ['FTDI', 'Betaflight', ]) or \
                        (port.product and "STM32" in port.product) or (port.vid and port.vid == 0x0483):
                    if debug:
                        print("      > FC found from '%s'" % port.device)
                    ports.append(port.device)
    except ImportError:
        pass

    if not ports:
        if debug:
            print("  ** No FC found, find all ports **")
        else:
            print(".")

        platform = sys.platform.lower()
        if platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif platform.startswith('linux') or platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            #ports = glob.glob('/dev/tty[A-Za-z]*')
            # List all ttyACM* and ttyUSB* ports only
            ports = glob.glob('/dev/ttyACM*')
            ports.extend(glob.glob('/dev/ttyUSB*'))
        elif platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.usbmodem*')
            ports.extend(glob.glob('/dev/tty.SLAB*'))
            ports.extend(glob.glob('/dev/tty.usbserial*'))
        else:
            raise Exception('Unsupported platform')

    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException) as error:
            if "permission denied" in str(error).lower():
                raise Exception("You don't have persmission to use serial port!")
            pass
    result.reverse()
    return result

def get_serial_port(debug=False):
    result = serial_ports()
    if debug:
        print()
        print("Detected the following serial ports on this system:")
        for port in result:
            print("  %s" % port)
        print()

    if len(result) == 0:
        return None

    return result[0]

if __name__ == '__main__':
    result = get_serial_port(True)
    if result == None:
        print("No valid serial port detected or port already open")
    else:
        print("Found: %s" % (result, ))
