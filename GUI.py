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
#ioc_started = False
#ioc_button_pushed = False

global Green_placeholder, Red_placeholder

def open_snr_window():
    """
    Function to open a new window for SNR Testing with 8 buttons (4 slots, 2 bays per slot).
    """
    # Create a new Toplevel window
    snr_window = tk.Toplevel(root)
    snr_window.title("SNR Testing")

    # Display instructions
    instructions = tk.Label(
        snr_window, 
        text="Select a slot and bay for SNR testing:", 
        font=("Arial", 14)
    )
    instructions.pack(pady=10)

    # Create a frame for the buttons
    button_frame = tk.Frame(snr_window)
    button_frame.pack(pady=10)

    # Define button labels and slots
    slot_buttons = [
        (500, 501),  # Row 1 (slot=5)
        (400, 401),  # Row 2 (slot=4)
        (300, 301),  # Row 3 (slot=3)
        (200, 201),  # Row 4 (slot=2)
    ]

    def call_snr_testing(slot_number, bay_number):
        slot = slot_number // 100
        bay = bay_number
        serial = serial_entry.get()

        if not serial:
            update_system_messages("Missing Serial Number! Please Enter Serial Number and Confirm")
            return
        
        update_system_messages(f"Running SNR Test on slot {slot}, bay {bay}...")
        output = automatedTest.SNR_Testing(serial, slot, bay)
        if not output:
            update_system_messages("No SNR Test results returned. Check the logs or device connection.")
            return

        update_system_messages("Test Result:")
        for item in output:
            channel, power, snr_val = item
            result = "Passed"
            if float(power) < 1 or float(snr_val) < 60:
                result = "Failed"
            update_system_messages(f"Channel: {channel}    Power: {power}    SNR: {snr_val}    {result}")

    # Create buttons dynamically
    for row, (left_slot, right_slot) in enumerate(slot_buttons):
        # Left button (Bay 1)
        tk.Button(
            button_frame,
            text=f"{left_slot} (Bay 1)",
            width=15,
            command=lambda s=left_slot: call_snr_testing(s, 1)
        ).grid(row=row, column=0, padx=5, pady=5)

        # Right button (Bay 0)
        tk.Button(
            button_frame,
            text=f"{right_slot} (Bay 0)",
            width=15,
            command=lambda s=right_slot: call_snr_testing(s, 0)
        ).grid(row=row, column=1, padx=5, pady=5)

    # Add a label to display messages in the new window
    display_label = tk.Label(
        snr_window, 
        text="Select a slot and bay for testing", 
        font=("Arial", 12)
    )
    display_label.pack(pady=20)


def open_attenuation_window():
    """
    Function to open a new window for Attenuation Testing with 8 buttons (4 slots, 2 bays per slot).
    """
    # Create a new Toplevel window
    attn_window = tk.Toplevel(root)
    attn_window.title("Attenuation Testing")

    # Display instructions
    instructions = tk.Label(
        attn_window, 
        text="Select a slot and bay for Attenuation testing:", 
        font=("Arial", 14)
    )
    instructions.pack(pady=10)

    # Create a frame for the buttons
    button_frame = tk.Frame(attn_window)
    button_frame.pack(pady=10)

    # Define button labels and slots in reversed order
    slot_buttons = [
        (500, 501),  # Row 1
        (400, 401),  # Row 2
        (300, 301),  # Row 3
        (200, 201),  # Row 4
    ]

    # Create buttons dynamically
    def on_attenuation_button_click(slot, bay):
        update_system_messages(f"Running Attenuation Test on slot {slot}, bay {bay}...")
        run_attn()  # Modify `run_attn()` to accept slot and bay if needed

    for row, (left_slot, right_slot) in enumerate(slot_buttons):
        tk.Button(
            button_frame,
            text=f"{left_slot} (Bay 1)",  # Bay 1 on the left
            width=15,
            command=lambda s=left_slot, b=1: on_attenuation_button_click(s, b)
        ).grid(row=row, column=0, padx=5, pady=5)

        tk.Button(
            button_frame,
            text=f"{right_slot} (Bay 0)",  # Bay 0 on the right
            width=15,
            command=lambda s=right_slot, b=0: on_attenuation_button_click(s, b)
        ).grid(row=row, column=1, padx=5, pady=5)

    # Add a label to display messages in the new window
    display_label = tk.Label(
        attn_window, 
        text="Select a slot and bay for testing", 
        font=("Arial", 12)
    )
    display_label.pack(pady=20)



