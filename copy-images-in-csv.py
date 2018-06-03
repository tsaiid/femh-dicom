import os
import sys
import errno
import shutil
import pandas as pd

def main():
    if len(sys.argv) is not 4:
        print("argv: csv_path source_img_path output_img_path")
        sys.exit(1)

    csv_path = sys.argv[1]
    source_img_path = sys.argv[2]
    output_img_path = sys.argv[3]
    had_checked_dir_exists = False

    df = pd.read_csv(csv_path)
    for index, row in df.iterrows():
        accno = row['ACCNO'].split('.png')[0]
        src = os.path.join(source_img_path, accno + '.png')

        if not had_checked_dir_exists and not os.path.exists(output_img_path):
            try:
                os.makedirs(output_img_path)
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
            else:
                had_checked_dir_exists = True

        shutil.copy2(src, output_img_path)
        print(index, src, output_img_path)
        #if index > 3:
        #    break

if __name__ == "__main__":
    main()
