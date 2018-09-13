from os import listdir, makedirs
from os.path import isfile, isdir, join, exists, dirname
import os
import pydicom
from pydicom.dataset import FileDataset
from pydicom.multival import MultiValue
from app.dcmconv import get_LUT_value, get_PIL_mode, get_rescale_params
import csv
import numpy as np
from PIL import Image
from PIL.ImageOps import invert
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import errno
from app.mptqdm import parallel_process

def read_dcm_to_image(ds_or_file):
    if isinstance(ds_or_file, FileDataset):
        ds = ds_or_file
        debug_name = ds.get('AccessionNumber', 'No AccNo available')
    elif isinstance(ds_or_file, str):
        ds = pydicom.dcmread(ds_or_file)
        debug_name = ds_or_file
    else:
        raise

    try:
        im_arr = ds.pixel_array
    except AttributeError as e:
        print('{}: ds.pixel_array error. {}'.format(debug_name, str(e)))

    rescale_intercept, rescale_slope = get_rescale_params(ds)
    width = ds.get('WindowWidth', None)
    center = ds.get('WindowCenter', None)
    data = get_LUT_value(im_arr, width, center, rescale_intercept, rescale_slope)
    mode = get_PIL_mode(ds)
    img = Image.fromarray(data, mode)

    return img

def do_convert(filename, img_out_path, img_out_width=1024, img_out_square=True, use_ori_fname=False):
    ori_fname = os.path.splitext(os.path.basename(filename))[0]
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
    #print(filename, "AccNo:", ds_an, "PI:", ds_pi, "WW:", ds_ww, "WC:", ds_wc, "RI:", ds_ri, "RS:", ds_rs)
    out_fname = ds_an if ds_an and not use_ori_fname else ori_fname
    img_out_fullpath = join(img_out_path, out_fname + '.png')
    if not exists(dirname(img_out_fullpath)):
        try:
            makedirs(dirname(img_out_fullpath))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    try:
        img = read_dcm_to_image(ds)
    except:
        return

    # calculate resize image width/height
    img_width, img_height = img.size
    img_out_width = int(img_out_width)
    if img_out_square:
        img_out_height = img_out_width
    else:
        img_out_height = int( img_out_width / float(img_width) * float(img_height) )

    small_img = img.resize((img_out_width, img_out_height))
    small_img = small_img.convert('L')

    # MONOCHROME
    if ds.PhotometricInterpretation == 'MONOCHROME1':
        small_img = invert(small_img)

    small_img.save(img_out_fullpath)


def main():
    if len(sys.argv) is not 6:
        print("argv: img_path img_out_path img_out_width img_out_square use_ori_fname")
        sys.exit(1)

    img_path = sys.argv[1]
    img_out_path = sys.argv[2]
    img_out_width = int(sys.argv[3])
    img_out_square = sys.argv[4] != '0'
    use_ori_fname = sys.argv[5] != '0'
    t_start = time.time()

    if isfile(img_path):
        do_convert(img_path, img_out_path, img_out_width, img_out_square)
    elif isdir(img_path):
        files = [join(img_path, f) for f in listdir(img_path) if isfile(join(img_path, f))]
        arr = [{'filename': f, 'img_out_path': img_out_path, 'img_out_width': img_out_width, 'img_out_square': img_out_square} for f in files]
        parallel_process(arr, do_convert, use_kwargs=True)

    t_end = time.time()
    t_total = t_end - t_start
    print("Total Time: ", t_total)


if __name__ == "__main__":
    main()
