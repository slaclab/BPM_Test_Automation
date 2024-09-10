import vxi11
from PIL import Image, ImageTk
import io
import time
import subprocess


def get_oscilloscope_info(IP_address):
    # Initialize the VISA resource manager
    try:
        # Query the instrument identity
        idn = oscilloscope.ask("*IDN?")
        print(f"Oscilloscope IDN: {idn}")
    except:
        print(f"Failed to communicate with the oscilloscope")

# Use the VISA address from the oscilloscope's LAN settings
# oscilloscope_visa_address = "TCPIP0::169.254.254.254::inst0::INSTR"
	
#oscilloscope_IP_address = "169.254.254.254"
#oscilloscope = vxi11.Instrument(oscilloscope_IP_address)
#oscilloscope.timeout = 20000
#get_oscilloscope_info(oscilloscope_IP_address)
#oscilloscope.write(":DISPlay:DATA? BMP, GRATICULE, MONochrome")

# Initialize an empty byte string to hold the image data

#config_green_channel(oscilloscope)

#image_data = oscilloscope.read_raw()

def parse_ieee4882_header(data):
    # Assuming `data` starts with the '#' character
    if data[0] != ord('#'):
        raise ValueError("Data does not start with '#' character.")

    # n: the number of digits specifying the length of the data block
    n = int(chr(data[1]))

    # d: the length of the data block, specified by the next n digits
    d_length = int(data[2:2+n].decode())

    # The actual binary data starts after the '#' character, n digit, and the d_length digits
    start_of_data = 2 + n
    
    return data[start_of_data:start_of_data+d_length]

def config_red_channel(scope):
    scope.write(':CHANnel4:DISPlay ON')
    time.sleep(0.05)
    scope.write(':CHANnel4:OFFSet 0')  # Assuming 0 is the center. Adjust as per your oscilloscope's documentation.
    time.sleep(0.05)

    # 2. Set channel 2 to 50 ohm impedance
    scope.write(':CHANnel4:IMPedance FIFTy')
    time.sleep(0.05)

    # 3. Turn off channel 1, 3, and 4
    scope.write(':CHANnel1:DISPlay OFF')
    time.sleep(0.05)
    scope.write(':CHANnel2:DISPlay OFF')
    time.sleep(0.05)

    scope.write(':CHANnel3:DISPlay OFF')
    time.sleep(0.05)

    # 4. Set voltage division on channel 2 to 1V per division
    scope.write(':CHANnel4:SCALe 1')
    time.sleep(0.05)
    scope.write(':TRIGger:SOURce CHANnel4')
    time.sleep(0.05)
    # 5. Set trigger to 0.5V on channel 2
    scope.write(':TRIGger[:EDGE]:LEVel 0.5,CHANnel4')
    time.sleep(0.05)

    # 6. Set time division to 50 ns per division
    scope.write(':TIMebase:SCALe 50E-9')
    time.sleep(0.05)


def config_green_channel(scope):
    scope.write('CHANnel2:DISPlay ON')
    time.sleep(0.05)

    #set p-p measurement

    scope.write(':CHANnel2:OFFSet 0')  # Assuming 0 is the center. Adjust as per your oscilloscope's documentation.
    time.sleep(0.05)

    # 2. Set channel 2 to 50 ohm impedance
    scope.write(':CHANnel2:IMPedance FIFTy')
    time.sleep(0.05)

    # 3. Turn off channel 1, 3, and 4
    scope.write(':CHANnel1:DISPlay OFF')
    time.sleep(0.05)

    scope.write(':CHANnel3:DISPlay OFF')
    time.sleep(0.05)

    scope.write(':CHANnel4:DISPlay OFF')
    time.sleep(0.05)

    # 4. Set voltage division on channel 2 to 1V per division
    scope.write(':CHANnel2:SCALe 1')
    time.sleep(0.05)
    scope.write(':TRIGger:SOURce CHANnel2')
    time.sleep(0.05)
    # 5. Set trigger to 0.5V on channel 2
    scope.write(':TRIGger[:EDGE]:LEVel 0.5,CHANnel2')
    time.sleep(0.05)

    # 6. Set time division to 50 ns per division
    scope.write(':TIMebase:SCALe 50E-9')
    time.sleep(0.05)

def enable_calibration():
    print('Turning on Calibration')
    en_calib_command = "caput BPMS:B084:200:CALBTCTL 1"
    en_calib_result = subprocess.run(en_calib_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if en_calib_result.returncode == 0:
        print("Command executed successfully, calibration on.")
        print("Output:", en_calib_result.stdout)
    else:
        print("Command failed, failed to turn on calibration.")
        print("Error:", en_calib_result.stderr)
    
def disable_calibration():
    print('Turning off Calibration')
    dis_calib_command = "caput BPMS:B084:200:CALBTCTL 0"
    dis_calib_result = subprocess.run(dis_calib_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if dis_calib_result.returncode == 0:
        print("Command executed successfully, calibration off.")
        print("Output:", dis_calib_result.stdout)
    else:
        print("Command failed, failed to turn off calibration.")
        print("Error:", dis_calib_result.stderr)


def run_calibration_test():
    oscilloscope_IP_address = "169.254.254.254"
    oscilloscope = vxi11.Instrument(oscilloscope_IP_address)
    oscilloscope.timeout = 20000
    get_oscilloscope_info(oscilloscope_IP_address)

    #turn on calibration and wait
    enable_calibration()
    time.sleep(1)

    # Caputure Signals from red and green channels
    config_green_channel(oscilloscope)
    oscilloscope.write(":DISPlay:DATA? BMP, GRATICULE, MONochrome")
    image_data_green = oscilloscope.read_raw()
    actual_data_green = parse_ieee4882_header(image_data_green)

    config_red_channel(oscilloscope)
    oscilloscope.write(":DISPlay:DATA? BMP, GRATICULE, MONochrome")
    image_data_red = oscilloscope.read_raw()
    actual_data_red = parse_ieee4882_header(image_data_red)
    
    #turn off calibration
    disable_calibration()
    
    filename = 'test_config_green.bmp'
    with open(filename, 'wb') as file:
        file.write(actual_data_green)

    print('Image capture saved to test_config_green.bmp')

    filename = 'test_config_red.bmp'
    with open(filename, 'wb') as file:
        file.write(actual_data_red)

    print('Image capture saved to test_config_red.bmp')
    
    return actual_data_green, actual_data_red

#run_calibration_test()
