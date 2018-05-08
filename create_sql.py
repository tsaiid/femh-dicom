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
    CxrNormalProbability.metadata.create_all(engine)

"""
    Base = declarative_base()
    class CxrNormalProbability(Base):
        #表名
        __tablename__ = 'cxr_normal_probability'
        #定义id,主键唯一,
        id = Column(Integer, primary_key=True, autoincrement=True)
        acc_no = Column(String(16),nullable=False)
        exam_time = Column(DateTime(timezone=True), server_default=func.now())
        model_name = Column(String(16),nullable=False)
        model_ver = Column(String(16),nullable=False)
        normal_probability = Column(Float(),nullable=False)
        time_created = Column(DateTime(timezone=True), server_default=func.now())
        time_updated = Column(DateTime(timezone=True), onupdate=func.now())

    Base.metadata.create_all(engine)
"""

if __name__ == "__main__":
    main()
