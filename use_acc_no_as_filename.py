from os import listdir, makedirs
from os.path import isfile, isdir, join, exists, dirname
import pydicom
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

def do_rename(filename, img_out_path):
    ds = pydicom.dcmread(filename)
    img_an = ds.AccessionNumber
    img_out_fullpath = join(img_out_path, img_an + '.dcm')
    if not exists(dirname(img_out_fullpath)):
        try:
            makedirs(dirname(img_out_fullpath))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    ds.save_as(img_out_fullpath)
    print(filename, "->", img_an)

def main():
    if len(sys.argv) is not 3:
        print("argv")
        sys.exit(1)

    img_path = sys.argv[1]
    img_out_path = sys.argv[2]
    t_start = time.time()

    if isfile(img_path):
        do_rename(img_path, img_out_path)
    elif isdir(img_path):
        files = listdir(img_path)

        for f in files:
            fullpath = join(img_path, f)
            if isfile(fullpath):
                do_rename(fullpath, img_out_path)

    t_end = time.time()
    t_total = t_end - t_start
    print("Total Time: ", t_total)


if __name__ == "__main__":
    main()
