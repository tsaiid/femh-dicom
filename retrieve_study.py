from pynetdicom3 import AE
from pynetdicom3 import QueryRetrieveSOPClassList
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

    ae = AE(scu_sop_class=QueryRetrieveSOPClassList, ae_title=cfg['pacs']['my']['aet'])
    assoc_cf = ae.associate(cfg['pacs']['called']['ip'], cfg['pacs']['called']['port'])
    assoc_cm = ae.associate(cfg['pacs']['called']['ip'], cfg['pacs']['called']['port'])
    ds_q = Dataset()
    ds_q.AccessionNumber = acc_no
    ds_q.QueryRetrieveLevel = "SERIES"
    ds_q.Modality = ""
    responses_cf = assoc_cf.send_c_find(ds_q, query_model='P')
    for (status_cf, dataset_cf) in responses_cf:
        if status_cf.Status in (0xFF00, 0xFF01):
            modality = dataset_cf.Modality
            if modality not in ('CR', 'DX'):
                continue

            responses_cm = assoc_cm.send_c_move(dataset_cf, cfg['pacs']['my']['aet'], query_model='P')
            for (status_cm, dataset_cm) in responses_cm:
                if (status_cm.Status == 0x0):
                    pass
                else:
                    print('status: {}; dataset: {}'.format(status_cm, dataset_cm))

            """
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
            """

        elif status_cf.Status != 0x0:
            print("acc_no={}, status={}".format(acc_no, hex(status_cf.Status)))
    assoc_cf.release()
    assoc_cm.release()

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
