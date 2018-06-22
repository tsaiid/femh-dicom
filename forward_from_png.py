import numpy as np
import caffe
import cv2
import sys

def main():
    if len(sys.argv) is not 3:
        print("argv: png_path")
        sys.exit(1)

    caffe.set_mode_cpu()

    deploy_prototxt_file_path = 'models/caffe/quanta-1024-inception-3a-cardiomegaly.prototxt'
    caffe_model_file_path = 'models/caffe/quanta-1024-inception-3a-cardiomegaly.caffemodel'
    net = caffe.Net(deploy_prototxt_file_path, caffe_model_file_path, caffe.TEST)

    png_path = sys.argv[1]
    img = cv2.imread(png_path)
    if img.shape != (3, 1024, 1024):
        img = img.reshape(-1, 3, 1024, 1024)
    res = net.forward(data = np.asarray([img]))
    print(res)

if __name__ == "__main__":
    main()
