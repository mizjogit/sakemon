import optparse

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import types, Column, Table, inspect, Index
import datetime
import time

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


def add(session, period, agg_table, last_data_time, pvt, pvt_field_names):
    last = session.query(func.max(agg_table.c.timestamp)).scalar()
    if not last:
        last = session.query(func.min(DataTable.timestamp).label('timestamp')).scalar()
    if (last_data_time - last).total_seconds() < period:
        print "Not data for tailed agg at", period, \
              "last", last, \
              "last_data_time", last_data_time, \
              "seconds", (last_data_time - last).total_seconds(), \
              "days", (last_data_time - last).days
        return
    last += datetime.timedelta(seconds=period)
    funs = list()
    insp = inspect(DataTable)
    for field, pvt_funs in pvt.items():
        funs.extend([fun(insp.columns[field]) for fun in pvt_funs])
    qry = session.query(DataTable.timestamp, DataTable.probe_number, *funs) \
                 .group_by(func.round(func.unix_timestamp(DataTable.timestamp).op('DIV')(period)), DataTable.probe_number) \
                 .filter(DataTable.timestamp > last)
    session.execute(insert(agg_table).from_select(['timestamp', 'probe_number'] + pvt_field_names, qry))

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
        #create columns for fields other than timestamp, probe_number
        # don't want original temperature, humidity, do want proce number, timestamp
        pvt = {'temperature': [func.min, func.max, func.avg],
                'humidity': [func.avg]}

        # parse and remove primaries, keep others, added product of map above
        cols = list()
        pvt_fields = list()
        for col in inspect(DataTable).columns:
            if col.name not in pvt:
                cols.append(col)
        for col_name, spt in pvt.iteritems():
            for fun in spt:
                fname = '%s_%s' % (col_name, str(fun()).replace('()', ''))
                pvt_fields.append(fname)
                cols.append(Column(fname, types.Float))
        atables.append(Table('data%d' % agglevel, dbase.metadata, *map(lambda c: c.copy(), cols)))

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
                time.sleep(60)
                continue
            for agglevel, aggtable in zip(aggs, atables):
                add(session, agglevel, aggtable, last_data_time, pvt, pvt_fields)
            session.commit()
            time.sleep(60)
