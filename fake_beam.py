import subprocess

# Run the MATLAB script

def test():
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