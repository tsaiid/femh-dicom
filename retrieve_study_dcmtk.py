from pynetdicom3 import AE, QueryRetrievePresentationContexts
from pydicom.dataset import Dataset
import yaml
import os
import sys
import errno

def retrieve_study(cfg, acc_no, output_dir):
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    ae = AE(ae_title=cfg['pacs']['my']['aet'])
    ae.requested_contexts = QueryRetrievePresentationContexts
    assoc = ae.associate(cfg['pacs']['called']['ip'], cfg['pacs']['called']['port'])
    ds = Dataset()
    ds.AccessionNumber = acc_no
    ds.QueryRetrieveLevel = "SERIES"
    ds.Modality = ""
    responses = assoc.send_c_find(ds, query_model='P')
    for (status, dataset) in responses:
        if status.Status in (0xFF00, 0xFF01):
            modality = dataset.Modality
            if modality not in ('CR', 'DX'):
                continue

            p_id = dataset.PatientID
            study_uid = dataset.StudyInstanceUID
            series_uid = dataset.SeriesInstanceUID

            cmd_str = r'''movescu {pacs_ip} {pacs_port} +P {port} +xa -aec {pacs_aet} -aet {aet} \
                          -k QueryRetrieveLevel=SERIES \
                          -k PatientID={p_id} \
                          -k StudyInstanceUID={study_uid} \
                          -k SeriesInstanceUID={series_uid} \
                          -od {output_dir} \
                        '''.format( pacs_ip=cfg['pacs']['called']['ip'], pacs_port=cfg['pacs']['called']['port'], pacs_aet=cfg['pacs']['called']['aet'],
                                    aet=cfg['pacs']['my']['aet'], port=cfg['pacs']['my']['port'],
                                    p_id=p_id, study_uid=study_uid, series_uid=series_uid,
                                    output_dir=output_dir )
            #print(cmd_str)
            os.system(cmd_str)
            #print("Success. acc_no={}".format(acc_no))
        elif status.Status != 0x0:
            print("acc_no={}, status={}".format(acc_no, hex(status.Status)))
    assoc.release()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("argv: acc_no output_dir")

    # load cfg
    yml_path = os.path.join('config', 'pacs.yml')
    with open(yml_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)


    #acc_no = "RA04810941530099"
    acc_no = sys.argv[1]
    output_dir = sys.argv[2]

    retrieve_study(cfg, acc_no, output_dir)
