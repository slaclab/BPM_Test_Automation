import tkinter as tk
import os
from tkinter import ttk
from tkinter import font as tkFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import fake_beam
import threading
import automatedTest
import time
import calibration
from PIL import Image, ImageTk
import vxi11
import io
import subprocess
import testResolution


amc_card_inserted = False
ioc_started = False
ioc_button_pushed = False

global Green_placeholder, Red_placeholder

def update_system_messages(message):
    # Temporarily enable the widget to update text
    system_messages.config(state='normal')
    # Insert the message at the end
    system_messages.insert('end', message + '\n')
    # Disable the widget to prevent user input
    system_messages.config(state='disabled')

# Function to be called when the Confirm button is clicked
def confirm_serial():
    entered_serial = serial_entry.get()  # Get the text from the entry widget
    serial_display.config(text=entered_serial)  # Update the display label with the serial number
    update_system_messages(f"BPM Serial Number Under Test: {entered_serial}")


def update_status(canvas, status):
    color = "green" if status else "red"
    canvas.itemconfig("status_light", fill=color)

def run_SNR():
    if serial_entry.get(): 
      update_system_messages(f"Running SNR Test...")
      output = automatedTest.SNR_Testing(serial_entry.get())
      update_system_messages(f"Test Result: ")
      for item in output:
          result = "Passed"
          if float(item[1]) <  1 or float(item[2]) < 60:
              result = "Failed"
          update_system_messages(f"Channel: {item[0]}    Power: {item[1]}    SNR Value: {item[2]}    {result}")
    else:
      update_system_messages(f"Missing Serial Number! Please Enter Serial Number and Confirm")

def run_attn():
    if serial_entry.get(): 
        update_system_messages(f"Running Attenuation Test...")
        output = automatedTest.attenuation_Testing(serial_entry.get())
        #update_system_messages(f"Attenuation Testing Result: {output}")
        automatedTest.parse_data_and_plot(serial_entry.get())
    else: 
        update_system_messages(f"Missing Serial Number! Please Enter Serial Number and Confirm")

def run_fakeBeam():
    update_system_messages(f"Running Fake Beam... Please wait")
    if automatedTest.check_ioc_session("sioc-b084-bp02"):
        output = testResolution.run_resolution()
        x_res_o = output['res_x'] * 1e3
        y_res_o = output['res_y'] * 1e3
        update_system_messages(f"Fake Beam Testing Result:\n Y-Resolution: {y_res_o} um \n X-Resolution: {x_res_o} um")
    else: 
        update_system_messages(f"IOC Not Started, please start IOC")

def check_amc_card():
    while True:
        amc_card_inserted = automatedTest.check_BPM_connection()
        if amc_card_inserted:
            update_status(canvas_amc, True)
        else:
            update_status(canvas_amc, False)
            update_status(canvas_ioc, False)
            if ioc_button_pushed:
                ioc_starting_thread.join()
                ioc_button_pushed = False
            
        time.sleep(1)

def run_restart_ioc():
    if ioc_button_pushed:
        ioc_starting_thread.join()
        ioc_button_pushed = False
        automatedTest.restart_IOC()
        

def run_start_ioc():
    automatedTest.start_IOC()
    

def call_start_ioc_thread():
    ioc_button_pushed = True
    ioc_starting_thread.start()

#Restart IOC code (no longer needed)
#def call_restart_ioc_thread():
#    ioc_starting_thread.join()
#    ioc_restarting_thread.start()
#def run_restart_ioc():
#    automatedTest.restart_IOC()


def check_ioc_status():
    while True:
        ioc_started = automatedTest.check_ioc_session("sioc-b084-bp02")
        if ioc_started:
            update_status(canvas_ioc, True)
        else:
            update_status(canvas_ioc, False)
        time.sleep(1)
 
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


def program_FRU():
    if serial_entry.get(): 
      update_system_messages(f"Programming FRU")
      automatedTest.programFRU(serial_entry.get())
      out = automatedTest.readFRU(serial_entry.get())
      update_system_messages(f'{out}')
    else:
      update_system_messages(f"Missing Serial Number! Please Enter Serial Number and Confirm")




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

def calibration():
    # Create a new window
    
    global Green_placeholder, Red_placeholder
    
    calibration_window = tk.Toplevel(root)
    calibration_window.title("Calibration Test")

    # Display instructions
    instructions = tk.Label(calibration_window, text="Follow these instructions for calibration! \n 1. Ensure that Oscilloscope Red Channel and Green Channel are connected to AMC card. \n 2. Ensure that there are 10dB attenuators installed on the oscilloscope.", wraplength=400)
    instructions.pack(pady=10)

    # Test Button
    test_button = tk.Button(calibration_window, text="Test", command=get_calibration_results)
    test_button.pack(pady=10)

    # Image placeholders
    image_frame = tk.Frame(calibration_window)
    image_frame.pack(pady=10)

    # Assuming you have placeholder images or you can leave it empty initially
    Green_placeholder = tk.Label(image_frame, text="Green Calibration Placeholder", bg="grey", width=20, height=10)
    Green_placeholder.grid(row=0, column=0, padx=10)

    Red_placeholder = tk.Label(image_frame, text="Red Calibration Placeholder", bg="grey", width=20, height=10)
    Red_placeholder.grid(row=0, column=1, padx=10)

