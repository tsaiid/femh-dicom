#!/bin/bash

# Config
WORKDIR=/app
DCM_TMPDIR=/dcm_tmpdir
DAYS_BEFORE=1
USE_DB=1

# Script
PYTHON3=/usr/bin/python3
DCM_RETRIEVER=/app/retrieve_cxr_not_processed_dcmtk.py
KERAS_PREDICTER=/app/predict_share_img.py

cd $WORKDIR
# Start storescu
# python3 storescu.py ------ &

echo "Started at: $(TZ="Asia/Taipei" date)"

# Retrieve images
$PYTHON3 $DCM_RETRIEVER $DCM_TMPDIR $DAYS_BEFORE

# Keras model predicting
$PYTHON3 $KERAS_PREDICTER $DCM_TMPDIR $USE_DB

echo "Ended at: $(TZ="Asia/Taipei" date)"
