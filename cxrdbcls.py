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
    __tablename__ = 'ML_PREDICTIONS'
    #定义id,主键唯一,
    id = Column(Integer, primary_key=True, autoincrement=True)
    ACCNO = Column(String(50),nullable=False)
    MODEL_NAME = Column(String(50),nullable=False)
    MODEL_VER = Column(String(50),nullable=False)
    WEIGHTS_NAME = Column(String(50),nullable=False)
    WEIGHTS_VER = Column(String(50),nullable=False)
    PROBABILITY = Column(Float(),nullable=False)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())
