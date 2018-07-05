import os
os.environ["GLOG_minloglevel"] = "3"
import pandas as pd
import numpy as np
import caffe
import sys
from tqdm import tqdm

_net = None
_transformer = None

def global_caffe_init():
    global _net
    global _transformer

    caffe.set_mode_cpu()

    deploy_prototxt_file_path = 'models/caffe/quanta-1024-inception-v3-normal.prototxt'
    caffe_model_file_path = 'models/caffe/quanta-1024-inception-v3-normal.caffemodel'
    #deploy_prototxt_file_path = 'models/caffe/quanta-1024-inception-v3-cardiomegaly.prototxt'
    #caffe_model_file_path = 'models/caffe/quanta-1024-inception-v3-cardiomegaly.caffemodel'
    _net = caffe.Net(deploy_prototxt_file_path, caffe_model_file_path, caffe.TEST)

    #图片预处理设置
    _transformer = caffe.io.Transformer({'data': _net.blobs['data'].data.shape})  #设定图片的shape格式(1,3,28,28)
    _transformer.set_transpose('data', (2,0,1))    #改变维度的顺序，由原始图片(28,28,3)变为(3,28,28)
    #transformer.set_mean('data', np.load(mean_file).mean(1).mean(1))    #减去均值，前面训练模型时没有减均值，这儿就不用
    _transformer.set_raw_scale('data', 255)    # 缩放到[0，255]之间
    _transformer.set_channel_swap('data', (2,1,0))   #交换通道，将图片由RGB变为BGR

def do_forward(png_path):
    global _net
    global _transformer

    img = caffe.io.load_image(png_path)                   #加载图片
    _net.blobs['data'].data[...] = _transformer.preprocess('data', img)      #执行上面设置的图片预处理操作，并将图片载入到blob中

    #执行测试
    res = _net.forward()

    return res

def main():
    if len(sys.argv) is not 4:
        print("argv: csv_path png_dirpath csv_out_path")
        sys.exit(1)

    csv_path = sys.argv[1]
    png_dirpath = sys.argv[2]
    csv_out_path = sys.argv[3]

    # init caffe model
    global_caffe_init()

    df = pd.read_csv(csv_path)

    def _calc_prob(row):
        png_path = os.path.join(png_dirpath, row['ACCNO'] + '.png')
        res = do_forward(png_path)
        
        return res['loss3/prob'][0][1] 

    tqdm.pandas()

    df['prob'] = df.progress_apply(_calc_prob, axis=1)
    df = df.sort_values(by='prob', ascending=False)
    df.to_csv(csv_out_path, index=False)
    #print(df)

if __name__ == "__main__":
    main()
