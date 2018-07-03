import os
import sys
import cv2
import numpy as np
import pandas as pd
from PIL import Image
from skimage.transform import resize
from keras.models import load_model
from keras.preprocessing import image
from keras.applications.densenet import preprocess_input
from keras import backend as kb

def get_output_layer(model, layer_name):
    # get the symbolic outputs of each "key" layer (we gave them unique names).
    layer_dict = dict([(layer.name, layer) for layer in model.layers])
    layer = layer_dict[layer_name]
    return layer

def load_image(image_path):
    image = Image.open(image_path)
    image_array = np.asarray(image.convert("RGB"))
    image_array = image_array / 255.
    image_array = resize(image_array, (224, 224))
    return image_array

def main():
    if len(sys.argv) is not 3:
        print("argv: png_path png_out_path")
        sys.exit(1)

    model_path = 'models/keras/cxr-binary-classifier.h5'
    weights_path = 'models/keras/weights/fake-224-densenet121-32-nipple3k.h5'

    model = load_model(model_path)
    model.load_weights(weights_path)

    #png_path = '/data/RA00C31214070912.png'
    png_path = sys.argv[1]
    png_out_path = sys.argv[2]

    img_ori = cv2.imread(filename=png_path)
    img_transformed = load_image(png_path)

    # CAM overlay
    # Get the 512 input weights to the softmax.
    class_weights = model.layers[-1].get_weights()[0]
    final_conv_layer = get_output_layer(model, "bn")
    get_output = kb.function([model.layers[0].input], [final_conv_layer.output, model.layers[-1].output])
    [conv_outputs, predictions] = get_output([np.array([img_transformed])])
    conv_outputs = conv_outputs[0, :, :, :]

    # Create the class activation map.
    cam = np.zeros(dtype=np.float32, shape=(conv_outputs.shape[:2]))
    for i, w in enumerate(class_weights[0]):
        cam += w * conv_outputs[:, :, i]
    cam /= np.max(cam)
    cam = cv2.resize(cam, img_ori.shape[:2])
    heatmap = cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET)
    heatmap[np.where(cam < 0.2)] = 0
    img_out = heatmap * 0.5 + img_ori

    cv2.imwrite(png_out_path, img_out)

