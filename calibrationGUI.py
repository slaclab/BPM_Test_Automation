import vxi11
from PIL import Image, ImageTk
import io
import time
import subprocess
import datetime
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import tkinter as tk

def update_system_messages(message):
    # Temporarily enable the widget to update text
    system_messages.config(state='normal')
    # Insert the message at the end
    system_messages.insert('end', message + '\n')
    # Disable the widget to prevent user input
    system_messages.config(state='disabled')

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

    # 7. Set measurements
    scope.write(':MEASure:VPP 4')


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
    
    # 7. Set measurements
    scope.write(':MEASure:VPP 2')

def enable_calibration(card):
    print('Turning on Calibration')
    en_calib_command = f"caput BPMS:B084:{card}:CALBTCTL 1"
    en_calib_result = subprocess.run(en_calib_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if en_calib_result.returncode == 0:
        print("Command executed successfully, calibration on.")
        print("Output:", en_calib_result.stdout)
    else:
        print("Command failed, failed to turn on calibration.")
        print("Error:", en_calib_result.stderr)
    
def disable_calibration(card):
    print('Turning off Calibration')
    dis_calib_command = f"caput BPMS:B084:{card}:CALBTCTL 0"
    dis_calib_result = subprocess.run(dis_calib_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if dis_calib_result.returncode == 0:
        print("Command executed successfully, calibration off.")
        print("Output:", dis_calib_result.stdout)
    else:
        print("Command failed, failed to turn off calibration.")
        print("Error:", dis_calib_result.stderr)


def run_calibration_test(card):
    oscilloscope_IP_address = "169.254.254.254"
    oscilloscope = vxi11.Instrument(oscilloscope_IP_address)
    oscilloscope.timeout = 20000
    get_oscilloscope_info(oscilloscope_IP_address)

    #turn on calibration and wait
    enable_calibration(card)
    time.sleep(1)

    # Caputure Signals from red and green channels
    config_green_channel(oscilloscope)
    time.sleep(0.5)
    oscilloscope.write(":DISPlay:DATA? BMP, GRATICULE, MONochrome")
    image_data_green = oscilloscope.read_raw()
    actual_data_green = parse_ieee4882_header(image_data_green)

    config_red_channel(oscilloscope)
    time.sleep(0.5)
    oscilloscope.write(":DISPlay:DATA? BMP, GRATICULE, MONochrome")
    image_data_red = oscilloscope.read_raw()
    actual_data_red = parse_ieee4882_header(image_data_red)
    
    #turn off calibration
    disable_calibration(card)
    current_time = datetime.datetime.now()
    filenameGrn = f'{current_time}_card_green.bmp'
    with open(filenameGrn, 'wb') as file:
        file.write(actual_data_green)

    print('Image capture saved to test_config_green.bmp')

    filenameRed = f'{current_time}_config_red.bmp'
    with open(filenameRed, 'wb') as file:
        file.write(actual_data_red)

    print('Image capture saved to test_config_red.bmp')
    
    imgRed = mpimg.imread(filenameRed)
    imgGrn = mpimg.imread(filenameGrn)
    fig, axs = plt.subplots(1,2)
    axs[0].imshow(imgRed)
    axs[0].axis('off')
    axs[1].imshow(imgGrn)
    axs[1].axis('off')
    caption = '50ns per division, RFWD = 6'
    fig.text(0.5, 0.20, caption, ha='center', fontsize=20)
    plt.show()
    return actual_data_green, actual_data_red

#run_calibration_test()
# Create buttons individually and arrange them in the grid inside button_frame
root = tk.Tk()
root.title("Calibration")

# Create a frame for the buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

# List of button values
button_values = [
    (500, 501),
    (400, 401),
    (300, 301),
    (200, 201)
]

def on_button_500():
    display_label.config(text='500')
    update_system_messages('Running calibration on slot 500 \n')
    output = run_calibration_test(500)

def on_button_501():
    display_label.config(text='501')
    update_system_messages('Running calibration on slot 501 \n')
    output = run_calibration_test(501)

def on_button_400():
    display_label.config(text='400')
    update_system_messages('Running calibration on slot 400 \n')
    output = run_calibration_test(400)


def on_button_401():
    display_label.config(text='401')
    update_system_messages('Running calibration on slot 401 \n')
    output = run_calibration_test(401)


def on_button_300():
    display_label.config(text='300')
    update_system_messages('Running calibration on slot 300 \n')
    output = run_calibration_test(300)

def on_button_301():
    display_label.config(text='301')
    update_system_messages('Running calibration on slot 301 \n')
    output = run_calibration_test(301)

def on_button_200():
    display_label.config(text='200')
    update_system_messages('Running calibration on slot 200 \n')
    output = run_calibration_test(200)

def on_button_201():
    display_label.config(text='200')
    update_system_messages('Running calibration on slot 201 \n')
    output = run_calibration_test(201)


# Row 0
button_500 = tk.Button(button_frame, text='500', width=10, command=on_button_500)
button_500.grid(row=0, column=0, padx=5, pady=5)

button_501 = tk.Button(button_frame, text='501', width=10, command=on_button_501)
button_501.grid(row=0, column=1, padx=5, pady=5)

# Row 1
button_400 = tk.Button(button_frame, text='400', width=10, command=on_button_400)
button_400.grid(row=1, column=0, padx=5, pady=5)

button_401 = tk.Button(button_frame, text='401', width=10, command=on_button_401)
button_401.grid(row=1, column=1, padx=5, pady=5)

# Row 2
button_300 = tk.Button(button_frame, text='300', width=10, command=on_button_300)
button_300.grid(row=2, column=0, padx=5, pady=5)

button_301 = tk.Button(button_frame, text='301', width=10, command=on_button_301)
button_301.grid(row=2, column=1, padx=5, pady=5)

# Row 3
button_200 = tk.Button(button_frame, text='200', width=10, command=on_button_200)
button_200.grid(row=3, column=0, padx=5, pady=5)

button_201 = tk.Button(button_frame, text='201', width=10, command=on_button_201)
button_201.grid(row=3, column=1, padx=5, pady=5)

# Create a label for displaying the button value
display_label = tk.Label(root, text="", font=("Arial", 16))
display_label.pack(padx=10, pady=10)

# Create a label for displaying the button value
display_label = tk.Label(root, text="", font=("Arial", 16))
display_label.pack(pady=20)

# Create a frame to hold the Text widget and its scrollbar
messages_frame = tk.Frame(root)
messages_frame.pack(padx=10, pady=10, fill='both', expand=True)

# Create the scrollbar
scrollbar = tk.Scrollbar(messages_frame)
scrollbar.pack(side='right', fill='y')

# Text widget for system messages
system_messages = tk.Text(messages_frame, height=10, state='disabled', wrap='word', yscrollcommand=scrollbar.set)
system_messages.pack(side='left', fill='both', expand=True)


# Configure the scrollbar to control the text widget
scrollbar.config(command=system_messages.yview)

root.mainloop()
