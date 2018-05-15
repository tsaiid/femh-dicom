from os.path import join
from sqlalchemy import create_engine
import yaml
from mldbcls import MLPrediction

def main():
    # load cfg
    yml_path = join('config', 'cxr.yml')
    with open(yml_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    db_path = cfg['sqlite']['path']

    # To use a SQLite :memory: database, specify an empty URL:
    engine = create_engine('sqlite:///' + db_path)
    MLPrediction.metadata.create_all(engine)

if __name__ == "__main__":
    main()
