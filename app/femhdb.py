import os
import yaml
import cx_Oracle
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class FemhDb():
    def __init__(self):
        # load cfg
        yml_path = os.path.join('config', 'cxr.yml')
        with open(yml_path, 'r') as ymlfile:
            cfg = yaml.load(ymlfile)

        oracle_conn_str = 'oracle+cx_oracle://{username}:{password}@{dsn_str}'
        dsn_str = cx_Oracle.makedsn(cfg['oracle']['ip'], cfg['oracle']['port'], cfg['oracle']['service_name']).replace('SID', 'SERVICE_NAME')
        engine = create_engine(
            oracle_conn_str.format(
                username=cfg['oracle']['username'],
                password=cfg['oracle']['password'],
                dsn_str=dsn_str
            )
        )
        Session = sessionmaker(bind=engine)
        self.session = Session()
