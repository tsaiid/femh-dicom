from os import listdir, makedirs
from os.path import isfile, isdir, join, exists, dirname
import pydicom

img_path = 'abnormal_3'
img_out_path = 'abnormal_png'
#csv_path = 'abnormal.csv'
#csvfile_exists = isfile(csv_path)

files = listdir(img_path)

counter = 1

#with open(csv_path, 'a', newline='') as csvfile:
#fieldnames = ['Image Index', 'No Finding']
#writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

#if not csvfile_exists:
    #writer.writeheader()

for f in files:
    fullpath = join(img_path, f)
    if isfile(fullpath):
        ds = pydicom.dcmread(fullpath)
        img_an = ds.AccessionNumber
        #img_out_fullpath = join(img_out_path, img_an + '.png')
        #if not exists(dirname(img_out_fullpath)):
        #    try:
        #        makedirs(dirname(img_out_fullpath))
        #    except OSError as exc: # Guard against race condition
        #        if exc.errno != errno.EEXIST:
        #            raise

        # Window Center & Width
        window_center = ds.WindowCenter
        window_width = ds.WindowWidth

        print(counter, "\t", f, "AccNo:", ds.AccessionNumber, "WW:", ds.WindowWidth, "WC:", ds.WindowCenter, "RI:", ds.RescaleIntercept, "RS:", ds.RescaleSlope)

    counter += 1
    #if counter > 30:
    #    break

