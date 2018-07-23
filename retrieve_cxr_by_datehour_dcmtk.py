import yaml
import os
import sys
from datetime import datetime
import cx_Oracle
from sqlalchemy import create_engine
from retrieve_study_dcmtk import retrieve_study

def try_parsing_date_hour(text):
    try:
        dt = datetime.strptime(text, '%Y-%m-%d %H')
        start_date = dt.strftime('%Y-%m-%d')
        start_hour = dt.strftime('%H')
        return (start_date, start_hour)
    except:
        pass
    raise ValueError('no valid date format found')

def main():
    if len(sys.argv) < 4:
        print
        sys.exit("argv: date hour output_dir")

    # load cfg
    yml_path = os.path.join('config', 'cxr.yml')
    with open(yml_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # parse date str
    datehour_str = sys.argv[1] + ' ' + sys.argv[2]
    start_date, start_hour = try_parsing_date_hour(datehour_str)
    output_dir = sys.argv[3]

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
    (   SELECT accno, examdate
        FROM risworklistdatas
        WHERE
            examcode IN ('RA014', 'RA015', 'RA016', 'RA017', 'RA018', 'RA021')
            AND
            examdate BETWEEN
                TO_DATE( '{start_date} {start_hour}:00:00', 'yyyy-mm-dd hh24:mi:ss' )
                    AND
                TO_DATE( '{start_date} {start_hour}:59:59', 'yyyy-mm-dd hh24:mi:ss' )
        ORDER BY examdate
    ) w
WHERE
    ROWNUM <= 20000
    '''.format(start_date=start_date, start_hour=start_hour)
    results = engine_wl.execute(sql_get_worklist)
    cxr_list = [{'accno': row['accno'], 'examdate': row['examdate']} for row in results]
    cxr_total = len(cxr_list)
    print('Start retrieving CXR... Total: {cxr_total}'.format(cxr_total=cxr_total))
    for i, cxr in enumerate(cxr_list):
        print('{}/{}\t{}\t{}'.format(i, cxr_total, cxr['accno'], cxr['examdate']))
        retrieve_study(cfg, cxr['accno'], output_dir)

if __name__ == "__main__":
    main()
