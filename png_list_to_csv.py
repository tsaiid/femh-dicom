from os import listdir
from os.path import isfile, isdir, join
import csv
import sys

def main():
    if len(sys.argv) is not 3:
        print("argv")
        sys.exit(1)

    img_path = sys.argv[1]
    csv_path = sys.argv[2]
    #csvfile_exists = isfile(csv_path)

    if isdir(img_path):
        files = listdir(img_path)

        with open(csv_path, 'w', newline='') as csvfile:
            fieldnames = ['Image Index', 'No Finding']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for f in files:
                fullpath = join(img_path, f)
                if isfile(fullpath):
                    writer.writerow({'Image Index': f, 'No Finding': '0'})

if __name__ == "__main__":
    main()
