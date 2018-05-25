from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import DevConfig

import cx_Oracle
import yaml
import os
from sqlalchemy import create_engine
from flask import jsonify

#from mldbcls import MLPrediction


# 初始化 Flask 類別成為 instance
app = Flask(__name__)
app.config.from_object(DevConfig)
db = SQLAlchemy(app)

class MLPrediction(db.Model):
    __tablename__ = 'ML_PREDICTIONS'

    pred_id = db.Column(db.Integer, db.Sequence('SEQ_ML_PREDICTIONS_PRED_ID'), primary_key=True, autoincrement=True)
    accno = db.Column(db.String(50),nullable=False)
    model_name = db.Column(db.String(50),nullable=False)
    model_ver = db.Column(db.String(50),nullable=False)
    weights_name = db.Column(db.String(50),nullable=False)
    weights_ver = db.Column(db.String(50),nullable=False)
    category = db.Column(db.String(50),nullable=False)
    probability = db.Column(db.Float(),nullable=False)

    def __repr__(self):
        return '<MLPrediction %r>' % self.probability

# 路由和處理函式配對
@app.route('/')
def index():
    return 'Hello World!'

@app.route('/prob/<accno>')
def get_probability(accno):
    """
    yml_path = os.path.join('E:\\git\\femh-dicom\\config', 'cxr.yml')
    with open(yml_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    oracle_conn_str = 'oracle+cx_oracle://{username}:{password}@{dsn_str}'
    dsn_str = cx_Oracle.makedsn(cfg['oracle']['ip'],
                                cfg['oracle']['port'],
                                cfg['oracle']['service_name']).replace('SID', 'SERVICE_NAME')
    engine = create_engine(
        oracle_conn_str.format(
            username=cfg['oracle']['username'],
            password=cfg['oracle']['password'],
            dsn_str=dsn_str
        )
    )

    sql_get_worklist = '''
    SELECT  *
    FROM
        (   SELECT *
            FROM ml_predictions
            WHERE
                accno = '{accno}'
            ORDER BY model_name, weights_name, probability DESC
        )
    WHERE
        ROWNUM <= 10
    '''.format(accno=accno)
    results = engine.execute(sql_get_worklist)
    """

    pred = MLPrediction.query.filter_by(accno=accno).first()
    """
    prob_list = [{'accno': row['accno'],
                'model_name': row['model_name'],
                'weights_name': row['weights_name'],
                'probability': str(row['probability'])} for row in results]
    """
    return str(pred.probability)

# 判斷自己執行非被當做引入的模組，因為 __name__ 這變數若被當做模組引入使用就不會是 __main__
if __name__ == '__main__':
    app.run()