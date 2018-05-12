from sqlalchemy import create_engine
from cxrdbcls import CxrNormalProbability
import pandas as pd

def main():
    # get worklist
    engine_wl = create_engine('oracle:///')
    Session = sessionmaker(bind=engine_wl)
    session = Session()
    results = engine2.execute('select acc_no, exam_time from worklist limit 1000;')
    wl_dict_list = [dict(row) for row in results]
    session.close()

    # get prob db
    db_path = 'test_1.db'
    engine_prob = create_engine('sqlite:///' + db_path)
    Session = sessionmaker(bind=engine_prob)
    session = Session()
    results = engine_prob.execute('select acc_no, model_name, model_ver, normal_probability from cxr_normal_probability;')
    prob_dict_list = [dict(row) for row in results]
    session.close()

    # use pandas df
    wl_df = pd.DataFrame(wl_dict_list)
    prob_df = pd.DataFrame(prob_dict_list)
    df = wl_df.join(prob_df.set_index('acc_no'), on='acc_no', lsuffix='_left', rsuffix='_right')
    sorted_df = df.loc[df['model_name'] == 'test_model1'] \
                  .sort_values(by='normal_probability', ascending=False)
    print(sorted_df)

if __name__ == "__main__":
    main()
