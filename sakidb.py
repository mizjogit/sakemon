import optparse

from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker
from sqlalchemy import types, Column, Table, inspect  # , Index
import datetime
import time
import sys

dbase = declarative_base()


class Data(dbase):
    __tablename__ = 'data'
    timestamp = Column(types.DateTime, primary_key=True, nullable=False, default=datetime.datetime.now())
    probe_number = Column(types.Integer, primary_key=True, autoincrement=False, nullable=False)
    temperature = Column(types.Float, nullable=False)
    humidity = Column(types.Float)

    def __repr__(self):
        return "<date(%d, %3.2f,% 3.2f, %s)>" % (self.probe_number, self.temperature,
                self.humidity if self.humidity else 0.0,
                str(self.timestamp))



# Index(u'probe_number', DataTable.probe_number, unique=False)
# Index(u'probe_number', DataHour.probe_number, unique=False)
class config(dbase):
    __tablename__ = 'config'
    target = Column(types.String(length=64), primary_key=True)
    attribute = Column(types.String(length=64), primary_key=True)
    op = Column(types.String(length=1))
    value = Column(types.String(length=10))

    def __init__(self, target, attribute, op, value):
        self.target = target
        self.attribute = attribute
        self.op = op
        self.value = value

    def __repr__(self):
        return "%s,%s,%s,%s" % (self.target, self.attribute, self.op, self.value)


def add(session, period, agg_table):
    last_data_time = session.query(func.max(Data.timestamp).label('timestamp')).scalar()
    if not last_data_time:
        print "no last, probably no data"
        return
    last = session.query(func.max(agg_table.c.timestamp)).scalar()
    if not last:
        last = session.query(func.min(Data.timestamp).label('timestamp')).scalar()
    if (last_data_time - last).seconds < period:
        print "less than", period
        return
    last += datetime.timedelta(seconds=period)
    qry = session.query(Data.timestamp, Data.probe_number,
                        func.max(Data.temperature).label('max')) \
                 .group_by(cast(Data.timestamp / period, Numeric(20, 0)), Data.probe_number) \
                 .filter(Data.timestamp > last)
    print "Insert ", period, qry.all()
    session.execute(insert(agg_table).from_select(['timestamp', 'probe_number', 'temperature'], qry))

if __name__ == '__main__':
    from engineconfig import cstring
    from sqlalchemy import func
    from sqlalchemy import cast, Numeric
    from sqlalchemy import create_engine
    from sqlalchemy.schema import CreateTable
    from sqlalchemy import insert

    parser = optparse.OptionParser()
    parser.add_option("-c", "--create", dest="create", action="store_true", default=None, help="Create Tables")
    parser.add_option("-m", "--monitor", dest="monitor", action="store_true", default=None, help="monitor and update")
    options, args = parser.parse_args()

    engine = create_engine(cstring, pool_recycle=3600)
    aggs = [60, 600, 3600]
    atables = list()
    for ii, agglevel in enumerate(aggs):
        atables.append(Table('data%d' % agglevel,  dbase.metadata, *map(lambda c: c.copy(), inspect(Data).columns)))

    if options.create:
        dbase.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

#    add(session, period=60, agg_table=DataMinute)
    if options.monitor:
        while True:
            for agglevel, aggtable in zip(aggs, atables):
                add(session, period=agglevel, agg_table=aggtable)
            session.commit()
            time.sleep(60)
