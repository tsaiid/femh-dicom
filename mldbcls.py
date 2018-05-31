from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func, select, text
from sqlalchemy.schema import Sequence

@as_declarative()
class Base(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

class MLPrediction(Base):
    __tablename__ = 'RISML_PREDICTIONS'

    RED_ID = Column(String(100), primary_key=True, nullable=False)
    ACCNO = Column(String(50), nullable=False)
    MODEL_NAME = Column(String(50), nullable=False)
    MODEL_VER = Column(String(50), nullable=False)
    WEIGHTS_NAME = Column(String(50), nullable=False)
    WEIGHTS_VER = Column(String(50), nullable=False)
    CATEGORY = Column(String(50), nullable=False)
    PROBABILITY = Column(Float(), nullable=False)
#    time_created = Column(DateTime(timezone=True), server_default=func.now())
#    time_updated = Column(DateTime(timezone=True), onupdate=func.now())
