import cx_Oracle
import yaml
import os

class Config(object):
    pass
class ProdConfig(Config):
    pass
class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # load cfg
    yml_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'cxr.yml')
    with open(yml_path, 'r') as ymlfile:
        _cfg = yaml.load(ymlfile)

    oracle_conn_str = 'oracle+cx_oracle://{username}:{password}@{dsn_str}'
    dsn_str = cx_Oracle.makedsn(_cfg['oracle']['ip'],
                                _cfg['oracle']['port'],
                                _cfg['oracle']['service_name']).replace('SID', 'SERVICE_NAME')
    SQLALCHEMY_DATABASE_URI =   oracle_conn_str.format(
                                    username=_cfg['oracle']['username'],
                                    password=_cfg['oracle']['password'],
                                    dsn_str=dsn_str
                                )
