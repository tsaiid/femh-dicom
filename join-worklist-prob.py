from sqlalchemy import create_engine
from cxrdbcls import CxrNormalProbability
import pandas as pd
from os.path import join
import yaml

def main():
    # load cfg
    yml_path = join('config', 'cxr.yml')
    with open(yml_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # get prob db
    oracle_conn_str = 'oracle+cx_oracle://{username}:{password}@{dsn_str}'
    dsn_str = cx_Oracle.makedsn(cfg['oracle']['ip'], cfg['oracle']['port'], cfg['oracle']['service_name']).replace('SID', 'SERVICE_NAME')
    engine_prob = create_engine(
        oracle_conn_str.format(
            username=cfg['oracle']['username'],
            password=cfg['oracle']['password'],
            dsn_str=dsn_str
        )
    )
    #Session = sessionmaker(bind=engine_prob)
    #session_prob = Session()
    results = engine_prob.execute('select * from ml_predictions')
    prob_dict_list = [dict(row) for row in results]
    prob_df = pd.DataFrame(prob_dict_list)
    #session.close()

    # get worklist
    dsn_str = cx_Oracle.makedsn(cfg['oracle2']['ip'], cfg['oracle2']['port'], cfg['oracle2']['service_name']).replace('SID', 'SERVICE_NAME')
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
SELECT  w.accno,
        TO_CHAR(w.datadate, 'yyyy-mm-dd hh24:mi:ss') datadate_str,
        w.datastatus,
        TO_CHAR(w.examdate, 'yyyy-mm-dd hh24:mi:ss') examdate_str,
        w.examcode,
        w.examname
FROM
    (   SELECT id, accno, datadate, datastatus, examdate, examcode, examname, reportid
        FROM risworklistdatas
        WHERE
            examcode IN ('RA014', 'RA015', 'RA016', 'RA017', 'RA018', 'RA021')
            AND
            examdate BETWEEN
                TO_DATE( TO_CHAR( SYSDATE-30, 'yyyy-mm-dd' ), 'yyyy-mm-dd' )
                    AND
                TO_DATE( TO_CHAR( SYSDATE, 'yyyy-mm-dd' ) || ' 23:59:59', 'yyyy-mm-dd hh24:mi:ss' )
        ORDER BY examdate DESC
    ) w
WHERE
    w.datastatus <> 'RPTVS'
    AND
    ROWNUM < 2000
    '''
    results = engine_wl.execute(sql_get_worklist)
    wl_dict_list = [dict(row) for row in results]
    wl_df = pd.DataFrame(wl_dict_list)
    #session.close()

    # use pandas df
    df = wl_df.join(prob_df.set_index('accno'), on='accno', lsuffix='_left', rsuffix='_right')
    sorted_df = df.loc[(df['model_name'] == 'densenet121-binary-classification') & \
                       (df['weights_name'] == 'femh-224-32')] \
                  .sort_values(by='probability', ascending=False)
    print(sorted_df)

if __name__ == "__main__":
    main()
