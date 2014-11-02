import optparse

from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker
from sqlalchemy import types, Column, Table, inspect, Index
import datetime
import time
import sys

dbase = declarative_base()


class DataTable(dbase):
    __tablename__ = 'data'
    probe_number = Column(types.Integer, primary_key=True, autoincrement=False, nullable=False)
    temperature = Column(types.Float, nullable=False)
    humidity = Column(types.Float)
    timestamp = Column(types.DateTime, primary_key=True, nullable=False, default=datetime.datetime.now())

    def __repr__(self):
        return "<date(%d, %3.2f,% 3.2f, %s)>" % (self.probe_number, self.temperature,
                self.humidity if self.humidity else 0.0,
                str(self.timestamp))


# this one is use for max(DataTable.timestamp)
# the native PK is probe_number,timestamp

Index(u'data_timestamp_idx', DataTable.timestamp, unique=False)
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


def add(session, period, agg_table, last_data_time):
    last = session.query(func.max(agg_table.c.timestamp)).scalar()
    if not last:
        last = session.query(func.min(DataTable.timestamp).label('timestamp')).scalar()
    if (last_data_time - last).total_seconds() < period:
        print "Not data for tailed agg at", period, \
              "last", last, \
              "last_data_time", last_data_time, \
              "seconds",  (last_data_time - last).total_seconds(), \
              "days",  (last_data_time - last).days
        return
    last += datetime.timedelta(seconds=period)
    qry = session.query(DataTable.timestamp, DataTable.probe_number,
                        func.max(DataTable.temperature).label('max')) \
                 .group_by(func.round(func.unix_timestamp(DataTable.timestamp).op('DIV')(period)), DataTable.probe_number) \
                 .filter(DataTable.timestamp > last)
    # print "Insert ", period, qry.all()
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
    parser.add_option("-d", "--delete", dest="delete", action="store_true", default=None, help="delete data from 'data' tables")
    parser.add_option("-r", "--drop-all", dest="drop_all", action="store_true", default=None, help="drop all 'data' tables")
    options, args = parser.parse_args()

    engine = create_engine(cstring, pool_recycle=3600)
    aggs = [60, 600, 3600, 86400]
    atables = list()
    for ii, agglevel in enumerate(aggs):
        atables.append(Table('data%d' % agglevel,  dbase.metadata, *map(lambda c: c.copy(), inspect(DataTable).columns)))

    if options.create:
        dbase.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    if options.delete or options.drop_all:
        for table in dbase.metadata.sorted_tables:
            if table.name.find('data') == 0:
                print "deleting from", table.name
                if options.delete:
                    session.execute(table.delete())
                if options.drop_all:
                    session.execute('drop table %s' % table.name)

        session.commit()

#    add(session, period=60, agg_table=DataMinute)
    if options.monitor:
        while True:
            last_data_time = session.query(func.max(DataTable.timestamp).label('timestamp')).scalar()
            if not last_data_time:
                print "no last, probably no data"
                continue
            for agglevel, aggtable in zip(aggs, atables):
                add(session, period=agglevel, agg_table=aggtable, last_data_time=last_data_time)
            session.commit()
            time.sleep(60)
