#!/usr/bin/env python
import functools
import urlparse
import datetime
import os
import random

import gevent.monkey

from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import sessionmaker

import gevent
from gevent.pywsgi import WSGIServer
from gevent.coros import Semaphore

from engineconfig import cstring, servahost

import sakidb

gevent.monkey.patch_all()

class CollectApp:
    def __init__(self, cstring, event_rate=10):
        self.event_rate = event_rate
        self.session = sessionmaker(bind=create_engine(cstring))()
        self.temp = 20
        self.loops = 0

    def application(self, environ, start_response):
        response_headers = [('Content-type', 'text/plain')]
        start_response("200 OK", response_headers)
        return iter([])

    def timer(self):
        while True:
            dte = sakidb.DataTable(timestamp=datetime.datetime.now(),
                                   probe_number=random.randint(0, 4),
                                   temperature=self.temp + (self.loops % 5))
            self.loops += 1
            self.session.add(dte)
            self.session.commit()
            gevent.sleep(self.event_rate)

if __name__ == '__main__':
    semapp = CollectApp(cstring)
    gevent.spawn(functools.partial(CollectApp.timer, semapp))
    WSGIServer(('0.0.0.0', 8089), functools.partial(CollectApp.application, semapp)).serve_forever()
