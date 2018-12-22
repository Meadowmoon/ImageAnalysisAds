# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

DB_URI = 'sqlite:///imageads.db'
Base = declarative_base()


class Image(Base):
    __tablename__ = 'images'

    id = Column(Integer, primary_key=True)
    url = Column(String(80))
    obj = Column(String(80))
    #create_at = Column(String(80))
    #create_by = Column(String(80))
    
    
class Label(Base):
    __tablename__ = 'labels'

    obj = Column(String(80), primary_key=True)
    url = Column(String(80))
    #create_at = Column(String(80))
    #create_by = Column(String(80))


if __name__ == "__main__":

    engine = create_engine(DB_URI)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)