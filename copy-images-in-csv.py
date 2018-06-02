import os
import sys
import shutil
import pandas as pd

def main():
    if len(sys.argv) is not 4:
        print("argv: csv_path source_img_path output_img_path")
        sys.exit(1)

    csv_path = sys.argv[1]
    source_img_path = sys.argv[2]
    output_img_path = sys.argv[3]

    df = pd.read_csv(csv_path)
    for index, row in df.iterrows():
        src = os.path.join(source_img_path, row['ACCNO'] + '.png')
        shutil.copy2(src, output_img_path)
        #print(src, output_img_path)
        #if index > 3:
        #    break

if __name__ == "__main__":
    main()
