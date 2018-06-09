import pydicom
from pydicom.dataset import FileDataset
from PIL import Image
from PIL.ImageOps import invert
import numpy as np
from keras.models import load_model
from keras.preprocessing.image import img_to_array
from keras.applications.densenet import preprocess_input
import sys
from os import listdir
from os.path import isfile, isdir, join, expanduser
import yaml
import json
from cxrkerasmodel import CxrKerasModel
from dcmconv import get_LUT_value, get_PIL_mode, get_rescale_params
import hashlib
import cx_Oracle
from sqlalchemy import create_engine
from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import exists
from mldbcls import MLPrediction
import time

session = None
_use_db = None

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

def predict_image(img, model):
    """
    from keras demo
    """
    x = img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    preds = model.predict(x)
    return preds

def do_predict(models, path):
    results = []
    ds, img = read_dcm_to_image(path)
    acc_no = ds.get('AccessionNumber', None)

    for model in models:
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

        small_img = img.resize((model.width, model.height))
        small_img = small_img.convert('L')

        # MONOCHROME
        if ds.PhotometricInterpretation == 'MONOCHROME1':
            small_img = invert(small_img)

        #exam_time = ds.get('AcquisitionDate', None)
        small_img_arr = np.array(small_img.convert('RGB'))
        prob = predict_image(small_img_arr, model.obj)
        result = { 'acc_no': acc_no,
                   'model_name': model_name,
                   'model_ver': model_ver,
                   'weight_name': weight_name,
                   'weight_ver': weight_ver,
                   'category': category,
                   'probability': prob[0][0]  }
        results.append(result)
    return results

def check_if_pred_exists(acc_no, model_name, model_ver, weight_name, weight_ver, category):
    global session

    exists = session.query(MLPrediction).\
                       filter_by(ACCNO = acc_no).\
                       filter_by(MODEL_NAME = model_name).\
                       filter_by(MODEL_VER = model_ver).\
                       filter_by(WEIGHTS_NAME = weight_name).\
                       filter_by(WEIGHTS_VER = weight_ver).\
                       filter_by(CATEGORY = category).scalar()
    return exists

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
        #db_path = cfg['sqlite']['path']
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
    cxr_models = [CxrKerasModel(m, w) for m in cfg['model'] for w in m['weight']]
    print('{} models loaded.'.format(len(cxr_models)))
    for i, m in enumerate(cxr_models):
        print("{}. {} {} {} {}".format(i, m.model_name, m.model_ver, m.weight_name, m.weight_ver))

    t_models_loaded = time.time()
    print("Time for loading models: ", t_models_loaded - t_start)

    path = sys.argv[1]
    results = []
    if (isfile(path)):
        single_results = do_predict(cxr_models, path)
        results.extend(single_results)
    elif (isdir(path)):
        files = listdir(path)
        for f in files:
            fullpath = join(path, f)
            if isfile(fullpath):
                single_results = do_predict(cxr_models, fullpath)
                results.extend(single_results)

    t_prediction_done = time.time()
    print("Time for all predictions: ", t_prediction_done - t_models_loaded)

    # print results or write to db
    #print(results)
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
            session.commit()
        else:
            print(r)

    if _use_db:
        session.close()

if __name__ == "__main__":
    main()
