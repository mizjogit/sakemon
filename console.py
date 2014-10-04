from flask import Flask, url_for, make_response, flash, redirect
from flask import render_template
from flask import request

from  sqlalchemy import create_engine, Table, MetaData, select, join
from sqlalchemy.orm import scoped_session, sessionmaker

import sqlalchemy.exc

from flask.ext.bootstrap import Bootstrap
from flask_wtf import Form, BooleanField, TextField, validators, IntegerField, SelectField, RadioField


import sys
import json
import time
#import mod_wsgi

import sakidb

sys.stdout = sys.stderr

app = Flask(__name__)
Bootstrap(app)
CSRF_ENABLED = False

app.config.from_object(__name__)
app.debug = True

import socket
if socket.gethostname() == 'firewall7':
    engine = create_engine(u'mysql://josh:@localhost/josh')
else:
    engine = create_engine(u'mysql://root:Schumacher4@localhost/templogger')

Session = sessionmaker(bind=engine)
session = Session()

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

@app.route('/jsond/<int:sensor>')
def jsond(sensor=0):
    qry = session.query(sakidb.data).filter(sakidb.data.probe_number == sensor)
    return json.dumps([(time.mktime(ii.timestamp.timetuple()) * 1000, ii.temperature) for ii in qry])

app.secret_key = "\xcc\x1f\xc6O\x04\x18\x0eFN\xf9\x0c,\xfb4{''<\x9b\xfc\x08\x87\xe9\x13"

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
