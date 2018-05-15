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
from cxrmodel import CxrModel
from dcmconv import get_LUT_value, get_PIL_mode, get_rescale_params
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from cxrdbcls import CxrNormalProbability

engine = None

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
    result = None
    ds, img = read_dcm_to_image(path)
    for model in models:
        # check if exists
        acc_no = ds.get('AccessionNumber', None)
        model_name = model.model_name
        model_ver = model.model_ver
        weight_name = model.weight_name
        weight_ver = model.weight_ver
        is_exist = check_if_pred_exists(acc_no, model_name, model_ver, weight_name, weight_ver)
        if is_exist:
            continue

        small_img = img.resize((model.height, model.width))
        small_img = small_img.convert('L')

        # MONOCHROME
        if ds.PhotometricInterpretation == 'MONOCHROME1':
            small_img = invert(small_img)

        exam_time = ds.get('AcquisitionDate', None)
        small_img_arr = np.array(small_img.convert('RGB'))
        prob = predict_image(small_img_arr, model.obj)
        result = { 'acc_no': acc_no,
                    'model_name': model_name,
                    'model_ver': model_ver,
                    'weight_name': weight_name,
                    'weight_ver': weight_ver,
                    'probability': prob[0][0]  }
    return result

def check_if_pred_exists(acc_no, model_name, model_ver, weight_name, weight_ver):
    global engine
    query_str = 'select 1 ' \
                'from "ML_PREDICTIONS" ' \
                'where ACCNO = "{acc_no}" ' \
                '  and MODEL_NAME = "{model_name}" ' \
                '  and MODEL_VER = "{model_ver}" ' \
                '  and WEIGHTS_NAME = "{weight_name}" ' \
                '  and WEIGHTS_VER = "{weight_ver}";'.format(acc_no=acc_no,
                                                             model_name=model_name,
                                                             model_ver=model_ver,
                                                             weight_name=weight_name,
                                                             weight_ver=weight_ver)
    result = engine.execute(query_str)
    is_exist = result.fetchone()
    result.close()
    return True if is_exist else None

def main():
    if len(sys.argv) is not 2:
        print("argv")
        sys.exit(1)

    # load cfg
    yml_path = join('config', 'cxr.yml')
    with open(yml_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # init db engine
    global engine
    db_path = cfg['sqlite']['path']
    engine = create_engine('sqlite:///' + db_path)

    # load all models
    cxr_models = [CxrModel(m, w) for m in cfg['model'] for w in m['weight']]

    path = sys.argv[1]
    results = []
    if (isfile(path)):
        result = do_predict(cxr_models, path)
        if result:
            results.append(result)
    elif (isdir(path)):
        files = listdir(path)
        for f in files:
            fullpath = join(path, f)
            if isfile(fullpath):
                result = do_predict(cxr_models, fullpath)
                if result:
                    results.append(result)

    # print results or write to db
    print(results)
    print(len(results))
    """
    db_path = cfg['sqlite']['path']
    engine = create_engine('sqlite:///' + db_path)
    Session = sessionmaker(bind=engine)
    session = Session()
    for r in results:
        session.add(CxrNormalProbability(acc_no=r['acc_no'],
                                         model_name=r['model_name'],
                                         model_ver=r['model_ver'],
                                         normal_probability=r['normal_probability']))
        session.commit()
    session.close()
    """

if __name__ == "__main__":
    main()
