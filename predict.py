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
    for model in models:
        small_img = img.resize((model.height, model.width))
        small_img = small_img.convert('L')

        # MONOCHROME
        if ds.PhotometricInterpretation == 'MONOCHROME1':
            small_img = invert(small_img)

        acc_no = ds.get('AccessionNumber', None)
        exam_time = ds.get('AcquisitionDate', None)
        small_img_arr = np.array(small_img.convert('RGB'))
        prob = predict_image(small_img_arr, model.obj)
        results.append({'model_name': model.name,
                        'model_ver': model.ver,
                        'normal_probability': prob})

    return results

def main():
    if len(sys.argv) is not 2:
        print("argv")
        sys.exit(1)

    # load cfg
    home_dir = expanduser("~")
    tmp_dir = 'Dropbox/Tmp/TF'
    yml_path = join(home_dir, tmp_dir, 'cxr.yml')
    with open(yml_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # load all models
    cxr_models = []
    for m in cfg['model']:
        for w in m['weight']:
            cxr_models.append(CxrModel(m['path'], w))

    path = sys.argv[1]
    if (isfile(path)):
        results = do_predict(cxr_models, path)
    elif (isdir(path)):
        files = listdir(path)
        for f in files:
            fullpath = join(path, f)
            if isfile(fullpath):
                results = do_predict(cxr_models, fullpath)

    # print results or write to db
    print(results)


if __name__ == "__main__":
    main()