def get_calibration_results():    
    GreenImg, RedImg = run_calibration_test()
    green_path = "test_config_green.bmp"
    red_path = "test_config_red.bmp"
    greenImg = Image.open(green_path)
    redImg = Image.open(red_path)
    greenTKImg = ImageTk.PhotoImage(greenImg)
    redTkImg = ImageTk.PhotoImage(redImg)
    Green_placeholder.configure(image=greenTKImg)
    Green_placeholder.image = greenTKImg
    Red_placeholder.configure(image=redTkImg)
    Red_placeholder.image = redTkImg


amc_card_thread = threading.Thread(target=check_amc_card)
ioc_thread = threading.Thread(target=check_ioc_status)
ioc_starting_thread = threading.Thread(target=run_start_ioc)
#ioc_restarting_thread = threading.Thread(target=run_restart_ioc)


# Create the main window
root = tk.Tk()
root.title("BPM Testing Automation")

# Set a modern font
default_font = tkFont.Font(family="Helvetica", size=12)
button_font = tkFont.Font(family="Helvetica", size=10, weight="bold")
root.option_add("*Font", default_font)

# Style Configuration
root.configure(bg='white')

# Serial Number Entry and Confirm Button
serial_frame = tk.Frame(root)
serial_frame.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky='ew')

serial_label = tk.Label(serial_frame, text="Serial Number:")
serial_label.grid(row=0, column=0)

serial_entry = tk.Entry(serial_frame)
serial_entry.grid(row=0, column=1)

confirm_button = tk.Button(serial_frame, text="Confirm", command=confirm_serial)
confirm_button.grid(row=0, column=2)

# Label to display the entered Serial Number
serial_display = tk.Label(root, text="", font=("Helvetica", 16), fg="blue")
serial_display.grid(row=1, column=0, columnspan=4, padx=10, pady=5)

# Status lights and Start IOC button
status_frame = tk.Frame(root, bg='white')
status_frame.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky='ew')

# AMC Card Status
canvas_amc = tk.Canvas(status_frame, width=20, height=20, bg='white', highlightthickness=0)
canvas_amc.create_oval(5, 5, 20, 20, fill="red", tags="status_light")
canvas_amc.grid(row=2, column=0)
label_amc = tk.Label(status_frame, text="AMC Card Status", bg='white')
label_amc.grid(row=2, column=1)

# IOC Status
canvas_ioc = tk.Canvas(status_frame, width=20, height=20, bg='white', highlightthickness=0)
canvas_ioc.create_oval(5, 5, 20, 20, fill="red", tags="status_light")
canvas_ioc.grid(row=2, column=2)
label_ioc = tk.Label(status_frame, text="IOC Status", bg='white')
label_ioc.grid(row=2, column=3)

# Start IOC Button
start_ioc_button = tk.Button(status_frame, text="Start IOC", command=call_start_ioc_thread, font=button_font)
start_ioc_button.grid(row=2, column=4)

# Re Start IOC Button (No Longer Needed)
restart_ioc_button = tk.Button(status_frame, text="Restart IOC", command=automatedTest.restart_IOC, font=button_font)
restart_ioc_button.grid(row=2, column=6)

# ProgramFRU
programFRU_button = tk.Button(status_frame, text="Program FRU", command=program_FRU, font=button_font)
programFRU_button.grid(row=2, column=8)




# Buttons for SNR, Fake Beam, and Calibration
button_snr = tk.Button(root, text="SNR, Power Test", command=run_SNR, font=button_font)
button_snr.grid(row=3, column=0, sticky="ew", padx=10, pady=10)

button_attenuation = tk.Button(root, text="Attenuation Test", command=run_attn, font=button_font)
button_attenuation.grid(row=3, column=1, sticky="ew", padx=10, pady=10)

button_fake_beam = tk.Button(root, text="Fake Beam Test", command=run_fakeBeam, font=button_font)
button_fake_beam.grid(row=3, column=2, sticky="ew", padx=10, pady=10)

button_calibration = tk.Button(root, text="Calibration Test", command=calibration, font=button_font)
button_calibration.grid(row=3, column=3, sticky="ew", padx=10, pady=10)

# Text widget for system messages
system_messages = tk.Text(root, height=10, state='disabled', wrap='word')
system_messages.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

# Scrollbar for system messages
scrollbar = tk.Scrollbar(root, command=system_messages.yview)
scrollbar.grid(row=4, column=3, sticky='nsew')
system_messages['yscrollcommand'] = scrollbar.set

# Configure the column weights to ensure equal distribution
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
# Run the application
amc_card_thread.start()
ioc_thread.start()

root.mainloop()
