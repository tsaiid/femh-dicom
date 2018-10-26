import os
os.environ["GLOG_minloglevel"] = "2"
import pandas as pd
import numpy as np
import caffe
import cv2
import sys
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module='skimage')

_net = None
_transformer = None

def global_caffe_init():
    global _net
    global _transformer

    #caffe.set_mode_cpu()
    caffe.set_mode_gpu()

    deploy_prototxt_file_path = 'SSD_FEMH_pneumothorax_0823.prototxt'
    caffe_model_file_path = 'SSD_FEMH_pneumothorax_0823.caffemodel'
    mean_file_path = 'ChestXRay_mean0704.npy'
    _net = caffe.Net(deploy_prototxt_file_path, caffe_model_file_path, caffe.TEST)

    #图片预处理设置
    _transformer = caffe.io.Transformer({'data': _net.blobs['data'].data.shape})  #设定图片的shape格式(1,3,28,28)
    _transformer.set_transpose('data', (2,0,1))    #改变维度的顺序，由原始图片(28,28,3)变为(3,28,28)
    _transformer.set_mean('data', np.array([104,117,123]))
    #_transformer.set_mean('data', np.load(mean_file_path).mean(1).mean(1))    #减去均值，前面训练模型时没有减均值，这儿就不用
    _transformer.set_raw_scale('data', 255)    # 缩放到[0，255]之间
    _transformer.set_channel_swap('data', (2,1,0))   #交换通道，将图片由RGB变为BGR

def do_forward(png_path, conf_threshold):
    global _net
    global _transformer

    #_net.blobs['data'].reshape(1,3,500,500)
    img = caffe.io.load_image(png_path)                   #加载图片
    _net.blobs['data'].data[...] = _transformer.preprocess('data', img)      #执行上面设置的图片预处理操作，并将图片载入到blob中

    #执行测试
    detections = _net.forward()['detection_out']
    det_label = detections[0,0,:,1]
    det_conf = detections[0,0,:,2]
    det_xmin = detections[0,0,:,3]
    det_ymin = detections[0,0,:,4]
    det_xmax = detections[0,0,:,5]
    det_ymax = detections[0,0,:,6]

    top_indices = [i for i, conf in enumerate(det_conf) if conf >= conf_threshold]
    top_conf = det_conf[top_indices]
    top_label_indices = det_label[top_indices].tolist()
    top_xmin = det_xmin[top_indices]
    top_ymin = det_ymin[top_indices]
    top_xmax = det_xmax[top_indices]
    top_ymax = det_ymax[top_indices]

    f = lambda x: True if 0 <= x <= 1024 else False

    res = []
    for i in range(top_conf.shape[0]):
        xmin = int(round(top_xmin[i] * 1024))
        ymin = int(round(top_ymin[i] * 1024))
        xmax = int(round(top_xmax[i] * 1024))
        ymax = int(round(top_ymax[i] * 1024))
        score = top_conf[i]
        label = int(top_label_indices[i])
        if f(xmin) and f(ymin) and f(xmax) and f(ymax):
            res.append((png_path, label, score, xmin, ymin, xmax, ymax))

    return res

def main():
    if len(sys.argv) is not 3:
        print("argv: conf_threshold png_path")
        sys.exit(1)

    conf_threshold = float(sys.argv[1])
    path = sys.argv[2]

    # init caffe model
    global_caffe_init()

    results = []
    if (os.path.isfile(path)):
        single_results = do_forward(path, conf_threshold)
        results.extend(single_results)
    elif (os.path.isdir(path)):
        list_files = []
        for root, dirs, files in os.walk(path):
            for f in files:
                list_files.append(os.path.join(root, f))
        for fullpath in tqdm(list_files, ascii=True):
            if os.path.isfile(fullpath):
                single_results = do_forward(fullpath, conf_threshold)
                results.extend(single_results)

    for r in results:
        print(r)
    #np.set_printoptions(precision=3)

if __name__ == "__main__":
    main()
