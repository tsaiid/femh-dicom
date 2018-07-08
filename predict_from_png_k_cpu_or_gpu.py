import os
import numpy as np
import pandas as pd

import tensorflow as tf
from keras import backend as K

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

def keras_config():
    num_cores = 4
    config = tf.ConfigProto(intra_op_parallelism_threads=num_cores,
                            inter_op_parallelism_threads=num_cores, allow_soft_placement=True,
                            device_count = {'CPU': 1, 'GPU': 0})
    session = tf.Session(config=config)
    K.set_session(session)

def global_keras_init():
    global _model

    model_path = 'models/keras/cxr-binary-classifier.h5'
    weights_path = 'models/keras/weights/fake-224-densenet121-32-nipple3k.h5'
    #_model = load_model(model_path)
    #_model = DenseNet121(weights=weights_path, classes=1)
    t1 = time()
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
    t2 = time()
    print("Time for loading model: ", t2 - t1)
    _model.load_weights(weights_path)
    t3 = time()
    print("Time for loading weights: ", t3 - t2)

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
    keras_config()
    global_keras_init()

    t_models_loaded = time()
    print("Time for loading models: ", t_models_loaded - t_start)

    res = do_predict(png_path)
        
    print(res)

    t_prediction_done = time()
    print("Time for all predictions: ", t_prediction_done - t_models_loaded)

if __name__ == "__main__":
    main()
