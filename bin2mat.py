import numpy as np




def bin2mat(fname):
    # Open the file and read data as 16-bit integers
    with open(fname, 'rb') as fp:
        x = np.fromfile(fp, dtype=np.int16)

    # Convert the first 4 int16 values to uint8
    header = x[:4].astype(np.uint8)

    # Calculate nFrame (considering Python's 0-based indexing)
    nFrame = header[1] * 16 + header[0] // 16

    # The rest of the data
    data = x[4:]

    return header, nFrame, data