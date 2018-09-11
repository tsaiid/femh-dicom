import numpy as np
from pydicom.multival import MultiValue

# This function returns the data array values mapped to 0-256 using window/level parameters
#	If provided it takes into account the DICOM flags:
#	- Rescale Intercept http://dicomlookup.com/lookup.asp?sw=Tnumber&q=(0028,1052)
#	- Rescale Slope http://dicomlookup.com/lookup.asp?sw=Tnumber&q=(0028,1053)
#	Code adapted from pydicom, requires numpy
#	http://code.google.com/p/pydicom/source/browse/source/dicom/contrib/pydicom_PIL.py
def get_LUT_value(data, window, level, rescaleIntercept=0, rescaleSlope=1):
    if None in [window, level, rescaleIntercept, rescaleSlope]:
        return data

    if isinstance(window, list) or isinstance(window, MultiValue):
        window = window[0]
    if isinstance(level, list) or isinstance(level, MultiValue):
        level = int(level[0])
    # some vendors use wrong rescale intercept and slope?
    if rescaleSlope == 0 and rescaleIntercept == 1:
        rescaleSlope = 1
        rescaleIntercept = 0

    return np.piecewise(data,
                        [((data * rescaleSlope) + rescaleIntercept) <= (level - 0.5 - (window - 1) / 2),
                         ((data * rescaleSlope) + rescaleIntercept) > (level - 0.5 + (window - 1) / 2)],
                        [0, 255, lambda VAL: ((((VAL * rescaleSlope) + rescaleIntercept) - (level - 0.5)) / (
                        window - 1) + 0.5) * (255 - 0)])

def get_PIL_mode(ds):
    bits = ds.BitsAllocated
    samples = ds.SamplesPerPixel
    if bits == 8 and samples == 1:
        mode = "L"
    elif bits == 8 and samples == 3:
        mode = "RGB"
    elif bits == 16:
        mode = "I;16"
    return mode

def get_rescale_params(ds):
    try:
        rescale_intercept = ds.RescaleIntercept
    except AttributeError:
        rescale_intercept = 0.0
    try:
        rescale_slope = ds.RescaleSlope
    except AttributeError:
        rescale_slope = 1.0
    return rescale_intercept, rescale_slope