def open_resolution_window():
    """
    Function to open a new window for resolution testing.
    """
    # Create a new Toplevel window
    resolution_window = tk.Toplevel(root)
    resolution_window.title("Resolution Testing")

    # Create and display buttons for testing different slots
    def on_button_click(slot):
        update_system_messages(f"Running resolution on slot {slot}...\n")
        output = run_resolution(slot=slot)
        res_x = output['res_x'] * 1e3
        res_y = output['res_y'] * 1e3
        update_system_messages(f"X Resolution: {res_x:.2f} um\nY Resolution: {res_y:.2f} um\n")

    # Create a frame for the buttons
    button_frame = tk.Frame(resolution_window)
    button_frame.pack(pady=10)

    # Define button labels and slots
    slot_buttons = [
        (500, 501),
        (400, 401),
        (300, 301),
        (200, 201),
    ]

    # Dynamically create buttons
    for row, (slot1, slot2) in enumerate(slot_buttons):
        tk.Button(button_frame, text=str(slot1), width=10, command=lambda s=slot1: on_button_click(s)).grid(row=row, column=0, padx=5, pady=5)
        tk.Button(button_frame, text=str(slot2), width=10, command=lambda s=slot2: on_button_click(s)).grid(row=row, column=1, padx=5, pady=5)

    # Add a label to display messages in the new window
    display_label = tk.Label(resolution_window, text="Select a slot for resolution testing", font=("Arial", 14))
    display_label.pack(pady=20)

def run_resolution(slot = 200, nshots=2000, edef='30', attn1_val=4, attn2_val=8, save_to_matfile=False):
    """
    Collect BPM data and compute resolutions.

    Parameters:
    - dir_name: Directory name for saving files.
    - Data_directory: Path to the data directory.
    - nshots: Number of shots to acquire (default: 2000).
    - edef: EDEF number as a string (default: '30').
    - attn1_val: Attenuation value for ATT1 (default: 6).
    - attn2_val: Attenuation value for ATT2 (default: 6).
    - save_to_matfile: Boolean to save data to a .mat file (default: False).

    Returns:
    - A dictionary containing resolutions and data arrays.
    """
    tpg_pv = 'BSA:B084:2:' + edef + ':'
    
    # Verify calibration triggers are disabled
    os.system(f'caput BPMS:B084:{slot}:CALBTCTL 0')
    
    os.system('caput ' + tpg_pv + 'MEASCNT ' + str(nshots))
    
    os.system(f'caput BPMS:B084:{slot}:ATT1 ' + str(attn1_val))
    os.system(f'caput BPMS:B084:{slot}:ATT2 ' + str(attn2_val))
    
    time.sleep(1)
    
    # Get raw_wave
    try:
        raw_wave_output = subprocess.check_output(['caget', '-a', f'BPMS:B084:{slot}:RWAV'])
        time.sleep(0.5)
        raw_wave_str = raw_wave_output.decode('utf-8')
        spaceSep = raw_wave_str.split(' ')
        raw_wave_list = spaceSep[3:-2]
        raw_wave = np.array(raw_wave_list, dtype=float)
    except subprocess.CalledProcessError as e:
        print('Error executing caget:', e)
        raw_wave = np.array([])
    
    time.sleep(0.5)
    os.system('caput ' + tpg_pv + 'RATEMODE 0')
    time.sleep(0.5)
    os.system('caput ' + tpg_pv + 'FIXEDRATE 2')
    time.sleep(0.5)
    os.system('caput ' + tpg_pv + 'MEASSEVR.VAL 2')
    time.sleep(0.5)
    os.system('caput ' + tpg_pv + 'DESTMODE 0')
    time.sleep(1)
    os.system('caput ' + tpg_pv + 'CTRL 1')
    time.sleep(0.5)
    
    # Wait for the control process to complete
    p = 1  # Initialize p to 1 to enter the loop
    while p == 1:
        try:
            p_output = subprocess.check_output(['caget', tpg_pv + 'CTRL.RVAL'])
            p_str = p_output.decode('utf-8').strip()
            p_value = float(p_str.strip().split()[-1])
            p = p_value
        except subprocess.CalledProcessError as e:
            print('Error executing caget:', e)
            p = 1
        time.sleep(1)
    
    # Get y_data
    try:
        y_data_output = subprocess.check_output(['caget', '-a', f'BPMS:B084:{slot}:YHST' + edef])
        y_data_str = y_data_output.decode('utf-8')
        y_data_lines = y_data_str.split(' ')
        y_data_list = y_data_lines[4:-2]
        y_data = np.array(y_data_list, dtype=float)
    except subprocess.CalledProcessError as e:
        print('Error executing caget:', e)
        y_data = np.array([])
    
    # Get x_data
    try:
        x_data_output = subprocess.check_output(['caget', '-a', f'BPMS:B084:{slot}:XHST' + edef])
        x_data_str = x_data_output.decode('utf-8')
        x_data_lines = x_data_str.split(' ')
        x_data_list = x_data_lines[4:-2]
        x_data = np.array(x_data_list, dtype=float)
    except subprocess.CalledProcessError as e:
        print('Error executing caget:', e)
        x_data = np.array([])
    
    # Get tmit_data
    try:
        tmit_data_output = subprocess.check_output(['caget', '-a', f'BPMS:B084:{slot}:TMITHST' + edef])
        tmit_data_str = tmit_data_output.decode('utf-8')
        tmit_data_lines = tmit_data_str.split(' ')
        tmit_data_list = tmit_data_lines[4:-2]
        tmit_data = np.array(tmit_data_list, dtype=float)
    except subprocess.CalledProcessError as e:
        print('Error executing caget:', e)
        tmit_data = np.array([])
    
    # Compute resolutions
    if len(y_data) >= nshots:
        res_y = np.std(y_data[0:nshots])
    else:
        res_y = np.nan
        print('Not enough y_data')
    
    if len(x_data) >= nshots:
        res_x = np.std(x_data[0:nshots])
    else:
        res_x = np.nan
        print('Not enough x_data')
    
    #print('mat_fname:', mat_fname)
    print('yres:', res_y * 1e3)
    print('xres:', res_x * 1e3)
    
    # Plot data
    plt.figure(1)
    if len(x_data) >= nshots and len(y_data) >= nshots:
        plt.plot(x_data[:nshots], y_data[:nshots], '*')
        plt.title('Position of beam')
        plt.xlabel('X position (um)')
        plt.ylabel('Y position (um)')
    else:
        print('Not enough data to plot')
    
    plt.figure(2)
    if len(raw_wave) > 0:
        plt.plot(raw_wave)
    else:
        print('No raw_wave data to plot')
    
    plt.show()
    
    # Return the computed resolutions and data arrays
    return {
        'res_x': res_x,
        'res_y': res_y,
        'x_data': x_data,
        'y_data': y_data,
        'tmit_data': tmit_data,
        'raw_wave': raw_wave,
    }
    
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

