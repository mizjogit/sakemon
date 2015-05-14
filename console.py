#!/usr/bin/env python
import sys
import datetime
import calendar
from dateutil import tz

from flask import Flask, make_response, jsonify, render_template, request, flash

from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from flask.ext.bootstrap import Bootstrap

from flask.ext.wtf import Form
from wtforms import TextField, validators, SubmitField, BooleanField

import sakidb
from sakidb import DataTable, mtable, Sensors

sys.stdout = sys.stderr

app = Flask(__name__)
Bootstrap(app)
# CSRF_ENABLED = False
app.debug = True

from engineconfig import cstring, servahost
engine = create_engine(cstring, pool_recycle=3600)
Session = sessionmaker(bind=engine)  # autocommit=True)
session = Session()

probe_labels = ['Fermenter Internal', 'Fermenter External', 'Koji Chamber', 'Humidity Probe']

@app.route('/status2')
def status2():
    #     select data.probe_label,temperature,timestamp from data join (select probe_label, max(timestamp) as ts
    # from data group by probe_label) as xx where xx.ts = timestamp and xx.probe_label = data.probe_label;
    max_times = session.query(DataTable.probe_label, func.max(DataTable.timestamp).label('timestamp')).group_by(DataTable.probe_label).subquery()
    vals = session.query(DataTable.probe_label,
                         DataTable.temperature,
                         DataTable.humidity,
                         DataTable.timestamp,
                         Sensors.name,
                         Sensors.sclass) \
                  .join(max_times, and_(max_times.c.timestamp == DataTable.timestamp, max_times.c.probe_label == DataTable.probe_label)) \
                  .join(Sensors, DataTable.probe_label == Sensors.label) \
                  .order_by(DataTable.probe_label)
    response = make_response(render_template('status2.html', vals=vals, servahost=servahost))
    return response

@app.route('/status')
def status():
    #     select data.probe_label,temperature,timestamp from data join (select probe_label, max(timestamp) as ts
    # from data group by probe_label) as xx where xx.ts = timestamp and xx.probe_label = data.probe_label;
    max_times = session.query(DataTable.probe_label, func.max(DataTable.timestamp).label('timestamp')).group_by(DataTable.probe_label).subquery()
    vals = session.query(DataTable.probe_label,
                         DataTable.temperature,
                         DataTable.humidity,
                         DataTable.timestamp,
                         Sensors.name) \
                  .join(max_times, and_(max_times.c.timestamp == DataTable.timestamp, max_times.c.probe_label == DataTable.probe_label)) \
                  .join(Sensors, DataTable.probe_label == Sensors.label) \
                  .order_by(DataTable.probe_label)
    response = make_response(render_template('status.html', vals=vals, servahost=servahost))
    return response


@app.route('/post', methods=['POST'])
def post():
    for probe, temp in request.form.items():
        session.add(DataTable(probe, temp))
    return " "


@app.route('/report')
def report():
    vals = session.query(DataTable).order_by(DataTable.timestamp.desc()).limit(12)
    return render_template('report.html', vals=vals)


class SensorNameForm(Form):
    label = TextField('Label (short name)', [validators.Required()])
    name = TextField('Name', [validators.Required()])
    sclass = TextField('Sensor Class', [validators.Required()])
    display = BooleanField('Displayed', default=True)
    submit_button = SubmitField('Add')


@app.route('/sensorconfig/', methods=['POST', 'GET'])
def sensorconfig():
    form = SensorNameForm()
    if request.method == 'POST':
        if form.validate():
            try:
                nss = sakidb.Sensors(name=form.name.data, sclass=form.sclass.data, label=form.label.data, display=form.display.data)
                session.merge(nss)
            except IntegrityError as ee:
                flash(ee.message)
                session.rollback()
        else:
            flash(form.errors)
    return render_template('sensorconfig.html', form=form, vals=session.query(sakidb.Sensors).order_by(sakidb.Sensors.label))


@app.route('/sensordelete', methods=['POST'])
def sensordelete():
    res = session.query(sakidb.Sensors).filter_by(label=request.form['pk']).delete()
    return jsonify(result='OK', message="deleted %d" % res)


@app.route('/sensordtoggle', methods=['POST'])
def sensordtoggle():
    new_state = True if request.form['current'] == 'Hidden' else False
    session.query(sakidb.Sensors.display).filter_by(label=request.form['pk']).update({'display': new_state})
    res = session.query(sakidb.Sensors.display).filter_by(label=request.form['pk']).scalar()
    return jsonify(result='OK', display='Displayed' if res else 'Hidden')


