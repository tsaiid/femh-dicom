import os
import numpy as np
import pandas as pd
from keras.models import load_model
from keras.preprocessing import image
from keras.applications.densenet import preprocess_input
from PIL import Image
import sys
from tqdm import tqdm

_model = None

def global_keras_init():
    global _model

    model_path = 'models/keras/cxr-binary-classifier.h5'
    #weights_path = 'models/keras/weights/femh-224-densenet121-32-ekg.h5'
    #weights_path = 'models/keras/weights/femh-224-densenet121-32.h5'
    weights_path = 'models/keras/weights/femh-224-densenet121-32-standing.h5'
    _model = load_model(model_path)
    _model.load_weights(weights_path)

def do_predict(png_path):
    global _model

    try:
        img = image.load_img(png_path, target_size = (224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        preds = _model.predict(x)
    except Exception as inst:
        print(inst)
        preds = None

    return preds[0][0] if preds else None

def main():
    if len(sys.argv) is not 4:
        print("argv: csv_path png_dirpath csv_out_path")
        sys.exit(1)

    csv_path = sys.argv[1]
    png_dirpath = sys.argv[2]
    csv_out_path = sys.argv[3]

    # init Keras model
    global_keras_init()

    df = pd.read_csv(csv_path)

    def _calc_prob(row):
        png_path = os.path.join(png_dirpath, row['ACCNO'] + '.png')
        res = do_predict(png_path)

        return res or None

    tqdm.pandas()

    df['prob'] = df.progress_apply(_calc_prob, axis=1)
    df = df.sort_values(by='prob', ascending=False)
    df.to_csv(csv_out_path, index=False)
    #print(df)

if __name__ == "__main__":
    main()
