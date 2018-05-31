from os import listdir, makedirs
from os.path import isfile, isdir, join, exists, dirname
import pydicom
import csv
import sys

def do_extract(filename):
    ds = pydicom.dcmread(filename)
    dcm_tag_dict = {
        "SOP Instance UID": ds.get("SOPInstanceUID", "None"),
        "Accession Number": ds.get("AccessionNumber", "None"),
        "Patient ID": ds.get("PatientID", "None"),
        "Patient Age": ds.get("PatientAge", "None"),
        "Patient Gender": ds.get("PatientSex", "None"),
        "Study Description": ds.get("StudyDescription", "None"),
        "Normal": 1
    }
    return dcm_tag_dict

def main():
    if len(sys.argv) is not 3:
        print("argv")
        sys.exit(1)

    img_path = sys.argv[1]
    csv_path = sys.argv[2]
    csvfile_exists = isfile(csv_path)
    dcm_tag_dict_list = []

    if isfile(img_path):
        dcm_tag_dict = do_extract(img_path)
        dcm_tag_dict_list.append(dcm_tag_dict)
    elif isdir(img_path):
        files = listdir(img_path)
        for f in files:
            fullpath = join(img_path, f)
            if isfile(fullpath):
                dcm_tag_dict = do_extract(fullpath)
                dcm_tag_dict_list.append(dcm_tag_dict)

    # write csv
    if dcm_tag_dict_list:
        with open(csv_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=dcm_tag_dict_list[0].keys())
            if not csvfile_exists:
                writer.writeheader()
            for d in dcm_tag_dict_list:
                writer.writerow(d)

if __name__ == "__main__":
    main()