@app.route('/graph')
def graph():
    sensors = session.query(sakidb.Sensors).filter(sakidb.Sensors.display == True).all()
    return render_template('graph.html', sensors=sensors)


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


@app.route('/gauge/<label>')
def gstatus(label=None):
    max_time = session.query(func.max(DataTable.timestamp)).filter(DataTable.probe_label == label).subquery()
    row = session.query(DataTable.probe_label, DataTable.temperature, DataTable.humidity, DataTable.timestamp) \
                 .filter(DataTable.timestamp == max_time, DataTable.probe_label == label) \
                 .first()
    return jsonify(row._asdict())


@app.route('/pstatus/<label>')
def pstatus(label=None):
    max_time = session.query(func.max(DataTable.timestamp)).filter(DataTable.probe_label == label).subquery()
    row = session.query(DataTable.probe_label, DataTable.temperature, DataTable.humidity, DataTable.timestamp, Sensors.name) \
                  .join(Sensors, DataTable.probe_label == Sensors.label) \
                 .filter(DataTable.timestamp == max_time, DataTable.probe_label == label) \
                 .first()
    response = make_response(render_template('status_frag.html', row=row, probe_labels=probe_labels))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


def sensord(label, start, end, field_name, functions):
    seconds_per_sample_wanted, table, is_base_table = mtable.optimal(label, start, end)
    fields = list()
    for agg_func in functions:
        agg_func_name = str(agg_func()).replace('()', '')
        agg_field_name = field_name if is_base_table else '%s_%s' % (field_name, agg_func_name)
        fields.append(agg_func(table.c[agg_field_name]).label(agg_func_name))
    qry = session.query(table.c.timestamp, *fields) \
                 .group_by(func.round(func.unix_timestamp(table.c.timestamp).op('DIV')(seconds_per_sample_wanted))) \
                 .filter(table.c.timestamp >= start, table.c.timestamp <= end) \
                 .order_by(table.c.timestamp)
    if label:
        qry = qry.filter(table.c.probe_label == label)
    return qry






def utc1ktztolocal(onekts):
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    utc = datetime.datetime.fromtimestamp(float(onekts) / 1000.0).replace(tzinfo=from_zone)
    out = utc.astimezone(to_zone).replace(tzinfo=None)
    return out


def localtoutc1k(tt):
    from_zone = tz.tzlocal()
    to_zone = tz.tzutc()
    local = tt.replace(tzinfo=from_zone)
    out = local.astimezone(to_zone).replace(tzinfo=None)
    return calendar.timegm(out.timetuple()) * 1000.0




@app.route('/jdata/<label>')
@support_jsonp
def jdata(label=None):
    start = utc1ktztolocal(request.args.get('start'))
    end = utc1ktztolocal(request.args.get('end'))
    sensor = session.query(sakidb.Sensors).filter(sakidb.Sensors.label == label).first()
    if sensor.sclass == 'HUM':
        qry = sensord(label, start, end, 'humidity', [func.avg])
        return jsonify(data=[dict(x=localtoutc1k(ii.timestamp), y=ii.avg) for ii in qry])
    else:
        qry = sensord(label, start, end, 'temperature', [func.max, func.min])
        return jsonify(data=[dict(x=localtoutc1k(ii.timestamp), low=ii.min, high=ii.max) for ii in qry])


@app.route('/jsond/<label>')       # sensors, '0' '1', '2', '3', 'nav', 'h3'
def jsond(label=None):
    # qry = session.query(Data).filter(Data.probe_label == sensor)

    sensor = session.query(sakidb.Sensors).filter(sakidb.Sensors.label == label).first()
    start, end = session.query(func.min(DataTable.timestamp), func.max(DataTable.timestamp)).first()
    if label == 'nav':
        qry = sensord(None, start, end, 'temperature', [func.avg])
        return jsonify(data=[dict(x=localtoutc1k(ii.timestamp), y=ii.avg) for ii in qry])
    elif sensor.sclass == 'HUM':
        qry = sensord(label, start, end, 'humidity', [func.avg])
        return jsonify(data=[dict(x=localtoutc1k(ii.timestamp), y=ii.avg) for ii in qry])
    else:
        qry = sensord(label, start, end, 'temperature', [func.max, func.min])
        return jsonify(data=[dict(x=localtoutc1k(ii.timestamp), low=ii.min, high=ii.max) for ii in qry])






app.secret_key = "\xcd\x1f\xc6O\x04\x18\x0eFN\xf9\x0c,\xfb4{''<\x9b\xfc\x08\x87\xe9\x13"

if __name__ == '__main__':
    @app.after_request
    def session_commit(response):
        session.commit()
        return response
    app.run(debug=True, port=8080, host='0.0.0.0')
