import vxi11
from PIL import Image
import io

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
	

oscilloscope_IP_address = "169.254.254.254"

oscilloscope = vxi11.Instrument(oscilloscope_IP_address)
oscilloscope.timeout = 20000

get_oscilloscope_info(oscilloscope_IP_address)

oscilloscope.write(":DISPlay:DATA? BMP, GRATICULE, MONochrome")

# Initialize an empty byte string to hold the image data
image_data = oscilloscope.read_raw()

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
    return d_length, start_of_data

d_length, start_of_data = parse_ieee4882_header(image_data)
actual_data = image_data[start_of_data:start_of_data+d_length]


# The oscilloscope might send the BMP file in chunks. 
# We need to read each chunk until we have the whole file.
# This is just an example; your oscilloscope may require a different approach to read all data.
# Now, write the BMP data to a file
filename = 'oscilloscope_screen_capture.bmp'
with open(filename, 'wb') as file:
    file.write(actual_data)

#image = Image.open(io.BytesIO(image_data))


#try: 
#    image = Image.open(io.BytesIO(image_data))
#    image.save('OSC_capture.png')
#    print('Image capture saved')
#except IOError:
#    print('Could not read image data')


print('Image capture saved to oscilloscope_capture.bmp')


