import subprocess
import re
import data_processing
import os
import threading
from tkinter import filedialog
import matplotlib.pyplot as plt
import csv
import time
import numpy as np


def SNR_Testing(Serial, slot=2, bay=1):
    # Determine the appropriate YAML file based on the slot number
    if slot == 2:
        yaml_file = "000TopLevel.yaml"
    elif slot == 4:
        yaml_file = "001TopLevel.yaml"
    elif slot == 5:
        yaml_file = "002TopLevel.yaml"
    else:
        print(f"Invalid slot number: {slot}. Supported slots are 2, 4, 5.")
        return None

    # Set the bay argument (-b0 or -b1) based on the bay number
    bay_arg = f"-b{bay}"

    # Construct the command
    SNRcommand = (
        f"ssh laci@cpu-b34-bp01 'cd /afs/slac/g/lcls/users/BPM/LCLS_II/BPM/software/lcls2-py-scripts/ && "
        f"./launch.sh striplineTakeData.py -A0 -B0 -Y stripline_yaml/*_project.yaml/{yaml_file} "
        f"-D stripline_yaml/*_project.yaml/config/defaults_ss.yaml {bay_arg} -n1 -d /data/cpu-b34-bp01/bpm_data/ --forceReconfig'"
    )

    # Run the command and capture output
    SNRresult = subprocess.run(SNRcommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    file_pattern = r'\d{8}-\d{6}'

    if SNRresult.returncode == 0:
        # Decode the output and split into lines
        output_lines = SNRresult.stdout.decode().splitlines()
        # Get the last line
        last_line = output_lines[-2]
        match = re.search(file_pattern, last_line)
        if match:
            extracted_file = match.group()
            print(extracted_file)
            SCPcommand = (
                f"scp -r laci@cpu-b34-bp01:/data/cpu-b34-bp01/bpm_data/{extracted_file} ./{Serial}_{extracted_file}"
            )
            SCPcommand2 = (f"scp -r laci@cpu-b34-bp01:/data/cpu-b34-bp01/bpm_data/{extracted_file} /afs/slac.stanford.edu/g/lcls/users/BPM/LCLS_II/Data/{Serial}_{extracted_file}"
            )
            CPYresult = subprocess.run(SCPcommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            resultCP = subprocess.run(SCPcommand2, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if CPYresult.returncode == 0:
                SNR_PWR_Test_Result = data_processing.calculate_SNR_PWR(Serial, extracted_file)
                return SNR_PWR_Test_Result
            else:
                print("Issue encountered copying files, check permissions or try re-logging into your server.")
        else:
            print("Failed to extract file name from output.")
    else:
        print("Power and SNR Test Failure! Check board connection or this might be a faulty board.")
   


# Function to parse the data from the string
def parse_data_and_plot(filePath):
    remote_file = f"/afs/slac.stanford.edu/g/lcls/users/BPM/LCLS_II/Data/attn_sweep_SN{filePath}.txt"
    with open(remote_file, 'r') as file:
    	data_log = file.read()
    # Extract data using regular expression
    pattern = r"Stream(\d+):.*ATTN:\s+(\d+),\s+([-+]?[0-9]*\.?[0-9]+)db off expected attenuation"
    matches = re.findall(pattern, data_log)

    # Organize data into a dictionary
    data = {}
    for stream, attn, deviation in matches:
        attn = int(attn)
        deviation = float(deviation)
        if stream not in data:
            data[stream] = []
        data[stream].append((attn, deviation))

    # Calculate a baseline signal that goes linearly from 0 dBm at ATT 0 to -62 dBm at ATT 62
    total_attenuations = 62
    baseline_signal = np.linspace(0, -62, total_attenuations + 1)

    # Plotting the data
    plt.figure(figsize=(12, 8))

    # Adjusted signal plotting
    for stream, values in data.items():
        values.sort()  # Ensure the data is sorted by attenuation level
        attn_levels = [val[0] for val in values] if values else []
        deviations = [val[1] for val in values] if values else []
        if not attn_levels:  # Check if attn_levels is empty
            print(f"No data found for stream {stream}. Unable to plot.")
            continue

    	# Filter baseline_signal to match the attenuation levels in the data
        baseline_signal_filtered = [baseline_signal[attn] for attn in attn_levels]

	# Calculate the adjusted signal by adding deviation
        adjusted_signal = np.array(baseline_signal_filtered) + np.array(deviations)

    	# Adjusted Signal with Deviation by Stream
        plt.subplot(2, 1, 1)
        plt.plot(attn_levels, adjusted_signal, label=f'Adjusted Signal Stream {stream}')
        plt.xlabel('Attenuation Level')
        plt.ylabel('Adjusted Signal (dBm)')
        plt.title(f'C04-{filePath} Adjusted Signal with Deviation by Stream')
        plt.legend()
        plt.grid(True)

    # Deviation from Expected Attenuation by Stream
    plt.subplot(2, 1, 2)
    for stream, values in data.items():
        values.sort()  # Sort by attenuation level
        attn_levels = [val[0] for val in values] if values else []
        deviations = [val[1] for val in values] if values else []
        if not attn_levels:  # Check if attn_levels is empty
            print(f"No data found for stream {stream}. Unable to plot.")
            continue
        plt.plot(attn_levels, deviations, label=f'Deviation Stream {stream}')
        plt.xlabel('Attenuation Level')
        plt.ylabel('Deviation from Expected Attenuation (dB)')
        plt.title(f'C04-{filePath} Deviation by Stream')
        plt.legend()
        plt.grid(True)

    plt.tight_layout()
    plt.show()




def attenuation_Testing(Serial, slot=2, bay=1):
    # Determine the appropriate YAML file based on the slot number
    if slot == 2:
        yaml_file = "000TopLevel.yaml"
    elif slot == 4:
        yaml_file = "001TopLevel.yaml"
    elif slot == 5:
        yaml_file = "002TopLevel.yaml"
    else:
        print(f"Invalid slot number: {slot}. Supported slots are 2, 4, 5.")
        return None

    # Set the bay argument (-b0 or -b1) based on the bay number
    bay_arg = f"-b{bay}"

    # Construct the command for attenuation sweep
    # This command runs the `attnsweep_test.py` script remotely, stores output in /data directory
    # and tees output to a file named attn_sweep_SN<Serial>.txt.
    remote_output_file = f"attn_sweep_SN{Serial}.txt"
    ATTNcommand = (
        f"ssh laci@cpu-b34-bp01 'cd /afs/slac/g/lcls/users/BPM/LCLS_II/BPM/software/lcls2-py-scripts/ && "
        f"./launch.sh attnsweep_test.py {bay_arg} -s512 -n1 -d /data "
        f"-Y stripline_yaml/*_project.yaml/{yaml_file} 2>&1 | tee /data/cpu-b34-bp01/bpm_data/{remote_output_file}'"
    )

    # Run the attenuation sweep command and capture output
    ATTNresult = subprocess.run(ATTNcommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if ATTNresult.returncode == 0:
        # Command ran successfully
        print("Attenuation sweep completed successfully.")

        # Copy the resulting file back locally
        remote_file_path = f"/data/cpu-b34-bp01/bpm_data/{remote_output_file}"
        data_directory = "/afs/slac.stanford.edu/g/lcls/users/BPM/LCLS_II/Data"
        SCPcommand = f"scp -r laci@cpu-b34-bp01:{remote_file_path} {data_directory}"

        # Run SCP command to copy the file
        CPYresult = subprocess.run(SCPcommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if CPYresult.returncode == 0:
            print("Attenuation sweep file copied successfully.")
            # Here you could add data processing steps if needed, similar to SNR testing.
            # For example:
            # ATTN_Test_Result = data_processing.calculate_attenuation(Serial, remote_output_file)
            # return ATTN_Test_Result
            return True
        else:
            print("Error encountered copying the attenuation sweep results. Check permissions or server connection.")
            print(CPYresult.stderr.decode())
            return None
    else:
        # Command failed
        print("Attenuation sweep test failure! Check the board connection or the integrity of the script.")
        print(ATTNresult.stderr.decode())
        return None

    

def start_IOC():
    restartCommand = f"siocRestart sioc-b084-bp02"
    o = subprocess.run(restartCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    startCommand = f"iocConsole sioc-b084-bp02"
    o1 = subprocess.run(startCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print('starting IOC')
    if o1.returncode == 0:
        print('IOC Started')
    else:
        print('Issues encountered Starting IOC')
    #output_lines = iocResult.stdout.decode()
    #print(startCommand)
    #print(output_lines)
    #if iocResult == 0:
    #    print('Starting IOC...')
    #else:
    #    print('Issues encountered starting IOC')

    
def restart_IOC():
    stopCommand = f"siocRestart sioc-b084-bp02"
    iocResult = subprocess.run(stopCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if iocResult.returncode == 0:
        print('restarting IOC...')
    else:
        print('Issues encountered restarting IOC')
    

def programFRU(Serial):
    FRUCommand = f"cba_amc_init --file /afs/slac/g/lcls/users/BPM/LCLS_II/BPM/Fru/pc_379_396_03_c04.bin --serial --tag C04-{Serial} shm-b084-sp01/2/2"
    iocResult = subprocess.run(FRUCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if iocResult.returncode == 0:
        print('Programmed FRU')
    else:
        print('Issues encountered programming FRU')


def readFRU(Serial):
    FRUCommand = "cba_amc_init --dump shm-b084-sp01/2/2"
    iocResult = subprocess.run(FRUCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if iocResult.returncode == 0:
        return iocResult
    else:
        return 0
        print('Issues encountered reading FRU')

def check_BPM_connection():
    command = "cba_amc_init --dump shm-b084-sp01/2/2"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True)
    output = result.stdout
    # Initialize an empty string for the serial number
    product_serial_number = ""
    # Split the output into lines and iterate through them
    for line in output.split('\n'):
        # Check if the line contains 'Product Serial No.'
        if 'Product Serial No.' in line:
            # Extract the serial number (assuming it follows ':' and spaces)
            product_serial_number = line.split(':')[-1].strip()
            break
    if product_serial_number:
        return True
    else:
        return False


def check_ioc_session(server_name):
    # Run the screen -list command and capture its output
    screenCommand = "ssh laci@cpu-b34-bp01 'screen -ls'"
    screenResult = subprocess.run(screenCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
    output_lines = screenResult.stdout.decode()
    #print(output_lines)
    # Define the regex pattern to search for the server name
    iocPattern = fr'\b{server_name}\b.*\(Attached\)'
    if re.search(iocPattern, output_lines):
        return True
    else:
        return False

def fakeBeam_Testing():
    subprocess.run(["matlab", "-batch", "run('resolution_automated.m')"])

    # Read the output from the file
    with open('matlab_output.txt', 'r') as file:
        data = file.read()

    # Process the data
    numbers = data.split()
    number1 = float(numbers[1])
    number2 = float(numbers[3])
    out = [number1, number2]
    return out     
    
    
#serial_number = input("What's the board serial number: ")
#out = SNR_Testing(serial_number)
#print(out)
