import os
import numpy as np
import pandas as pd
from keras.models import load_model
from keras.preprocessing import image
from keras.applications.densenet import preprocess_input
from PIL import Image
import sys
from time import time

_model = None

def global_keras_init():
    global _model

    model_path = 'models/keras/cxr-binary-classifier.h5'
    weights_path = 'models/keras/weights/fake-224-densenet121-32-nipple3k.h5'
    _model = load_model(model_path)
    _model.load_weights(weights_path)

def do_predict(png_path):
    global _model

    img = image.load_img(png_path, target_size = (224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    preds = _model.predict(x)

    return preds 

def main():
    if len(sys.argv) is not 2:
        print("argv: png_path")
        sys.exit(1)

    png_path = sys.argv[1]

    t_start = time()

    # init Keras model
    global_keras_init()

    t_models_loaded = time()
    print("Time for loading models: ", t_models_loaded - t_start)

    res = do_predict(png_path)
        
    print(res)

    t_prediction_done = time()
    print("Time for all predictions: ", t_prediction_done - t_models_loaded)

if __name__ == "__main__":
    main()
