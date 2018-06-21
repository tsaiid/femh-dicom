from os import listdir, makedirs
from os.path import isfile, isdir, join, exists, dirname
import pydicom
import sys

def main():
    if len(sys.argv) is not 3:
        print("argv: img_path accno")
        sys.exit(1)

    img_path = sys.argv[1]
    accno = sys.argv[2]

    if isdir(img_path):
        files = listdir(img_path)

        for f in files:
            fullpath = join(img_path, f)
            if isfile(fullpath):
                ds = pydicom.dcmread(fullpath)
                if accno == ds.get('AccessionNumber', None):
                    print('{}: {}'.format(accno, fullpath))
                    break

if __name__ == "__main__":
    main()
