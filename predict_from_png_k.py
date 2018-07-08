import os
import numpy as np
import pandas as pd
from keras.applications.densenet import DenseNet121
from keras.models import load_model
from keras.preprocessing import image
from keras.applications.densenet import preprocess_input
from PIL import Image
import sys
from time import time

from keras.layers import Input
from keras.layers.core import Dense
from keras.models import Model

_model = None

def global_keras_init():
    global _model

    model_path = 'models/keras/cxr-binary-classifier.h5'
    weights_path = 'models/keras/weights/fake-224-densenet121-32-nipple3k.h5'
    #_model = load_model(model_path)
    #_model = DenseNet121(weights=weights_path, classes=1)
    input_shape = (224, 224, 3)
    img_input = Input(shape=input_shape)
    base_model = DenseNet121(include_top=False,
                             input_tensor=img_input,
                             input_shape=input_shape,
                             weights=None,
                             pooling="avg")
    x = base_model.output
    predictions = Dense(1, activation="sigmoid", name="predictions")(x)
    _model = Model(inputs=img_input, outputs=predictions)
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
