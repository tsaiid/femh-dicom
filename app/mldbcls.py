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
    __tablename__ = 'risml_predictions'

    pred_id = Column(String(100), primary_key=True, nullable=False)
    accno = Column(String(50), nullable=False)
    model_name = Column(String(50), nullable=False)
    model_ver = Column(String(50), nullable=False)
    weights_name = Column(String(50), nullable=False)
    weights_ver = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)
    probability = Column(Float(), nullable=False)
    comm = Column(Float(), nullable=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
#    time_updated = Column(DateTime(timezone=True), onupdate=func.now())
