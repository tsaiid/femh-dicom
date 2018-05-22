import yaml
import os
import sys
from . import retrieve_study

def main():
    if len(sys.argv) < 2:
        print
        sys.exit("no argv")

    # load cfg
    yml_path = os.path.join('config', 'pacs.yml')
    with open(yml_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)


    #acc_no = "RA04810941530099"
    acc_no = sys.argv[1]
    output_dir = sys.argv[2]

    retrieve_study(cfg, acc_no, output_dir)


if __name__ == "__main__":
    main()