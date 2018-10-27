import yaml
import os
import sys
from datetime import datetime
import cx_Oracle
from sqlalchemy import create_engine
from retrieve_study_dcmtk import retrieve_study

def main():
    if len(sys.argv) < 3:
        print
        sys.exit("argv: output_dir days_before")

    # load cfg
    yml_path = os.path.join('config', 'cxr.yml')
    with open(yml_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    output_dir = sys.argv[1]
    days_before = int(sys.argv[2])

    # get worklist of cxr on the target date
    oracle_conn_str = 'oracle+cx_oracle://{username}:{password}@{dsn_str}'
    dsn_str = cx_Oracle.makedsn(cfg['oracle']['ip'],
                                cfg['oracle']['port'],
                                cfg['oracle']['service_name']).replace('SID', 'SERVICE_NAME')
    engine_wl = create_engine(
        oracle_conn_str.format(
            username=cfg['oracle']['username'],
            password=cfg['oracle']['password'],
            dsn_str=dsn_str
        )
    )
    #Session = sessionmaker(bind=engine)
    #session = Session()
    sql_get_worklist = '''
SELECT  w.accno,
        TO_CHAR(w.examdate, 'yyyy-mm-dd hh24:mi:ss') examdate
FROM
    (   SELECT risworklistdatas.accno, examdate
        FROM risworklistdatas
        LEFT JOIN
            (SELECT accno, weights_name, probability FROM risml_predictions
            ) p
        ON risworklistdatas.accno = p.accno
            AND weights_name = 'quanta-1024-normal-30k'
        WHERE
            examcode IN ('RA014', 'RA015', 'RA016', 'RA017', 'RA018', 'RA021')
            AND
            examdate BETWEEN
                TO_DATE( TO_CHAR( SYSDATE-{days_before}, 'yyyy-mm-dd' ), 'yyyy-mm-dd' )
                    AND
                TO_DATE( TO_CHAR( SYSDATE, 'yyyy-mm-dd' ) || ' 23:59:59', 'yyyy-mm-dd hh24:mi:ss' )
            AND
            datastatus NOT IN ('RPTVS', 'RPTCR', 'DC')
            AND
            probability IS NULL
        ORDER BY examdate
    ) w
WHERE
    ROWNUM <= 1000
    '''.format(days_before=days_before)
    results = engine_wl.execute(sql_get_worklist)
    cxr_list = [{'accno': row['accno'], 'examdate': row['examdate']} for row in results]
    cxr_total = len(cxr_list)
    print('Start retrieving CXR... Total: {cxr_total}'.format(cxr_total=cxr_total))
    for i, cxr in enumerate(cxr_list):
        print('{}/{}\t{}\t{}'.format(i, cxr_total, cxr['accno'], cxr['examdate']))
        retrieve_study(cfg, cxr['accno'], output_dir)

if __name__ == "__main__":
    main()
