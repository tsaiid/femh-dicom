from keras.models import load_model

class CxrKerasModel():
    def __init__(self, model_cfg, weight_cfg):
        self.obj = load_model(model_cfg['path'])
        self.model_name = model_cfg['name']
        self.model_ver = model_cfg['ver']
        self.weight_name = weight_cfg['name']
        self.weight_ver = weight_cfg['ver']
        self.category = weight_cfg['category']
        self.obj.load_weights(weight_cfg['path'])
        self.width = weight_cfg['width']
        self.height = weight_cfg['height']

