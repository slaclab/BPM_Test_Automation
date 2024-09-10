import numpy as np
from numpy.fft import fft
import scipy
from scipy.signal.windows import blackman
import os
from datetime import datetime
import math
import cmath
import bin2mat


# Define additional functions if needed, e.g., bin2mat_single_GbE, dBm2mW, mW2dBm

def calculate_SNR_PWR(Serial, file):
    colors = ['Red', 'Yellow', 'Blue', 'Green']
    out = []
    Data_directory = f'./{Serial}_{file}/'

    for i in range(4, 8):  # MATLAB 4:7 is equivalent to Python range(4, 8)
        dir_name = datetime.now().strftime('%m_%d_%Y_%H%M%S')
        directory = Data_directory

        ctrl = {"byte_reverse": 1}
        ADC = {"index": i, "bay": 0}

        ch1_fname = directory + f'Stream{ADC["index"]}_{ADC["bay"]}.bin'
        ch1_header, ch1_nFrame, ch1_data_raw = bin2mat.bin2mat(ch1_fname)
        ch1_min = np.min(ch1_data_raw)
        ch1_max = np.max(ch1_data_raw)
        #ch1_amp = ch1_max - ch1_min
        ch1_mean = np.mean(ch1_data_raw)

        fs = 370e6
        Struck_250_fs = 250e6
        ADC_FS_Vpp = 1.7
        ADC_impedance = 100
        ADC_FS_Vp = ADC_FS_Vpp / 2
        ADC_FS_Vrms = 0.707 * ADC_FS_Vp
        ADC_FS_Pmw = (1e3 * ADC_FS_Vrms ** 2) / ADC_impedance
        ADC_FS_dBm = 10 * math.log10(ADC_FS_Pmw)
        bitnum = 16
        L = len(ch1_data_raw)

        mean_data = ch1_data_raw - ch1_mean
        mean_data_max = np.max(mean_data)
        mean_data_min = np.min(mean_data)
        mean_data_amp = mean_data_max - mean_data_min
        dBFS_offset = 20 * np.log10(mean_data_max / (2 ** (bitnum - 1)))

        NFFT = 2 ** nextpow2(L + 2)
        fullscale = 2 ** (bitnum - 1)

        # Blackman window
        cc = 1 / 0.42
        w = scipy.signal.windows.blackman(L)
        data_fullscale = mean_data / fullscale
        f = fs / 2 * np.linspace(0, 1, NFFT // 2)

        rmsdata_fullscale = data_fullscale - np.mean(data_fullscale)
        Y = fft(rmsdata_fullscale * w, NFFT) * cc / L
        amp_spec = 2 * np.abs(Y[:NFFT // 2])
        amp_spec_dB = 20 * np.log10(amp_spec)

        sig_max = np.max(amp_spec[10:])
        sig_max_ind = np.where((amp_spec <= sig_max) & (amp_spec >= sig_max))[0]
        noise_array = np.concatenate([amp_spec[:sig_max_ind[0] - 20], amp_spec[sig_max_ind[0] + 20:]])

        noise_sum = np.sum(noise_array)
        noise_sum_dB = 20 * np.log10(noise_sum)
        noise_std = np.std(noise_array)
        noise_std_dB = 20 * np.log10(noise_std)

        sig_samp = 2
        sig_dBm_dist = np.zeros((sig_samp * 2 + 1, 1))
        sig_mw_dist = np.zeros((sig_samp * 2 + 1, 1))
        for j in range(sig_samp * 2 + 1):
            sig_dBm_dist[j] = ADC_FS_dBm + amp_spec_dB[sig_max_ind[0] - sig_samp + j]
            sig_mw_dist[j] = dBm2mW(sig_dBm_dist[j])

        sig_power = mW2dBm(np.sum(sig_mw_dist))
        fft_gain = 10 * np.log10(L / 2)
        sig_max_dBFS = ADC_FS_dBm + sig_power
        SNR = sig_max_dBFS - noise_std_dB - fft_gain
        out.append([colors[i-4], sig_power, SNR])

    return out

# Helper function to find next power of 2
def nextpow2(n):
    return np.ceil(np.log2(np.abs(n))).astype('int')

def dBm2mW(dBm):
    """
    Convert dBm to mW.
    
    Parameters:
    dBm (float or np.array): Power in dBm.

    Returns:
    float or np.array: Power in milliwatts.
    """
    return 10 ** (dBm / 10.0)


def mW2dBm(mW):
    """
    Convert mW to dBm.
    
    Parameters:
    mW (float or np.array): Power in milliwatts.

    Returns:
    float or np.array: Power in dBm.
    """
    if mW <= 0:
        raise ValueError("Power in mW should be greater than 0.")
    return 10.0 * math.log10(mW)


# You need to implement or translate the bin2mat_single_GbE, dBm2mW, and mW2dBm functions from MATLAB to Python as well.
