#!/bin/bash

# Config
DCM_TMPDIR=/dcm_tmpdir
IMG_PNG_1024_PATH=/imgsrv/png/1024
IMG_PNG_1500_PATH=/imgsrv/png/1500

# Start storescu
python3 storescu.py ------ &

# Retrieve images
DATEHOUR=date -d '1 hour ago' "+%Y-%m-%d %H"
retrieve_cxr_by_date_hour.py $DATEHOUR $DCM_TMPDIR

# Caffe model forwarding
python3 forward_share_img.py $DCM_TMPDIR 1

# Keras model predicting
python3 predict_share_img.py $DCM_TMPDIR 1

# Convert images
python3 convert_png_mp.py $DCM_TMPDIR $IMG_PNG_1024_PATH 1024 1
python3 convert_png_mp.py $DCM_TMPDIR $IMG_PNG_1500_PATH 1024 0