def run_SNR(slot=2, bay=1):
    if serial_entry.get(): 
      update_system_messages(f"Running SNR Test...")
      output = automatedTest.SNR_Testing(serial_entry.get(), slot, bay)
      update_system_messages(f"Test Result: ")
      for item in output:
          result = "Passed"
          if float(item[1]) <  1 or float(item[2]) < 60:
              result = "Failed"
          update_system_messages(f"Channel: {item[0]}    Power: {item[1]}    SNR Value: {item[2]}    {result}")
    else:
      update_system_messages(f"Missing Serial Number! Please Enter Serial Number and Confirm")

def run_attn(slot=2, bay=1):
    if serial_entry.get(): 
        update_system_messages("Running Attenuation Test...")
        output = automatedTest.attenuation_Testing(serial_entry.get(), slot, bay)
        # If needed, you can print or use `output` here.
        automatedTest.parse_data_and_plot(serial_entry.get())
    else: 
        update_system_messages("Missing Serial Number! Please Enter Serial Number and Confirm")


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
        time.sleep(1)

#def run_restart_ioc():
#    if ioc_button_pushed:
#        ioc_starting_thread.join()
#        ioc_button_pushed = False
#        automatedTest.restart_IOC()
        

#def run_start_ioc():
#    automatedTest.start_IOC()

