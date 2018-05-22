import yaml
import os
import sys
from datetime import datetime
#from retrieve_study import retrieve_study

def try_parsing_date(text):
    for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%Y%m%d'):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError('no valid date format found')

def main():
    if len(sys.argv) < 3:
        print
        sys.exit("no argv")

    # load cfg
    yml_path = os.path.join('config', 'pacs.yml')
    with open(yml_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # parse date str
    target_date = try_parsing_date(sys.argv[1]).strftime('%Y-%m-%d')
    output_dir = sys.argv[2]

    # get worklist of cxr on the target date
    dsn_str = cx_Oracle.makedsn(cfg['oracle2']['ip'],
                                cfg['oracle2']['port'],
                                cfg['oracle2']['service_name']).replace('SID', 'SERVICE_NAME')
    engine_wl = create_engine(
        oracle_conn_str.format(
            username=cfg['oracle2']['username'],
            password=cfg['oracle2']['password'],
            dsn_str=dsn_str
        )
    )
    #Session = sessionmaker(bind=engine)
    #session = Session()
    sql_get_worklist = '''
SELECT  w.accno
FROM
    (   SELECT accno
        FROM risworklistdatas
        WHERE
            examcode IN ('RA014', 'RA015', 'RA016', 'RA017', 'RA018', 'RA021')
            AND
            examdate BETWEEN
                TO_DATE( TO_CHAR( {target_date}, 'yyyy-mm-dd' ), 'yyyy-mm-dd' )
                    AND
                TO_DATE( TO_CHAR( {target_date}, 'yyyy-mm-dd' ) || ' 23:59:59', 'yyyy-mm-dd hh24:mi:ss' )
        ORDER BY examdate
    ) w
WHERE
    ROWNUM < 2000
    '''.format(target_date=target_date)
    results = engine_wl.execute(sql_get_worklist)
    #cxr_list = [row['accno'] for row in results]
    for row in results:
        print(row['accno'])
        retrieve_study(cfg, acc_no, output_dir)

if __name__ == "__main__":
    main()