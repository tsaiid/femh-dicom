import os
os.environ["GLOG_minloglevel"] = "3"
import sys
import time
import yaml
import json
import errno

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='skimage')

import pydicom
from pydicom.dataset import FileDataset

from PIL import Image
from PIL.ImageOps import invert

import cx_Oracle
from app.mldbcls import MLPrediction
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.exc import IntegrityError, InvalidRequestError
import hashlib

from app.dcmconv import get_LUT_value, get_PIL_mode, get_rescale_params

import numpy as np
import caffe
from app.cxrcaffemodel import CxrCaffeModel

from app.femhdb import FemhDb

_session = None
_use_db = None
_caffe_models = None

def global_caffe_init(cfg):
    global _caffe_models

    caffe.set_mode_cpu()

    # load all models
    _caffe_models = [CxrCaffeModel(m) for m in cfg['caffemodel']]
    print('{} models loaded.'.format(len(_caffe_models)))
    for i, m in enumerate(_caffe_models):
        print("{}. {} {} {} {}".format(i, m.model_name, m.model_ver, m.weight_name, m.weight_ver))

def check_if_pred_exists(acc_no, model_name, model_ver, weight_name, weight_ver, category):
    global _session

    try:
        exists = _session.query(MLPrediction).\
                            filter_by(ACCNO = acc_no).\
                            filter_by(MODEL_NAME = model_name).\
                            filter_by(MODEL_VER = model_ver).\
                            filter_by(WEIGHTS_NAME = weight_name).\
                            filter_by(WEIGHTS_VER = weight_ver).scalar()
    except MultipleResultsFound:
        print("MultipleResultsFound: ACCNO = {}, CATEGORY = {}. Please check DB.".format(acc_no, category))
        exists = True

    return exists

def do_forward(ds, png_path):
    global _caffe_models
    global _use_db

    results = []
    acc_no = ds.get('AccessionNumber', None)

    for model in _caffe_models:
        # check if exists
        model_name = model.model_name
        model_ver = model.model_ver
        weight_name = model.weight_name
        weight_ver = model.weight_ver
        category = model.category

        if _use_db:
            is_exist = check_if_pred_exists(acc_no, model_name, model_ver, weight_name, weight_ver, category)
            if is_exist:
                print("{} {} {} exists, skip.".format(acc_no, model_name, weight_name))
                continue

        model.load_net()
        img = caffe.io.load_image(png_path, color=model.is_color())
        model.net.blobs['data'].data[...] = model.transformer.preprocess('data', img)
        res = model.net.forward()
        model.clear_net()   # to save memory; 1 model takes up to 3 GB
        prob = np.amax(res['loss3/prob'][0])
        label = model.labels[np.argmax(res['loss3/prob'][0])]
        result = { 'acc_no': acc_no,
                   'model_name': model_name,
                   'model_ver': model_ver,
                   'weight_name': weight_name,
                   'weight_ver': weight_ver,
                   'category': category + '-' + label,
                   'probability': prob  }

        results.append(result)
    return results

def read_dcm_to_image(ds_or_file):
    if isinstance(ds_or_file, FileDataset):
        ds = ds_or_file
        debug_name = ds.get('AccessionNumber', None)
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
    data = get_LUT_value(im_arr, ds.WindowWidth, ds.WindowCenter, rescale_intercept, rescale_slope)
    mode = get_PIL_mode(ds)
    img = Image.fromarray(data, mode)

    return img

def do_convert_then_forward(fpath, img_out_path):
    ds = pydicom.dcmread(fpath)

    # Debug Info
    ds_uid = ds.get('SOPInstanceUID', fpath)
    ds_an = ds.get('AccessionNumber', None)
    if not ds_an:
        raise ValueError('No AccessionNumber for UID: {}'.format(ds_uid))

    ds_pi = ds.get('PhotometricInterpretation', None)
    ds_ww = ds.get('WindowWidth', None)
    ds_wc = ds.get('WindowCenter', None)
    ds_ri = ds.get('RescaleIntercept', None)
    ds_rs = ds.get('RescaleSlope', None)
    #print(filename, "AccNo:", ds_an, "PI:", ds_pi, "WW:", ds_ww, "WC:", ds_wc, "RI:", ds_ri, "RS:", ds_rs)
    img_out_fullpath = os.path.join(img_out_path, ds_an + '.png')
    if not os.path.exists(os.path.dirname(img_out_fullpath)):
        try:
            os.makedirs(os.path.dirname(img_out_fullpath))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    try:
        img = read_dcm_to_image(ds)
    except:
        raise

    try:
        # always (1024, 1024, 1) png
        img_out_width_height = 1024

        small_img = img.resize((img_out_width_height, img_out_width_height))
        small_img = small_img.convert('L')

        # MONOCHROME
        if ds.PhotometricInterpretation == 'MONOCHROME1':
            small_img = invert(small_img)
    except:
        print('convert {} error.'.format(fpath))
        raise

    try:
        small_img.save(img_out_fullpath)
    except:
        print('save {} ({}) error.'.format(fpath, ds_an))
        raise

    # Do forward
    return do_forward(ds, img_out_fullpath)

def main():
    global _use_db
    global _session

    if len(sys.argv) is not 4:
        print("argv: img_path img_out_path use_db")
        sys.exit(1)

    img_path = sys.argv[1]
    img_out_path = sys.argv[2]
    _use_db = sys.argv[3] != '0'

    t_start = time.time()

    # load cfg
    yml_path = os.path.join('config', 'cxr.yml')
    with open(yml_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    if _use_db:
        db = FemhDb()
        _session = db.session

    # load all models
    global_caffe_init(cfg)
    t_models_loaded = time.time()
    print("Time for loading models: ", t_models_loaded - t_start)

    results = []
    list_files = []
    if os.path.isfile(img_path):
        list_files.append(img_path)
    elif os.path.isdir(img_path):
        for root, dirs, files in os.walk(img_path):
            for f in files:
                list_files.append(os.path.join(root, f))

    for fpath in list_files:
        try:
            single_results = do_convert_then_forward(fpath, img_out_path)
            results.extend(single_results)
        except:
            print('Convert Then Forward Error for {}'.format(fpath))
            raise

    t_prediction_done = time.time()
    print("Time for all predictions: ", t_prediction_done - t_models_loaded)

    print('{} done. {} results.'.format(img_path, len(results)))

    class MyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return super(MyEncoder, self).default(obj)

    for r in results:
        if _use_db:
            hash_pred_id = hashlib.sha256(json.dumps(r, sort_keys=True, cls=MyEncoder).encode('utf-8')).hexdigest()
            _session.add(MLPrediction(   RED_ID=hash_pred_id,
                                        ACCNO=r['acc_no'],
                                        MODEL_NAME=r['model_name'],
                                        MODEL_VER=r['model_ver'],
                                        WEIGHTS_NAME=r['weight_name'],
                                        WEIGHTS_VER=r['weight_ver'],
                                        CATEGORY=r['category'],
                                        PROBABILITY=r['probability'] ))
            try:
                _session.commit()
            except IntegrityError:
                print('sqlalchemy.exc.IntegrityError: {}'.format(r))
            except InvalidRequestError:
                _session.rollback()
                print('sqlalchemy.exc.InvalidRequestError: {}'.format(r))
        else:
            print(r)

    if _use_db:
        _session.close()

if __name__ == "__main__":
    main()
