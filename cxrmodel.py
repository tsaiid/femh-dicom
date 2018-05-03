from keras.models import load_model

class CxrModel():
    def __init__(self, h5_path, weight_cfg):
        self.obj = load_model(h5_path)
        self.name = weight_cfg['name']
        self.ver = weight_cfg['ver']
        self.obj.load_weights(weight_cfg['path'])
        self.height = weight_cfg['height']
        self.width = weight_cfg['width']