def check_ioc1_status():
    last_status = None  # Keep track of the last known status
    while True:
        try:
            subprocess.check_output(['caget', 'BPMS:B084:200:ATT2'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ioc_started = True
        except subprocess.CalledProcessError:
            ioc_started = False
        except Exception:
            ioc_started = False
        # Only update the status indicator if the status has changed
        if ioc_started != last_status:
            update_status(canvas_ioc1, ioc_started)
            last_status = ioc_started
        time.sleep(1)

def check_ioc2_status():
    last_status = None
    while True:
        try:
            subprocess.check_output(['caget', 'BPMS:B084:300:ATT2'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ioc_started = True
        except subprocess.CalledProcessError:
            ioc_started = False
        except Exception:
            ioc_started = False
        if ioc_started != last_status:
            update_status(canvas_ioc2, ioc_started)
            last_status = ioc_started
        time.sleep(1)

def check_ioc3_status():
    last_status = None
    while True:
        try:
            subprocess.check_output(['caget', 'BPMS:B084:400:ATT2'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ioc_started = True
        except subprocess.CalledProcessError:
            ioc_started = False
        except Exception:
            ioc_started = False
        if ioc_started != last_status:
            update_status(canvas_ioc3, ioc_started)
            last_status = ioc_started
        time.sleep(1)

def check_ioc4_status():
    last_status = None
    while True:
        try:
            subprocess.check_output(['caget', 'BPMS:B084:500:ATT2'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ioc_started = True
        except subprocess.CalledProcessError:
            ioc_started = False
        except Exception:
            ioc_started = False
        if ioc_started != last_status:
            update_status(canvas_ioc4, ioc_started)
            last_status = ioc_started
        time.sleep(1)   

def call_start_ioc_thread():
    ioc_button_pushed = True
    ioc_starting_thread.start()

def open_calibration_window():
    """
    Opens a new window for calibration testing.
    """
    # Create a new Toplevel window
    calibration_window = tk.Toplevel(root)
    calibration_window.title("Calibration Testing")

    # Create and display buttons for testing different slots
    def on_calibration_button_click(slot):
        update_system_messages(f"Running calibration on slot {slot}...\n")
        output = run_calibration_test(slot)

    # Create a frame for buttons
    button_frame = tk.Frame(calibration_window)
    button_frame.pack(pady=10)

    # List of slot pairs for buttons
    slot_buttons = [
        (500, 501),
        (400, 401),
        (300, 301),
        (200, 201),
    ]

    # Create buttons dynamically
    for row, (slot1, slot2) in enumerate(slot_buttons):
        tk.Button(
            button_frame,
            text=str(slot1),
            width=10,
            command=lambda s=slot1: on_calibration_button_click(s)
        ).grid(row=row, column=0, padx=5, pady=5)

        tk.Button(
            button_frame,
            text=str(slot2),
            width=10,
            command=lambda s=slot2: on_calibration_button_click(s)
        ).grid(row=row, column=1, padx=5, pady=5)

    # Create a label to display messages
    display_label = tk.Label(calibration_window, text="Select a slot for calibration testing", font=("Arial", 14))
    display_label.pack(pady=20)

    # Create a frame to hold the Text widget and its scrollbar for system messages
    messages_frame = tk.Frame(calibration_window)
    messages_frame.pack(padx=10, pady=10, fill='both', expand=True)

    # Add scrollbar
    scrollbar = tk.Scrollbar(messages_frame)
    scrollbar.pack(side='right', fill='y')

    # Text widget for displaying system messages
    system_messages = tk.Text(messages_frame, height=10, state='disabled', wrap='word', yscrollcommand=scrollbar.set)
    system_messages.pack(side='left', fill='both', expand=True)

    # Configure the scrollbar to control the text widget
    scrollbar.config(command=system_messages.yview)


#Restart IOC code (no longer needed)
#def call_restart_ioc_thread():
#    ioc_starting_thread.join()
#    ioc_restarting_thread.start()
#def run_restart_ioc():
#    automatedTest.restart_IOC()

#
#def check_ioc_status():
#    while True:
#        ioc_started = automatedTest.check_ioc_session("sioc-b084-bp02")
#        if ioc_started:
#            update_status(canvas_ioc, True)
#        else:
#            update_status(canvas_ioc, False)
#        time.sleep(1)
 
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

def IOC_Console(number):
    """
    Runs the iocConsole command in a terminal emulator for the specified number.
    """
    # Define the command to run
    command = f"iocConsole sioc-b084-bp0{number}"

    try:
        # Use xterm for Linux environments
        subprocess.Popen(["xterm", "-hold", "-e", command])
    except FileNotFoundError:
        print("Error: 'xterm' is not installed. Please install it or specify another terminal emulator.")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")

def open_terminal_and_run_ioc(number):
    """
    Runs the siocRestart command and then opens the IOC console for a specified number.
    """
    # Construct the siocRestart command
    command1 = f"siocRestart sioc-b084-bp0{number}"

    # Run the siocRestart command directly (no terminal required)
    try:
        result = subprocess.run(command1, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Restart Command Output:\n{result.stdout.decode('utf-8')}")
    except subprocess.CalledProcessError as e:
        print(f"Restart Command Failed:\n{e.stderr.decode('utf-8')}")

    # Open the IOC console after restarting
    IOC_Console(number)




amc_card_thread = threading.Thread(target=check_amc_card)
#ioc_thread = threading.Thread(target=check_ioc_status)
#ioc_starting_thread = threading.Thread(target=run_start_ioc)
#ioc_restarting_thread = threading.Thread(target=run_restart_ioc)
ioc1_thread = threading.Thread(target=check_ioc1_status)
ioc2_thread = threading.Thread(target=check_ioc2_status)
ioc3_thread = threading.Thread(target=check_ioc3_status)
ioc4_thread = threading.Thread(target=check_ioc4_status)


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
serial_frame.grid(row=0, column=0, columnspan=6, padx=10, pady=10, sticky='ew')

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

# ProgramFRU
programFRU_button = tk.Button(status_frame, text="Program FRU", command=program_FRU, font=button_font)
programFRU_button.grid(row=2, column=8)


# Buttons for SNR, Fake Beam, and Calibration
button_snr = tk.Button(root, text="SNR, Power Test", command=open_snr_window, font=button_font)
button_snr.grid(row=3, column=0, sticky="ew", padx=10, pady=10)

button_attenuation = tk.Button(root, text="Attenuation Test", command=open_attenuation_window, font=button_font)
button_attenuation.grid(row=3, column=1, sticky="ew", padx=10, pady=10)

button_fake_beam = tk.Button(root, text="Resolution Test", command=open_resolution_window, font=button_font)
button_fake_beam.grid(row=3, column=2, sticky="ew", padx=10, pady=10)

button_calibration = tk.Button(root, text="Calibration Test", command=open_calibration_window, font=button_font)
button_calibration.grid(row=3, column=3, sticky="ew", padx=10, pady=10)

# Add a fourth button for IOC Console
button_ioc_console1 = tk.Button(root, text="sioc-b084-sp02", command=lambda: open_terminal_and_run_ioc(1), font=button_font)
button_ioc_console1.grid(row=3, column=4, sticky="ew", padx=10, pady=10)

canvas_ioc1 = tk.Canvas(root, width=20, height=20, bg='white', highlightthickness=0)
canvas_ioc1.create_oval(5, 5, 20, 20, fill="red", tags="status_light")
canvas_ioc1.grid(row=3, column=5)

label_ioc1 = tk.Label(root, text="Status", bg='white')
label_ioc1.grid(row=3, column=6)

button_ioc_console2 = tk.Button(root, text="sioc-b084-sp03", command=lambda: open_terminal_and_run_ioc(2), font=button_font)
button_ioc_console2.grid(row=4, column=4, sticky="ew", padx=10, pady=10)

canvas_ioc2 = tk.Canvas(root, width=20, height=20, bg='white', highlightthickness=0)
canvas_ioc2.create_oval(5, 5, 20, 20, fill="red", tags="status_light")
canvas_ioc2.grid(row=4, column=5)

label_ioc2 = tk.Label(root, text="Status", bg='white')
label_ioc2.grid(row=4, column=6)

button_ioc_console3 = tk.Button(root, text="sioc-b084-sp04", command=lambda: open_terminal_and_run_ioc(3), font=button_font)
button_ioc_console3.grid(row=5, column=4, sticky="ew", padx=10, pady=10)

canvas_ioc3 = tk.Canvas(root, width=20, height=20, bg='white', highlightthickness=0)
canvas_ioc3.create_oval(5, 5, 20, 20, fill="red", tags="status_light")
canvas_ioc3.grid(row=5, column=5)

label_ioc3 = tk.Label(root, text="Status", bg='white')
label_ioc3.grid(row=5, column=6)

button_ioc_console4 = tk.Button(root, text="sioc-b084-sp05", command=lambda: open_terminal_and_run_ioc(4), font=button_font)
button_ioc_console4.grid(row=6, column=4, sticky="ew", padx=10, pady=10)

canvas_ioc4 = tk.Canvas(root, width=20, height=20, bg='white', highlightthickness=0)
canvas_ioc4.create_oval(5, 5, 20, 20, fill="red", tags="status_light")
canvas_ioc4.grid(row=6, column=5)

label_ioc4 = tk.Label(root, text="Status", bg='white')
label_ioc4.grid(row=6, column=6)

# Adjust Text widget and scrollbar positions to accommodate new rows
system_messages = tk.Text(root, height=10, state='disabled', wrap='word')
system_messages.grid(row=7, column=0, columnspan=6, padx=10, pady=10, sticky="ew")

scrollbar = tk.Scrollbar(root, command=system_messages.yview)
scrollbar.grid(row=7, column=6, sticky='nsew')
system_messages['yscrollcommand'] = scrollbar.set

# Configure column weights for even distribution
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
root.grid_columnconfigure(4, weight=1)
root.grid_columnconfigure(5, weight=1)
root.grid_columnconfigure(6, weight=1)

# Run the application
amc_card_thread.start()
ioc1_thread.start()
# Start other IOC threads if implemented
ioc2_thread.start()
ioc3_thread.start()
ioc4_thread.start()

root.mainloop()
