import os
import time
import numpy as np
import matplotlib.pyplot as plt
import datetime
import subprocess
import scipy.io

def run_resolution(nshots=2000, edef='30', attn1_val=6, attn2_val=6, save_to_matfile=False):
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
    os.system('caput BPMS:B084:200:CALBTCTL 0')
    
    os.system('caput ' + tpg_pv + 'MEASCNT ' + str(nshots))
    
    os.system('caput BPMS:B084:200:ATT1 ' + str(attn1_val))
    os.system('caput BPMS:B084:200:ATT2 ' + str(attn2_val))
    
    time.sleep(1)
    
    # Get raw_wave
    try:
        raw_wave_output = subprocess.check_output(['caget', '-a', 'BPMS:B084:200:RWAV'])
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
        y_data_output = subprocess.check_output(['caget', '-a', 'BPMS:B084:200:YHST' + edef])
        y_data_str = y_data_output.decode('utf-8')
        y_data_lines = y_data_str.split(' ')
        y_data_list = y_data_lines[4:-2]
        y_data = np.array(y_data_list, dtype=float)
    except subprocess.CalledProcessError as e:
        print('Error executing caget:', e)
        y_data = np.array([])
    
    # Get x_data
    try:
        x_data_output = subprocess.check_output(['caget', '-a', 'BPMS:B084:200:XHST' + edef])
        x_data_str = x_data_output.decode('utf-8')
        x_data_lines = x_data_str.split(' ')
        x_data_list = x_data_lines[4:-2]
        x_data = np.array(x_data_list, dtype=float)
    except subprocess.CalledProcessError as e:
        print('Error executing caget:', e)
        x_data = np.array([])
    
    # Get tmit_data
    try:
        tmit_data_output = subprocess.check_output(['caget', '-a', 'BPMS:B084:200:TMITHST' + edef])
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
