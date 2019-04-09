import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import numpy as np
import pandas as pd
from keras.models import load_model
from keras.preprocessing import image
from keras.applications.densenet import preprocess_input
from PIL import Image
import sys
from time import time
from tqdm import tqdm

_model = None

def global_keras_init():
    global _model

    model_path = 'models/keras/cxr-binary-classifier.h5'
    weights_path = 'models/keras/weights/femh-224-densenet121-32-left-hand-best.h5'
    _model = load_model(model_path)
    _model.load_weights(weights_path)

def do_predict(png_path):
    global _model

    img = image.load_img(png_path, target_size = (224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    preds = _model.predict(x)

    result = [{ 'png_path': png_path,
                'probability': preds[0][0]  }]

    return result

def main():
    if len(sys.argv) is not 2:
        print("argv: png_or_dir_path")
        sys.exit(1)

    png_or_dir_path = sys.argv[1]

    t_start = time()

    # init Keras model
    global_keras_init()

    t_models_loaded = time()
    print("Time for loading models: ", t_models_loaded - t_start)

    results = []
    if (os.path.isfile(png_or_dir_path)):
        single_results = do_predict(png_or_dir_path)
        results.extend(single_results)
    elif (os.path.isdir(png_or_dir_path)):
        list_files = []
        for root, dirs, files in os.walk(png_or_dir_path):
            for f in files:
                list_files.append(os.path.join(root, f))
        for fullpath in tqdm(list_files, ascii=True):
            if os.path.isfile(fullpath):
                single_results = do_predict(fullpath)
                results.extend(single_results)

    #print(results)
    for r in results:
        if r['probability'] > 0.5:
            print(r)

    t_prediction_done = time()
    print("Time for all predictions: ", t_prediction_done - t_models_loaded)

if __name__ == "__main__":
    main()
