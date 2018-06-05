import os
import sys
import csv

def main():
    if len(sys.argv) is not 3:
        print("argv: start_dir output_csv_path")
        sys.exit(1)

    start_dir = sys.argv[1]
    output_csv_path = sys.argv[2]
    acc_nos = set()

    for root, dirs, files in os.walk(start_dir):
        #print(root)
        for f in files:
            acc_no = os.path.splitext(f)[0]
            acc_nos.add(acc_no)

    with open(output_csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ACCNO'])
        for acc_no in acc_nos:
            writer.writerow([acc_no])

if __name__ == "__main__":
    main()
