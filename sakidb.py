# -*- coding: utf-8 -*-

from sqlalchemy import *
from sqlalchemy.dialects.mysql import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, sessionmaker
import datetime

dbase = declarative_base()


class DataTable(dbase):
    __tablename__ = 'data'
#    timestamp = Column(TIMESTAMP(), primary_key=True, nullable=False, default=text(u'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    timestamp = Column(TIMESTAMP(), primary_key=True, nullable=False)
    probe_number = Column(INTEGER(), primary_key=True, nullable=False)
    temperature = Column(FLOAT(), nullable=False)
    humidity = Column(FLOAT())

    def __repr__(self):
        return "<date(%d, %3.2f,% 3.2f, %s)>" % (self.probe_number, self.temperature, self.humidity, str(self.timestamp)) 


Index(u'probe_number', DataTable.probe_number, unique=False)


class config(dbase):
    __tablename__ = 'config'
    target = Column(String(length=64), primary_key = True)
    attribute = Column(String(length=64), primary_key = True)
    op = Column(CHAR(length=1))
    value = Column(String(length=10))

    def __init__(self, target, attribute, op, value):
        self.target = target
        self.attribute = attribute
        self.op = op
        self.value = value

    def __repr__(self):
        return "%s,%s,%s,%s" % (self.target, self.attribute, self.op, self.value)



if __name__ == '__main__':
    engine = create_engine(u'mysql://root:Schumacher4@localhost/templogger')
    dbase.metadata.create_all(engine)
