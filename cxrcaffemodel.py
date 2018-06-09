import caffe

class CxrCaffeModel():
    def __init__(self, model_cfg):
        self.net = caffe.Net(model_cfg['prototxt_path'], model_cfg['model_path'], caffe.TEST)
        self.model_name = model_cfg['model_name']
        self.model_ver = model_cfg['model_ver']
        self.weight_name = model_cfg['weight_name']
        self.weight_ver = model_cfg['weight_ver']
        self.category = model_cfg['category']
        self.width = model_cfg['width']
        self.height = model_cfg['height']
