from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func

@as_declarative()
class Base(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    id = Column(Integer, primary_key=True)

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