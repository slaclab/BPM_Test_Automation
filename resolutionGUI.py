import os
import time
import numpy as np
import matplotlib.pyplot as plt
import datetime
import subprocess
import scipy.io
import tkinter as tk

def update_system_messages(message):
    # Temporarily enable the widget to update text
    system_messages.config(state='normal')
    # Insert the message at the end
    system_messages.insert('end', message + '\n')
    # Disable the widget to prevent user input
    system_messages.config(state='disabled')

def run_resolution(slot = 200, nshots=2000, edef='30', attn1_val=6, attn2_val=6, save_to_matfile=False):
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
    

def on_button_click(value):
    display_label.config(text=str(value))


root = tk.Tk()
root.title("Number Buttons")

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
    update_system_messages('Running resolution on slot 500 \n')
    output = run_resolution(slot = 500)
    res_x = output['res_x']*1e3
    res_y = output['res_y']*1e3
    update_system_messages(f'X Resolution: {res_x}\n Y Resolution: {res_y}\n')

def on_button_501():
    display_label.config(text='501')
    update_system_messages('Running resolution on slot 501 \n')
    output = run_resolution(slot = 501)
    res_x = output['res_x']*1e3
    res_y = output['res_y']*1e3
    update_system_messages(f'X Resolution: {res_x}\n Y Resolution: {res_y}\n')

def on_button_400():
    display_label.config(text='400')
    update_system_messages('Running resolution on slot 400 \n')
    output = run_resolution(slot = 400)
    res_x = output['res_x']*1e3
    res_y = output['res_y']*1e3
    update_system_messages(f'X Resolution: {res_x}\n Y Resolution: {res_y}\n')


def on_button_401():
    display_label.config(text='401')
    update_system_messages('Running resolution on slot 401 \n')
    output = run_resolution(slot = 401)
    res_x = output['res_x']*1e3
    res_y = output['res_y']*1e3
    update_system_messages(f'X Resolution: {res_x}\n Y Resolution: {res_y}\n')


def on_button_300():
    display_label.config(text='300')
    update_system_messages('Running resolution on slot 300 \n')
    output = run_resolution(slot = 300)
    res_x = output['res_x']*1e3
    res_y = output['res_y']*1e3
    update_system_messages(f'X Resolution: {res_x}\n Y Resolution: {res_y}\n')

def on_button_301():
    display_label.config(text='301')
    update_system_messages('Running resolution on slot 301 \n')
    output = run_resolution(slot = 301)
    res_x = output['res_x']*1e3
    res_y = output['res_y']*1e3
    update_system_messages(f'X Resolution: {res_x}\n Y Resolution: {res_y}\n')

def on_button_200():
    display_label.config(text='200')
    update_system_messages('Running resolution on slot 200 \n')
    output = run_resolution(slot = 200)
    res_x = output['res_x']*1e3
    res_y = output['res_y']*1e3
    update_system_messages(f'X Resolution: {res_x}\n Y Resolution: {res_y}\n')

def on_button_201():
    display_label.config(text='200')
    update_system_messages('Running resolution on slot 201 \n')
    output = run_resolution(slot = 201)
    res_x = output['res_x']*1e3
    res_y = output['res_y']*1e3
    update_system_messages(f'X Resolution: {res_x}\n Y Resolution: {res_y}\n')

# Create buttons individually and arrange them in the grid inside button_frame

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

