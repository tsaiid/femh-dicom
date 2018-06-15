# -*- coding: utf-8 -*-

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
            def get_category_limit_sql(category, query):
                limit_sql = None
                category_dict = query.get(category)
                if category_dict:
                    high_limit = category_dict.get('high')
                    low_limit = category_dict.get('low')
                    if (high_limit and low_limit):
                        limit_sql = '({cat} <= {high} AND {cat} >= {low})'.format(cat=category, high=high_limit, low=low_limit)
                return limit_sql

            cond_list = [get_category_limit_sql(cat, query) \
                            for cat in ('normal', 'ett', 'port', 'cardiomegaly') \
                            if get_category_limit_sql(cat, query)]

            cond_list.append('(ROWNUM <= 100)')
            cond_sql_str = ' AND '.join(cond_list)

            sql = '''
SELECT *
FROM (
    SELECT  w.accno,
            w.datastatus,
            TO_CHAR(w.examdate, 'yyyy-mm-dd hh24:mi:ss') examdate_str,
            w.examcode,
            w.examname,
            w.operatedrid,
            category, probability
    FROM risworklistdatas w
    LEFT JOIN
        (   SELECT *
            FROM (
                SELECT accno, weights_name, category, probability
                FROM risml_predictions
                WHERE
                    weights_name IN ('femh-224-32',
                                     'femh-224-32-ett',
                                     'femh-224-32-port-a',
                                     'femh-224-32-cardiomegaly')
            )
        ) p
    ON w.accno = p.accno
    WHERE
        examcode IN ('RA014', 'RA015', 'RA016', 'RA017', 'RA018', 'RA021')
            AND
        examdate BETWEEN
            TO_DATE( '{start_date}', 'yyyy-mm-dd' )
                AND
            TO_DATE( '{end_date} 23:59:59', 'yyyy-mm-dd hh24:mi:ss' )
)
PIVOT (
    MAX(probability)
    FOR category IN ('cxr-normal' normal,
                     'cxr-ett' ett,
                     'cxr-port-a' port,
                     'cxr-cardiomegaly' cardiomegaly)
)
WHERE {cond_sql_str}
ORDER BY normal DESC
'''.format(start_date=start_date, end_date=end_date, cond_sql_str=cond_sql_str)

            result_dict['response'] = sql

    return jsonify(result_dict)

# 判斷自己執行非被當做引入的模組，因為 __name__ 這變數若被當做模組引入使用就不會是 __main__
if __name__ == '__main__':
    app.run(host='0.0.0.0')
