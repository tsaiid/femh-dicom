import yaml
import os
import sys
from datetime import datetime
import cx_Oracle
from sqlalchemy import create_engine
from retrieve_study import retrieve_study

def try_parsing_date_range(text):
    # only one date
    for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%Y%m%d'):
        try:
            start_date = datetime.strptime(text, fmt).strftime('%Y-%m-%d')
            return (start_date, start_date)
        except ValueError:
            pass
    # date range fmt: yyyymmdd-yyyymmdd
    try:
        text_a, text_b = text.split('-')
        fmt = '%Y%m%d'
        start_date = datetime.strptime(text_a, fmt)
        end_date = datetime.strptime(text_b, fmt)
        if end_date < start_date:
            end_date = start_date
        return (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    except ValueError:
        pass
    raise ValueError('no valid date format found')

def main():
    if len(sys.argv) < 3:
        print
        sys.exit("argv: date_or_daterange output_dir")

    # load cfg
    yml_path = os.path.join('config', 'cxr.yml')
    with open(yml_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # parse date str
    start_date, end_date = try_parsing_date_range(sys.argv[1])
    output_dir = sys.argv[2]

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
                TO_DATE( '{start_date}', 'yyyy-mm-dd' )
                    AND
                TO_DATE( '{end_date} 23:59:59', 'yyyy-mm-dd hh24:mi:ss' )
        ORDER BY examdate
    ) w
WHERE
    ROWNUM <= 20000
    '''.format(start_date=start_date, end_date=end_date)
    results = engine_wl.execute(sql_get_worklist)
    cxr_list = [{'accno': row['accno'], 'examdate': row['examdate']} for row in results]
    cxr_total = len(cxr_list)
    print('Start retrieving CXR... Total: {cxr_total}'.format(cxr_total=cxr_total))
    for i, cxr in enumerate(cxr_list):
        print('{}/{}\t{}\t{}'.format(i, cxr_total, cxr['accno'], cxr['examdate']))
        retrieve_study(cfg, cxr['accno'], output_dir)

if __name__ == "__main__":
    main()
