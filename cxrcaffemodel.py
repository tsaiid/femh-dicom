import caffe

class CxrCaffeModel():
    def __init__(self, model_cfg):
        self.prototxt_path = model_cfg['prototxt_path']
        self.model_path = model_cfg['model_path']
        self.model_name = model_cfg['model_name']
        self.model_ver = model_cfg['model_ver']
        self.weight_name = model_cfg['weight_name']
        self.weight_ver = model_cfg['weight_ver']
        self.category = model_cfg['category']
        self.labels = model_cfg['labels']
        self.width = model_cfg['width']
        self.height = model_cfg['height']

        self.net = None
        self.transformer = None

    def load_net(self):
        self.net = caffe.Net(self.prototxt_path, self.model_path, caffe.TEST)

        # init transformer
        self.transformer = caffe.io.Transformer({'data': self.net.blobs['data'].data.shape})
        self.transformer.set_transpose('data', (2,0,1))
        #self.transformer.set_mean('data', np.load(mean_file).mean(1).mean(1))
        self.transformer.set_raw_scale('data', 255)
        if (self.is_color()):
            self.transformer.set_channel_swap('data', (2,1,0))

    def clear_net(self):
        self.net = None

    def is_color(self):
        return True if (self.net.blobs['data'].data.shape[1] == 3) else False
