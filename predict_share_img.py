import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import pydicom
from pydicom.dataset import FileDataset
from PIL import Image
from PIL.ImageOps import invert
import numpy as np
from keras.models import load_model
from keras.preprocessing.image import img_to_array
from keras.applications.densenet import preprocess_input
import sys
import yaml
from app.cxrkerasmodel import CxrKerasModel
from app.dcmconv import get_LUT_value, get_PIL_mode, get_rescale_params
from app.femhdb import FemhDb
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from app.mldbcls import MLPrediction
from app.hashlib import hash_pred_id
import time
from tqdm import tqdm

session = None
_use_db = None
_keras_models = None

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

def do_predict(path):
    global _keras_models
    results = []
    ds, img = read_dcm_to_image(path)
    acc_no = ds.get('AccessionNumber', None)

    # prepare all resize
    small_imgs_arr = {}
    for model in _keras_models:
        target_size = (model.width, model.height)
        if target_size not in small_imgs_arr:
            small_img = img.resize(target_size).convert('L')
            if ds.PhotometricInterpretation == 'MONOCHROME1':
                small_img = invert(small_img)
            small_imgs_arr[target_size] = np.array(small_img.convert('RGB'))

    for model in _keras_models:
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
                #print("{} {} {} exists, skip.".format(acc_no, model_name, weight_name))
                continue

        """
        small_img = img.resize((model.width, model.height))
        small_img = small_img.convert('L')

        # MONOCHROME
        if ds.PhotometricInterpretation == 'MONOCHROME1':
            small_img = invert(small_img)
        """

        #exam_time = ds.get('AcquisitionDate', None)
        #small_img_arr = np.array(small_img.convert('RGB'))
        #prob = predict_image(small_imgs_arr[(model.width, model.height)], model.obj)
        """
        from keras demo
        """
        x = img_to_array(small_imgs_arr[(model.width, model.height)])
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        preds = model.obj.predict(x)

        result = { 'acc_no': acc_no,
                   'model_name': model_name,
                   'model_ver': model_ver,
                   'weight_name': weight_name,
                   'weight_ver': weight_ver,
                   'category': category,
                   'probability': preds[0][0]  }
        results.append(result)
    return results

def check_if_pred_exists(acc_no, model_name, model_ver, weight_name, weight_ver, category):
    global _session

    try:
        exists = _session.query(MLPrediction).\
                            filter_by(accno = acc_no).\
                            filter_by(model_name = model_name).\
                            filter_by(model_ver = model_ver).\
                            filter_by(weights_name = weight_name).\
                            filter_by(weights_ver = weight_ver).\
                            filter_by(category = category).scalar()
    except MultipleResultsFound:
        print("MultipleResultsFound: accno = {}, category = {}. Please check DB.".format(acc_no, category))
        exists = True

    return exists

def main():
    global _session
    global _use_db
    global _keras_models

    if len(sys.argv) is not 3:
        print("argv: target_path use_db")
        sys.exit(1)

    path = sys.argv[1]
    _use_db = sys.argv[2] != '0'

    t_start = time.time()

    # load cfg
    yml_path = os.path.join('config', 'cxr.yml')
    with open(yml_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    if _use_db:
        db = FemhDb()
        _session = db.session

    # load all models
    _keras_models = [CxrKerasModel(m, w) for m in tqdm(cfg['model'], ascii=True) for w in tqdm(m['weight'], ascii=True)]
    print('{} models loaded.'.format(len(_keras_models)))
    for i, m in enumerate(_keras_models):
        print("{}. {} {} {} {}".format(i, m.model_name, m.model_ver, m.weight_name, m.weight_ver))

    t_models_loaded = time.time()
    print("Time for loading models: ", t_models_loaded - t_start)

    results = []
    if (os.path.isfile(path)):
        single_results = do_predict(path)
        results.extend(single_results)
    elif (os.path.isdir(path)):
        list_files = []
        for root, dirs, files in os.walk(path):
            for f in files:
                list_files.append(os.path.join(root, f))
        for fullpath in tqdm(list_files, ascii=True):
            if os.path.isfile(fullpath):
                single_results = do_predict(fullpath)
                results.extend(single_results)

    t_prediction_done = time.time()
    print("Time for all predictions: ", t_prediction_done - t_models_loaded)

    # print results or write to db
    #print(results)
    print('{} done. {} results.'.format(path, len(results)))

    for r in results:
        if _use_db:
            _session.add(MLPrediction(  pred_id=hash_pred_id(r),
                                        accno=r['acc_no'],
                                        model_name=r['model_name'],
                                        model_ver=r['model_ver'],
                                        weights_name=r['weight_name'],
                                        weights_ver=r['weight_ver'],
                                        category=r['category'],
                                        probability=r['probability'] ))
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
