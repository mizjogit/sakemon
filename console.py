import datetime

from flask import Flask, url_for, make_response, flash, redirect, jsonify, abort
from flask import render_template
from flask import request

#from flask.ext.sqlalchemy import SQLAlchemy

from sqlalchemy import create_engine, Table, MetaData, select, join, func
from sqlalchemy.orm import scoped_session, sessionmaker
import sqlalchemy.exc
from sqlalchemy import cast, Numeric

from flask.ext.bootstrap import Bootstrap
#from flask_wtf import Form, BooleanField, TextField, validators, IntegerField, SelectField, RadioField

from flask.ext.wtf import Form
from wtforms import BooleanField, TextField, validators, IntegerField, SelectField, RadioField, SubmitField
from wtforms.validators import Required

import sys
import json
import time
#import mod_wsgi

import sakidb

sys.stdout = sys.stderr

app = Flask(__name__)
Bootstrap(app)
CSRF_ENABLED = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Schumacher4@localhost/templogger'
app.config.from_object(__name__)
app.debug = True

from engineconfig import cstring
engine = create_engine(cstring)
#engine = create_engine(u'mysql://root:Schumacher4@localhost/templogger')
#engine = create_engine(u'mysql://rfo:password@localhost/sake')
Session = sessionmaker(bind=engine)
session = Session()
#session = SQLAlchemy(app)

@app.route('/status')
def status():
#    vals = session.query(sakidb.data).order_by(sakidb.data.timestamp.desc()).limit(12)
#    select probe_number,temperature,humidity,max(timestamp) from data group by probe_number order by probe_number

    vals = session.query(sakidb.data.probe_number,
                         sakidb.data.temperature,
                         sakidb.data.humidity,
                         func.max(sakidb.data.timestamp).label('timestamp')) \
                                  .group_by(sakidb.data.probe_number) \
                                  .order_by(sakidb.data.probe_number)
    response = make_response(render_template('status.html', vals=vals))
#    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/post', methods=['POST'])
def post():
    for probe,temp in request.form.items():
	session.add(sakidb.data(probe, temp))
    session.commit()
    return " "

@app.route('/report')
def report():
    #vals = session.query(sakidb.data).all()
    vals = session.query(sakidb.data).order_by(sakidb.data.timestamp.desc()).limit(12)
    return render_template('report.html', vals=vals)

class AlertForm(Form):
    target = TextField('Device',  [validators.Required()])
    attribute = TextField('Attribute',  [validators.Required()])
    op = TextField('Operator',  [validators.Required()])
    value = TextField('Value',  [validators.Required()])
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
     return ''.join([ str(ii) + "\n"  for ii in qry ])

        
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
            content = str(callback) + '(' + str(f(*args,**kwargs).data) + ')'
            return current_app.response_class(content, mimetype='application/javascript')
        else:
            return f(*args, **kwargs)
    return decorated_function

target = 100

@app.route('/jdata/<int:sensor>')
@support_jsonp
def jdata(sensor=0):
    start = datetime.datetime.fromtimestamp(float(request.args.get('start')) / 1000.0)
    end = datetime.datetime.fromtimestamp(float(request.args.get('end')) / 1000.0)

    seconds = (end - start).total_seconds()
    seconds_per_sample_wanted = seconds / target
    qry = session.query(sakidb.data.timestamp,  \
                       func.max(sakidb.data.temperature).label('max'), \
                       func.min(sakidb.data.temperature).label('min')). \
                       group_by(cast(sakidb.data.timestamp / seconds_per_sample_wanted, Numeric(20, 0))). \
                       filter(sakidb.data.probe_number == sensor, sakidb.data.timestamp >= start, sakidb.data.timestamp <= end)

    return jsonify(data=[dict(x=int(time.mktime(ii.timestamp.timetuple())) * 1000, low=ii.min, high=ii.max) for ii in qry])

@app.route('/pstatus/<sensor>')
def pstatus(sensor=None):
    row = session.query(sakidb.data.probe_number,
                         sakidb.data.temperature,
                         sakidb.data.humidity,
                         func.max(sakidb.data.timestamp).label('timestamp')) \
                                  .filter(sakidb.data.probe_number == sensor).first()
    response = make_response(render_template('status_frag.html', row=row))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response



@app.route('/jsond/<sensor>')
def jsond(sensor=0):
    # qry = session.query(sakidb.data).filter(sakidb.data.probe_number == sensor)
    if sensor == 'nav':
        qry = session.query(sakidb.data.timestamp, func.max(sakidb.data.temperature).label('max')). \
                                     group_by(cast(sakidb.data.timestamp / 3600, Numeric(20, 0)))
        return json.dumps([dict(x=int(time.mktime(ii.timestamp.timetuple())) * 1000, y=ii.max) for ii in qry])
    else:
        start, end = session.query(func.max(sakidb.data.timestamp), func.min(sakidb.data.timestamp)).first()
        seconds = (end - start).total_seconds()
        seconds_per_sample_wanted = seconds / target
        qry = session.query(sakidb.data.timestamp,  \
                           func.avg(sakidb.data.temperature).label('avg'), \
                           func.max(sakidb.data.temperature).label('max'), \
                           func.min(sakidb.data.temperature).label('min')). \
                           group_by(cast(sakidb.data.timestamp / seconds_per_sample_wanted, Numeric(20, 0))). \
                           filter(sakidb.data.probe_number == sensor)
        return json.dumps([dict(x=int(time.mktime(ii.timestamp.timetuple())) * 1000, low=ii.min, high=ii.max) for ii in qry])

app.secret_key = "\xcc\x1f\xc6O\x04\x18\x0eFN\xf9\x0c,\xfb4{''<\x9b\xfc\x08\x87\xe9\x13"

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
