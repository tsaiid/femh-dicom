from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from config import DevConfig
from sqlalchemy import text

#from mldbcls import MLPrediction


# 初始化 Flask 類別成為 instance
app = Flask(__name__)
app.config.from_object(DevConfig)
db = SQLAlchemy(app)

"""
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
"""

# 路由和處理函式配對
@app.route('/')
def index():
    return 'Hello World!'

@app.route('/prob/<accno>')
def get_probability(accno):
    sql = text('''
    SELECT *
    FROM (
        SELECT accno, category, probability
        FROM risml_predictions
        WHERE accno='{accno}'
        AND weights_name IN ('femh-224-32',
                             'femh-224-32-ett',
                             'femh-224-32-port-a',
                             'femh-224-32-cardiomegaly')
    )
    PIVOT (
        MAX(probability)
        FOR category IN ('cxr-normal' normal,
                         'cxr-ett' ett,
                         'cxr-port-a' port,
                         'cxr-cardiomegaly' cardiomegaly)
    )
    '''.format(accno=accno))
    results = db.engine.execute(sql)
    row = results.fetchone()
    if row:
        result_dict = {
            'success': 1,
            'accno': row['accno'],
            'probabilities': {
                'normal': str(row['normal']),
                'ett': str(row['ett']),
                'port': str(row['port']),
                'cardiomegaly': str(row['cardiomegaly'])
            }
        }
    else:
        result_dict = {
            'success': 0,
            'reason': 'No result for accno: {accno}'.format(accno=accno)
        }
    return jsonify(result_dict)

@app.route('/selector', methods=['POST'])
def selector():
    result_dict = {'success': 0, 'reason': 'nil'}
    if request.is_json:
        query = request.get_json()
        start_date = query.get('start_date')
        end_date = query.get('end_date')
        if not start_date or not end_date:
            result_dict['reason'] = 'date range error'
        else:
            sql = '''
            SELECT * FROM RISML_PREDICTIONS
            WHERE examdate BETWEEN {start_date} AND {end_date}
            '''.format(start_date=start_date, end_date=end_date)

            normal = query.get('normal')
            if normal:
                normal_up = normal.get('up')
                normal_down = normal.get('down')
                if (normal_up and normal_down):
                    sql += '''
                AND (category = 'cxr-normal' AND weights_name = 'femh-224-32'
                    AND probability <= {up} AND probability >= {down})
                           '''.format(up=normal_up, down=normal_down)

            ett = query.get('ett')
            if ett:
                ett_up = ett.get('up')
                ett_down = ett.get('down')
                if (ett_up and ett_down):
                    sql += '''
                AND (category = 'cxr-ett' AND weights_name = 'femh-224-32'
                    AND probability <= {up} AND probability >= {down})
                           '''.format(up=ett_up, down=ett_down)

            port = query.get('port')
            if ett:
                port_up = port.get('up')
                port_down = port.get('down')
                if (port_up and port_down):
                    sql += '''
                AND (category = 'cxr-port' AND weights_name = 'femh-224-32'
                    AND probability <= {up} AND probability >= {down})
                           '''.format(up=port_up, down=port_down)

            cardiomegaly = query.get('cardiomegaly')
            if ett:
                cardiomegaly_up = cardiomegaly.get('up')
                cardiomegaly_down = cardiomegaly.get('down')
                if (cardiomegaly_up and cardiomegaly_down):
                    sql += '''
                AND (category = 'cxr-cardiomegaly' AND weights_name = 'femh-224-32'
                    AND probability <= {up} AND probability >= {down})
                           '''.format(up=cardiomegaly_up, down=cardiomegaly_down)

            sql += '''
                AND ROWNUM <= 100
                   '''

            result_dict['response'] = sql

    return jsonify(result_dict)

# 判斷自己執行非被當做引入的模組，因為 __name__ 這變數若被當做模組引入使用就不會是 __main__
if __name__ == '__main__':
    app.run(host='0.0.0.0')
