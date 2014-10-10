import datetime

from flask import Flask, url_for, make_response, flash, redirect, jsonify
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
    vals = session.query(sakidb.temperature).order_by(sakidb.temperature.timestamp.desc()).limit(12)
    return render_template('status.html', vals=vals)


@app.route('/post', methods=['POST'])
def post():
    for probe,temp in request.form.items():
	session.add(sakidb.temperature(probe, temp))
    session.commit()
    return " "

@app.route('/report')
def report():
    #vals = session.query(sakidb.temperature).all()
    vals = session.query(sakidb.temperature).order_by(sakidb.temperature.timestamp.desc()).limit(12)
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
            nf = sakidb.config(form.target.temperature, form.attribute.temperature, form.op.temperature, form.value.temperature)
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
            content = str(callback) + '(' + str(f(*args,**kwargs).temperature) + ')'
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
    qry = session.query(sakidb.temperature.timestamp,  \
                       func.max(sakidb.temperature.temperature).label('max'), \
                       func.min(sakidb.temperature.temperature).label('min')). \
                       group_by(cast(sakidb.temperature.timestamp / seconds_per_sample_wanted, Numeric(20, 0))). \
                       filter(sakidb.temperature.probe_number == sensor, sakidb.temperature.timestamp >= start, sakidb.temperature.timestamp <= end)

    return jsonify(data=[dict(x=int(time.mktime(ii.timestamp.timetuple())) * 1000, low=ii.min, high=ii.max) for ii in qry])

@app.route('/jsond/<sensor>')
def jsond(sensor=0):
    # qry = session.query(sakidb.temperature).filter(sakidb.temperature.probe_number == sensor)
    if sensor == 'nav':
        qry = session.query(sakidb.temperature.timestamp, func.max(sakidb.temperature.temperature).label('max')). \
                                     group_by(cast(sakidb.temperature.timestamp / 3600, Numeric(20, 0)))
        return json.dumps([dict(x=int(time.mktime(ii.timestamp.timetuple())) * 1000, y=ii.max) for ii in qry])
    else:
        start, end = session.query(func.max(sakidb.temperature.timestamp), func.min(sakidb.temperature.timestamp)).first()
        seconds = (end - start).total_seconds()
        seconds_per_sample_wanted = seconds / target
        qry = session.query(sakidb.temperature.timestamp,  \
                           func.avg(sakidb.temperature.temperature).label('avg'), \
                           func.max(sakidb.temperature.temperature).label('max'), \
                           func.min(sakidb.temperature.temperature).label('min')). \
                           group_by(cast(sakidb.temperature.timestamp / seconds_per_sample_wanted, Numeric(20, 0))). \
                           filter(sakidb.temperature.probe_number == sensor)
        return json.dumps([dict(x=int(time.mktime(ii.timestamp.timetuple())) * 1000, low=ii.min, high=ii.max) for ii in qry])

app.secret_key = "\xcc\x1f\xc6O\x04\x18\x0eFN\xf9\x0c,\xfb4{''<\x9b\xfc\x08\x87\xe9\x13"

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
