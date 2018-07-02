import os
os.environ["GLOG_minloglevel"] = "3"
import numpy as np
import caffe
import cv2
import sys

def main():
    if len(sys.argv) is not 2:
        print("argv: png_path")
        sys.exit(1)

    caffe.set_mode_cpu()

    deploy_prototxt_file_path = 'models/caffe/quanta-1024-inception-v3-normal.prototxt'
    caffe_model_file_path = 'models/caffe/quanta-1024-inception-v3-normal.caffemodel'
    #deploy_prototxt_file_path = 'models/caffe/quanta-1024-inception-v3-cardiomegaly.prototxt'
    #caffe_model_file_path = 'models/caffe/quanta-1024-inception-v3-cardiomegaly.caffemodel'
    net = caffe.Net(deploy_prototxt_file_path, caffe_model_file_path, caffe.TEST)

    png_path = sys.argv[1]
    #图片预处理设置
    transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})  #设定图片的shape格式(1,3,28,28)
    transformer.set_transpose('data', (2,0,1))    #改变维度的顺序，由原始图片(28,28,3)变为(3,28,28)
    #transformer.set_mean('data', np.load(mean_file).mean(1).mean(1))    #减去均值，前面训练模型时没有减均值，这儿就不用
    transformer.set_raw_scale('data', 255)    # 缩放到[0，255]之间
    transformer.set_channel_swap('data', (2,1,0))   #交换通道，将图片由RGB变为BGR
    img=caffe.io.load_image(png_path)                   #加载图片
    net.blobs['data'].data[...] = transformer.preprocess('data',img)      #执行上面设置的图片预处理操作，并将图片载入到blob中

    #执行测试
    res = net.forward()

    print(res)

if __name__ == "__main__":
    main()
