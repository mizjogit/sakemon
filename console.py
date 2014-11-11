#!/usr/bin/env python
import sys
import time
import datetime

from flask import Flask, make_response, jsonify, render_template, request, flash

from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from flask.ext.bootstrap import Bootstrap

from flask.ext.wtf import Form
from wtforms import TextField, validators, SubmitField, BooleanField

import sakidb
from sakidb import DataTable, mtable

sys.stdout = sys.stderr

app = Flask(__name__)
Bootstrap(app)
# CSRF_ENABLED = False
app.debug = True

from engineconfig import cstring, servahost
engine = create_engine(cstring, pool_recycle=3600)
Session = sessionmaker(bind=engine)  # autocommit=True)
session = Session()

probe_labels = ['Fermenter Internal', 'Fermenter External', 'Koji Chamber', 'RH Probe']


@app.route('/status')
def status():
    #     select data.probe_number,temperature,timestamp from data
    #       join (select probe_number, max(timestamp) as ts from data group by probe_number)
    #      as xx where xx.ts = timestamp and xx.probe_number = data.probe_number;
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


class SensorNameForm(Form):
    name = TextField('Name', [validators.Required(), validators.length(max=128)])
    short_name = TextField('Short Name', [validators.Required(), validators.length(max=20)])
    display = BooleanField('Displayed', default=True)
    submit_button = SubmitField('Add')


@app.route('/sensorconfig/', methods=['POST', 'GET'])
def sensorconfig():
    form = SensorNameForm()
    if request.method == 'POST':
        if form.validate():
            try:
                nss = sakidb.sensors(name=form.name.data, short_name=form.short_name.data, display=form.display.data)
                session.merge(nss)
                session.commit()
            except IntegrityError as ee:
                flash(ee.message)
                session.rollback()
        else:
            flash(form.errors)
    return render_template('sensorconfig.html', form=form, vals=session.query(sakidb.sensors).order_by(sakidb.sensors.number))


@app.route('/sensordelete', methods=['POST'])
def sensordelete():
    res = session.query(sakidb.sensors).filter_by(number=request.form['pk']).delete()
    session.commit()
    return jsonify(result='OK', message="deleted %d" % res)


@app.route('/sensordtoggle', methods=['POST'])
def sensordtoggle():
    new_state = True if request.form['current'] == 'Hidden' else False
    session.query(sakidb.sensors.display).filter_by(number=request.form['pk']).update({'display': new_state})
    res = session.query(sakidb.sensors.display).filter_by(number=request.form['pk']).scalar()
    session.commit()
    return jsonify(result='OK', display='Displayed' if res else 'Hidden')


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


@app.route('/graph2')
def graph2():
    return render_template('graph2.html')


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


@app.route('/gauge/<sensor>')
def gstatus(sensor='0'):

    if sensor[0] == 'h':
    	max_time = session.query(func.max(DataTable.timestamp)).filter(DataTable.probe_number == sensor[1]).subquery()
    	row = session.query(DataTable.probe_number, DataTable.temperature, DataTable.humidity, DataTable.timestamp) \
                 .filter(DataTable.timestamp == max_time, DataTable.probe_number == sensor[1]) \
                 .first()
	response = make_response(render_template('status_gauge_h.html', row=row, probe_labels=probe_labels))
    else:
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


def sensord(sensor, start, end, field_name, functions):
    seconds_per_sample_wanted, table, is_base_table = mtable.optimal(sensor, start, end)
    fields = list()
    for agg_func in functions:
        agg_func_name = str(agg_func()).replace('()', '')
        agg_field_name = field_name if is_base_table else '%s_%s' % (field_name, agg_func_name)
        fields.append(agg_func(table.c[agg_field_name]).label(agg_func_name))
    qry = session.query(table.c.timestamp, *fields) \
                 .group_by(func.round(func.unix_timestamp(table.c.timestamp).op('DIV')(seconds_per_sample_wanted))) \
                 .filter(table.c.probe_number == sensor, table.c.timestamp >= start, table.c.timestamp <= end) \
                 .order_by(table.c.timestamp)
    return qry


@app.route('/jdata/<sensor>')
@support_jsonp
def jdata(sensor='0'):
    start = datetime.datetime.fromtimestamp(float(request.args.get('start')) / 1000.0)
    end = datetime.datetime.fromtimestamp(float(request.args.get('end')) / 1000.0)
    if sensor[0] == 'h':
        qry = sensord(sensor[1], start, end, 'humidity', [func.avg])
        return jsonify(data=[dict(x=int(time.mktime(ii.timestamp.timetuple())) * 1000, y=ii.avg) for ii in qry])
    else:
        qry = sensord(sensor, start, end, 'temperature', [func.max, func.min])
        return jsonify(data=[dict(x=int(time.mktime(ii.timestamp.timetuple())) * 1000, low=ii.min, high=ii.max) for ii in qry])


@app.route('/jsond/<sensor>')       # sensors, '0' '1', '2', '3', 'nav', 'h3'
def jsond(sensor='0'):
    # qry = session.query(Data).filter(Data.probe_number == sensor)

    start, end = session.query(func.min(DataTable.timestamp), func.max(DataTable.timestamp)).first()
    if sensor == 'nav':
        qry = sensord(sensor, start, end, 'temperature', [func.avg])
        return jsonify(data=[dict(x=int(time.mktime(ii.timestamp.timetuple())) * 1000, y=ii.avg) for ii in qry])
    elif sensor[0] == 'h':
        qry = sensord(sensor[1], start, end, 'humidity', [func.avg])
        return jsonify(data=[dict(x=int(time.mktime(ii.timestamp.timetuple())) * 1000, y=ii.avg) for ii in qry])
    else:
        qry = sensord(sensor, start, end, 'temperature', [func.max, func.min])
        return jsonify(data=[dict(x=int(time.mktime(ii.timestamp.timetuple())) * 1000, low=ii.min, high=ii.max) for ii in qry])

app.secret_key = "\xcd\x1f\xc6O\x04\x18\x0eFN\xf9\x0c,\xfb4{''<\x9b\xfc\x08\x87\xe9\x13"

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
