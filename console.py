import sys
import json
import time
import datetime

from flask import Flask, make_response, jsonify, render_template, request

from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy import cast, Numeric
from flask.ext.bootstrap import Bootstrap

from flask.ext.wtf import Form
from wtforms import TextField, validators, SubmitField

import sakidb
from sakidb import DataTable

sys.stdout = sys.stderr

app = Flask(__name__)
Bootstrap(app)
CSRF_ENABLED = False
app.debug = True

from engineconfig import cstring, servahost
engine = create_engine(cstring, pool_recycle=3600)
Session = sessionmaker(bind=engine, autocommit=True)
session = Session()

probe_labels = ['Fermenter Internal', 'Fermenter External', 'Koji Chamber', 'Humidity Probe']


@app.route('/status')
def status():
#     select data.probe_number,temperature,timestamp from data join (select probe_number, max(timestamp) as ts from data group by probe_number) as xx where xx.ts = timestamp and xx.probe_number = data.probe_number;
    max_times = session.query(DataTable.probe_number, func.max(DataTable.timestamp).label('timestamp')).group_by(DataTable.probe_number).subquery()
    vals = session.query(DataTable.probe_number,
                         DataTable.temperature,
                         DataTable.humidity,
                         DataTable.timestamp) \
                  .join(max_times, and_(max_times.c.timestamp == DataTable.timestamp, max_times.c.probe_number == DataTable.probe_number)) \
                  .order_by(DataTable.probe_number)
    response = make_response(render_template('status.html', vals=vals, servahost=servahost, probe_labels=probe_labels))
    return response

@app.route('/post', methods=['POST'])
def post():
    for probe, temp in request.form.items():
        session.add(DataTable(probe, temp))
    session.commit()
    return " "


@app.route('/report')
def report():
    vals = session.query(DataTable).order_by(DataTable.timestamp.desc()).limit(12)
    return render_template('report.html', vals=vals)


class AlertForm(Form):
    target = TextField('Device', [validators.Required()])
    attribute = TextField('Attribute', [validators.Required()])
    op = TextField('Operator', [validators.Required()])
    value = TextField('Value', [validators.Required()])
    submit_button = SubmitField('Add')


@app.route('/alertconfig/', methods=['POST', 'GET'])
def alertconfig():
    if request.method == 'POST':
        form = AlertForm()
        if form.validate():
            nf = sakidb.config(form.target.data, form.attribute.data, form.op.data, form.value.data)
            session.merge(nf)
            session.commit()
    else:
        form = AlertForm(request.args)
    return render_template('alertconfig.html', form=form, vals=session.query(sakidb.config).all())


@app.route('/getconfig')
@app.route('/getconfig/<string:target>')
def getconfig(target=None):
    qry = session.query(sakidb.config)
    if target is not None:
        qry = qry.filter(sakidb.config.target == target)
    return ''.join([str(ii) + "\n" for ii in qry])


@app.route('/graph')
def graph():
    return render_template('graph.html')


from functools import wraps
from flask import current_app


def support_jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f(*args, **kwargs).data) + ')'
            return current_app.response_class(content, mimetype='application/javascript')
        else:
            return f(*args, **kwargs)
    return decorated_function


from json import encoder
encoder.FLOAT_REPR = lambda o: format(o, '.2f')

target = 100


