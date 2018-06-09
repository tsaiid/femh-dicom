import numpy as np
import caffe
import cv2
import pydicom
import time
import yaml
import cx_Oracle
import hashlib


session = None
_use_db = None
_caffe_models = None

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

    exists = session.query(MLPrediction).\
                       filter_by(ACCNO = acc_no).\
                       filter_by(MODEL_NAME = model_name).\
                       filter_by(MODEL_VER = model_ver).\
                       filter_by(WEIGHTS_NAME = weight_name).\
                       filter_by(WEIGHTS_VER = weight_ver).\
                       filter_by(CATEGORY = category).scalar()
    return exists

def do_forward(path):
    global _caffe_models
    """
    img = cv2.imread('RA02130904360389.png')
    if img.shape != (3, 1024, 1024):
        img = img.reshape(3, 1024, 1024)
    #img2 = img.reshape(-1, 3, 1024, 1024)
    res = net.forward(data = np.asarray([img]))
    """
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
            small_imgs_arr[target_size] = np.array(small_img.convert('RGB'))

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

        res = model.net.forward(small_imgs_arr[(model.width, model.height)])
        result = { 'acc_no': acc_no,
                   'model_name': model_name,
                   'model_ver': model_ver,
                   'weight_name': weight_name,
                   'weight_ver': weight_ver,
                   'category': category,
                   'probability': prob[0][0]  }
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
    global _caffe_models
    caffe.set_mode_cpu()
    _caffe_models = [CxrCaffeModel(m) for m in cfg['caffemodel']]
    print('{} models loaded.'.format(len(_caffe_models)))
    for i, m in enumerate(cxr_models):
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
        for f in files:
            fullpath = join(path, f)
            if isfile(fullpath):
                single_results = do_forward(fullpath)
                results.extend(single_results)

    t_prediction_done = time.time()
    print("Time for all predictions: ", t_prediction_done - t_models_loaded)

    print('{} done. {} results.'.format(path, len(results)))

    if _use_db:
        session.close()

if __name__ == "__main__":
    main()
