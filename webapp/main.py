from flask import Flask, jsonify
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

# 判斷自己執行非被當做引入的模組，因為 __name__ 這變數若被當做模組引入使用就不會是 __main__
if __name__ == '__main__':
    app.run()