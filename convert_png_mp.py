from os import listdir, makedirs
from os.path import isfile, isdir, join, exists, dirname
import pydicom
from pydicom.dataset import FileDataset
from pydicom.multival import MultiValue
import csv
import numpy as np
from PIL import Image
from PIL.ImageOps import invert
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import errno

# This function returns the data array values mapped to 0-256 using window/level parameters
#	If provided it takes into account the DICOM flags:
#	- Rescale Intercept http://dicomlookup.com/lookup.asp?sw=Tnumber&q=(0028,1052)
#	- Rescale Slope http://dicomlookup.com/lookup.asp?sw=Tnumber&q=(0028,1053)
#	Code adapted from pydicom, requires numpy
#	http://code.google.com/p/pydicom/source/browse/source/dicom/contrib/pydicom_PIL.py
def get_LUT_value(data, window, level, rescaleIntercept=0, rescaleSlope=1):
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

def read_dcm_to_image(ds_or_file):
    if isinstance(ds_or_file, FileDataset):
        ds = ds_or_file
    elif isinstance(ds_or_file, str):
        ds = pydicom.dcmread(filename)
    else:
        raise

    im_arr = ds.pixel_array

    rescale_intercept, rescale_slope = get_rescale_params(ds)
    data = get_LUT_value(im_arr, ds.WindowWidth, ds.WindowCenter, rescale_intercept, rescale_slope)
    mode = get_PIL_mode(ds)
    img = Image.fromarray(data, mode)

    return img

def do_convert(filename, img_out_path):
    ds = pydicom.dcmread(filename)
    img_an = ds.AccessionNumber

    # Debug Info
    ds_an = ds.AccessionNumber if 'AccessionNumber' in ds else None
    ds_pi = ds.PhotometricInterpretation if 'PhotometricInterpretation' in ds else None
    ds_ww = ds.WindowWidth if 'WindowWidth' in ds else None
    ds_wc = ds.WindowCenter if 'WindowCenter' in ds else None
    ds_ri = ds.RescaleIntercept if 'RescaleIntercept' in ds else None
    ds_rs = ds.RescaleSlope if 'RescaleSlope' in ds else None
    ds_uid = ds.SOPInstanceUID if 'SOPInstanceUID' in ds else None
    print(filename, "AccNo:", ds_an, "PI:", ds_pi, "WW:", ds_ww, "WC:", ds_wc, "RI:", ds_ri, "RS:", ds_rs)
    img_out_fullpath = join(img_out_path, ds_an + '.png')
    if not exists(dirname(img_out_fullpath)):
        try:
            makedirs(dirname(img_out_fullpath))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    img = read_dcm_to_image(ds)

    small_img = img.resize((1024, 1024))
    small_img = small_img.convert('L')

    # MONOCHROME
    if ds.PhotometricInterpretation == 'MONOCHROME1':
        small_img = invert(small_img)

    small_img.save(img_out_fullpath)


def main():
    if len(sys.argv) is not 3:
        print("argv")
        sys.exit(1)

    img_path = sys.argv[1]
    img_out_path = sys.argv[2]
    t_start = time.time()

    if isfile(img_path):
        do_convert(img_path, img_out_path)
    elif isdir(img_path):
        with ProcessPoolExecutor() as executor:
            files = [join(img_path, f) for f in listdir(img_path) if isfile(join(img_path, f))]

            futures = [executor.submit(do_convert, f, img_out_path) for f in files]

            for future in as_completed(futures):
                try:
                    future.result()
                    #err = future.exception()
                    #if err is not None:
                    #    raise err
                except KeyboardInterrupt:
                    # non-graceful shutdown
                    # https://gist.github.com/clchiou/f2608cbe54403edb0b13
                    print("stopped by hand")
                    executor._threads.clear()
                    concurrent.futures.thread._threads_queues.clear()

        """
        for f in files:
            fullpath = join(img_path, f)
            if isfile(fullpath):
                do_convert(fullpath, img_out_path)
        """

    t_end = time.time()
    t_total = t_end - t_start
    print("Total Time: ", t_total)


if __name__ == "__main__":
    main()