@app.route('/jdata/<sensor>')
@support_jsonp
def jdata(sensor='0'):
    start = datetime.datetime.fromtimestamp(float(request.args.get('start')) / 1000.0)
    end = datetime.datetime.fromtimestamp(float(request.args.get('end')) / 1000.0)

    seconds = (end - start).total_seconds()
    seconds_per_sample_wanted = seconds / target
    if sensor[0] == 'h':
        qry = session.query(DataTable.timestamp,
                            func.avg(DataTable.humidity).label('avg')) \
                     .group_by(cast(DataTable.timestamp / seconds_per_sample_wanted, Numeric(20, 0))) \
                     .filter(DataTable.probe_number == sensor[1], DataTable.timestamp >= start, DataTable.timestamp <= end) \
                     .order_by(DataTable.timestamp)
        return jsonify(data=[dict(x=int(time.mktime(ii.timestamp.timetuple())) * 1000, y=ii.avg) for ii in qry])
    else:
        qry = session.query(DataTable.timestamp,
                            func.max(DataTable.temperature).label('max'),
                            func.min(DataTable.temperature).label('min')) \
                     .group_by(cast(DataTable.timestamp / seconds_per_sample_wanted, Numeric(20, 0))) \
                     .filter(DataTable.probe_number == sensor, DataTable.timestamp >= start, DataTable.timestamp <= end) \
                     .order_by(DataTable.timestamp)
        return jsonify(data=[dict(x=int(time.mktime(ii.timestamp.timetuple())) * 1000, low=ii.min, high=ii.max) for ii in qry])


@app.route('/gauge/<sensor>')
def gstatus(sensor='0'):
    max_time = session.query(func.max(DataTable.timestamp)).filter(DataTable.probe_number == sensor).subquery()
    row = session.query(DataTable.probe_number, DataTable.temperature, DataTable.humidity, DataTable.timestamp) \
                 .filter(DataTable.timestamp == max_time, DataTable.probe_number == sensor) \
                 .first()
    response = make_response(render_template('status_gauge.html', row=row, probe_labels=probe_labels))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/pstatus/<sensor>')
def pstatus(sensor='0'):
    max_time = session.query(func.max(DataTable.timestamp)).filter(DataTable.probe_number == sensor).subquery()
    row = session.query(DataTable.probe_number, DataTable.temperature, DataTable.humidity, DataTable.timestamp) \
                 .filter(DataTable.timestamp == max_time, DataTable.probe_number == sensor) \
                 .first()
    response = make_response(render_template('status_frag.html', row=row, probe_labels=probe_labels))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/jsond/<sensor>')
def jsond(sensor='0'):
    # qry = session.query(DataTable).filter(DataTable.probe_number == sensor)
    if sensor == 'nav':
        qry = session.query(DataTable.timestamp, func.max(DataTable.temperature).label('max')) \
                     .group_by(cast(DataTable.timestamp / 3600, Numeric(20, 0))) \
                     .order_by(DataTable.timestamp)
        return jsonify(data=[dict(x=int(time.mktime(ii.timestamp.timetuple())) * 1000, y=ii.max) for ii in qry])
    elif sensor[0] == 'h':
        start, end = session.query(func.max(DataTable.timestamp), func.min(DataTable.timestamp)).first()
        seconds = (end - start).total_seconds()
        seconds_per_sample_wanted = seconds / target
        qry = session.query(DataTable.timestamp,
                            func.avg(DataTable.humidity).label('avg')) \
                     .group_by(cast(DataTable.timestamp / seconds_per_sample_wanted, Numeric(20, 0))) \
                     .filter(DataTable.probe_number == sensor[1]) \
                     .order_by(DataTable.timestamp)
        return jsonify(data=[dict(x=int(time.mktime(ii.timestamp.timetuple())) * 1000, y=ii.avg) for ii in qry])
    else:
        start, end = session.query(func.max(DataTable.timestamp), func.min(DataTable.timestamp)).first()
        seconds = (end - start).total_seconds()
        seconds_per_sample_wanted = seconds / target
        qry = session.query(DataTable.timestamp,
                            func.avg(DataTable.temperature).label('avg'),
                            func.max(DataTable.temperature).label('max'),
                            func.min(DataTable.temperature).label('min')) \
                     .group_by(cast(DataTable.timestamp / seconds_per_sample_wanted, Numeric(20, 0))) \
                     .filter(DataTable.probe_number == sensor) \
                     .order_by(DataTable.timestamp)
        return jsonify(data=[dict(x=int(time.mktime(ii.timestamp.timetuple())) * 1000, low=ii.min, high=ii.max) for ii in qry])

app.secret_key = "\xcd\x1f\xc6O\x04\x18\x0eFN\xf9\x0c,\xfb4{''<\x9b\xfc\x08\x87\xe9\x13"

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
