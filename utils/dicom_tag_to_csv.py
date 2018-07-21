import os
from os import listdir, makedirs
from os.path import isfile, isdir, join, exists, dirname
import pydicom
import csv
import sys
import pandas as pd
from collections import OrderedDict
from tqdm import tqdm

def do_extract(filename):
    ds = pydicom.dcmread(filename)
    dcm_tag_dict = OrderedDict({
        "SOP Instance UID": ds.get("SOPInstanceUID", "None"),
        "Accession Number": ds.get("AccessionNumber", "None"),
        "Patient ID": ds.get("PatientID", "None"),
        "Patient Age": ds.get("PatientAge", "None"),
        "Patient Gender": ds.get("PatientSex", "None"),
        "Study Description": ds.get("StudyDescription", "None"),
        "Protocol Name": ds.get("ProtocolName", "None"),
        "View Position": ds.get("ViewPosition", "None"),
        "Operators Name": ds.get("OperatorsName", "None")
    })
    return dcm_tag_dict

def main():
    if len(sys.argv) is not 3:
        print("argv: img_path csv_path")
        sys.exit(1)

    img_path = sys.argv[1]
    csv_path = sys.argv[2]
    csvfile_exists = isfile(csv_path)
    #dcm_tag_dict_list = []
    dcm_tag_df = pd.DataFrame()

    if os.path.isfile(img_path):
        dcm_tag_dict = do_extract(img_path)
        dcm_tag_dict_list.append(dcm_tag_dict)
    elif os.path.isdir(img_path):
        list_files = []
        for root, dirs, files in os.walk(img_path):
            for f in files:
                list_files.append(os.path.join(root, f))
        for fullpath in tqdm(list_files, ascii=True):
            if os.path.isfile(fullpath):
                dcm_tag_dict = do_extract(fullpath)
                if dcm_tag_df.empty:
                    dcm_tag_df = pd.DataFrame(columns = dcm_tag_dict.keys())
                dcm_tag_df = dcm_tag_df.append(dcm_tag_dict, ignore_index=True)

    # write csv
    if not dcm_tag_df.empty:
        try:
            ori_df = pd.read_csv(csv_path)
        except FileNotFoundError:
            ori_df = pd.DataFrame()
        all_df = pd.concat([ori_df, dcm_tag_df]).drop_duplicates(subset=dcm_tag_df.columns[0]).reset_index(drop=True)
        #print('ori_df: {}       dcm_tag_df: {}            all_df: {}'.format(len(ori_df), len(dcm_tag_df), len(all_df)))
        all_df.to_csv(csv_path, index=False)
        """
    if dcm_tag_dict_list:
        with open(csv_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=dcm_tag_dict_list[0].keys())
            if not csvfile_exists:
                writer.writeheader()
            for d in dcm_tag_dict_list:
                writer.writerow(d)
        """

if __name__ == "__main__":
    main()
