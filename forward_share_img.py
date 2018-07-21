import os
os.environ["GLOG_minloglevel"] = "3"
import numpy as np
import caffe
import cv2
from PIL import Image
from PIL.ImageOps import invert
import pydicom
from pydicom.dataset import FileDataset
import time
import yaml
import json
import cx_Oracle
from mldbcls import MLPrediction
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from os import listdir
from os.path import isfile, isdir, join, expanduser
import sys
import hashlib
from cxrcaffemodel import CxrCaffeModel
from dcmconv import get_LUT_value, get_PIL_mode, get_rescale_params
from tqdm import tqdm

session = None
_use_db = None
_caffe_models = None
_transformer = None

def read_dcm_to_image(ds_or_file):
    if isinstance(ds_or_file, FileDataset):
        ds = ds_or_file
    elif isinstance(ds_or_file, str):
        ds = pydicom.dcmread(ds_or_file)
    else:
        raise

    im_arr = ds.pixel_array

    rescale_intercept, rescale_slope = get_rescale_params(ds)
    data = get_LUT_value(im_arr, ds.WindowWidth, ds.WindowCenter, rescale_intercept, rescale_slope)
    mode = get_PIL_mode(ds)
    img = Image.fromarray(data, mode)

    return ds, img

def check_if_pred_exists(acc_no, model_name, model_ver, weight_name, weight_ver, category):
    global session

    try:
        exists = session.query(MLPrediction).\
                            filter_by(ACCNO = acc_no).\
                            filter_by(MODEL_NAME = model_name).\
                            filter_by(MODEL_VER = model_ver).\
                            filter_by(WEIGHTS_NAME = weight_name).\
                            filter_by(WEIGHTS_VER = weight_ver).\
                            filter_by(CATEGORY = category).scalar()
    except MultipleResultsFound:
        print("MultipleResultsFound: ACCNO = {}, CATEGORY = {}. Please check DB.".format(acc_no, category))
        exists = True

    return exists

def do_forward(path):
    global _caffe_models
    global _transformer

    results = []
    ds, img = read_dcm_to_image(path)
    acc_no = ds.get('AccessionNumber', None)

    # prepare all resize
    small_imgs_arr = {}
    for model in _caffe_models:
        target_size = (model.width, model.height)
        if target_size not in small_imgs_arr:
            small_img = img.resize(target_size).convert('L')
            if ds.PhotometricInterpretation == 'MONOCHROME1':
                small_img = invert(small_img)
            _transformer = caffe.io.Transformer({'data': model.net.blobs['data'].data.shape})
            _transformer.set_transpose('data', (2,0,1))
            #_transformer.set_mean('data', np.load(mean_file).mean(1).mean(1))
            _transformer.set_raw_scale('data', 255)
            #_transformer.set_channel_swap('data', (2,1,0))
            #small_imgs_arr[target_size] = _transformer.preprocess('data', np.array(small_img.convert('RGB')).astype(np.float32))
            small_img_arr = np.array(small_img).astype(np.float32)
            if small_img_arr.ndim == 2:
                small_img_arr = small_img_arr[:, :, np.newaxis]
            small_imgs_arr[target_size] = _transformer.preprocess('data', small_img_arr)

    for model in _caffe_models:
        # check if exists
        model_name = model.model_name
        model_ver = model.model_ver
        weight_name = model.weight_name
        weight_ver = model.weight_ver
        category = model.category

        global _use_db
        if _use_db:
            is_exist = check_if_pred_exists(acc_no, model_name, model_ver, weight_name, weight_ver, category)
            if is_exist:
                print("{} {} {} exists, skip.".format(acc_no, model_name, weight_name))
                continue

        model.net.blobs['data'].data[...] = small_imgs_arr[(model.width, model.height)]
        res = model.net.forward()
        result = { 'acc_no': acc_no,
                   'model_name': model_name,
                   'model_ver': model_ver,
                   'weight_name': weight_name,
                   'weight_ver': weight_ver,
                   'category': category,
                   'probability': res['loss3/prob'][0][1]  }

        results.append(result)
    return results

def main():
    if len(sys.argv) is not 3:
        print("argv: target_path use_db")
        sys.exit(1)

    global _use_db
    _use_db = sys.argv[2] != '0'

    t_start = time.time()

    # load cfg
    yml_path = join('config', 'cxr.yml')
    with open(yml_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    if _use_db:
        # init db engine
        global session
        oracle_conn_str = 'oracle+cx_oracle://{username}:{password}@{dsn_str}'
        dsn_str = cx_Oracle.makedsn(cfg['oracle']['ip'], cfg['oracle']['port'], cfg['oracle']['service_name']).replace('SID', 'SERVICE_NAME')
        engine = create_engine(
            oracle_conn_str.format(
                username=cfg['oracle']['username'],
                password=cfg['oracle']['password'],
                dsn_str=dsn_str
            )
        )
        Session = sessionmaker(bind=engine)
        session = Session()

    # load all models
    global _caffe_models
    caffe.set_mode_cpu()
    _caffe_models = [CxrCaffeModel(m) for m in tqdm(cfg['caffemodel'], ascii=True)]
    print('{} models loaded.'.format(len(_caffe_models)))
    for i, m in enumerate(_caffe_models):
        print("{}. {} {} {} {}".format(i, m.model_name, m.model_ver, m.weight_name, m.weight_ver))

    t_models_loaded = time.time()
    print("Time for loading models: ", t_models_loaded - t_start)

    path = sys.argv[1]
    results = []
    if (isfile(path)):
        single_results = do_forward(path)
        results.extend(single_results)
    elif (isdir(path)):
        files = listdir(path)
        for f in tqdm(files, ascii=True):
            fullpath = join(path, f)
            if isfile(fullpath):
                single_results = do_forward(fullpath)
                results.extend(single_results)

    t_prediction_done = time.time()
    print("Time for all predictions: ", t_prediction_done - t_models_loaded)

    print('{} done. {} results.'.format(path, len(results)))

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
            session.add(MLPrediction(   RED_ID=hash_pred_id,
                                        ACCNO=r['acc_no'],
                                        MODEL_NAME=r['model_name'],
                                        MODEL_VER=r['model_ver'],
                                        WEIGHTS_NAME=r['weight_name'],
                                        WEIGHTS_VER=r['weight_ver'],
                                        CATEGORY=r['category'],
                                        PROBABILITY=r['probability'] ))
            try:
                session.commit()
            except IntegrityError:
                print('sqlalchemy.exc.IntegrityError: {}'.format(r))
            except InvalidRequestError:
                session.rollback()
                print('sqlalchemy.exc.InvalidRequestError: {}'.format(r))
        else:
            print(r)

    if _use_db:
        session.close()

if __name__ == "__main__":
    main()
