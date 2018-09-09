#!/bin/bash

# Config
WORKDIR=/app
DCM_TMPDIR=/dcm_tmpdir
IMG_PNG_1024_PATH=/imgsrv/png/new/1024
IMG_PNG_1500_PATH=/imgsrv/png/new/1500

# Script
PYTHON3=/usr/bin/python3
FIND=/usr/bin/find
DCM_RETRIEVER=/app/retrieve_cxr_by_datehour_dcmtk.py
CAFFE_FORWARDER=/app/convert_then_forward.py
KERAS_PREDICTER=/app/predict_share_img.py
PNG_CONVERTER=/app/convert_png_mp.py

cd $WORKDIR
# Start storescu
# python3 storescu.py ------ &

echo "Started at: $(TZ="Asia/Taipei" date)"

# Retrieve images
DATEHOUR=$(TZ="Asia/Taipei" date -d '1 hour ago' "+%Y-%m-%d %H")
$PYTHON3 $DCM_RETRIEVER $DATEHOUR $DCM_TMPDIR

# Convert 1024 png and then Caffe model forwarding
$PYTHON3 $CAFFE_FORWARDER $DCM_TMPDIR $IMG_PNG_1024_PATH 1

# Keras model predicting
$PYTHON3 $KERAS_PREDICTER $DCM_TMPDIR 1

# Convert images
## Only need to convert 1500 png. 1024 was done with Caffe forwarding
#$PYTHON3 $DCM_TMPDIR $IMG_PNG_1024_PATH 1024 1 0
$PYTHON3 $PNG_CONVERTER $DCM_TMPDIR $IMG_PNG_1500_PATH 1500 0 0

# Remove old png images > 30 days
$FIND $IMG_PNG_1024_PATH $IMG_PNG_1500_PATH -maxdepth 1 -mtime +30 -type f -delete

echo "Ended at: $(TZ="Asia/Taipei" date)"
