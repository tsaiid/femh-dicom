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

        # init transformer
        self.transformer = caffe.io.Transformer({'data': self.net.blobs['data'].data.shape})
        self.transformer.set_transpose('data', (2,0,1))
        #self.transformer.set_mean('data', np.load(mean_file).mean(1).mean(1))
        self.transformer.set_raw_scale('data', 255)
        #self.transformer.set_channel_swap('data', (2,1,0))
