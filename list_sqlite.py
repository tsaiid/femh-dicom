from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import datetime
from cxrdbcls import CxrNormalProbability

def main():
    # To use a SQLite :memory: database, specify an empty URL:
    engine = create_engine('sqlite:///./cxr-normal-probability.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    ret = session.query(CxrNormalProbability).all()
    for i in ret:
        print(i.acc_no, i.exam_time, i.model_name, i.model_ver, i.normal_probability, i.time_created)
    session.close()

if __name__ == "__main__":
    main()
