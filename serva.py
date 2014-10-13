#!/usr/bin/env python
import functools
import urlparse
import datetime
import os

import gevent
from gevent.pywsgi import WSGIServer
from gevent.coros import Semaphore


class E4XX(Exception):
    def __init__(self, etype, message):
        self.etype = etype
        self.message = message

    def __repr__(self):
        types = {404: "Not Found", 405: "Method Not Allowed"}
        return '%03d %s' % (self.etype, types[self.etype]) if self.etype in types else (400, 'Bad Request')

    def __str__(self):
        return self.message


def IfNotAbort(testval, etype, text):
    if testval:
        raise E4XX(etype, text)


class SemaApp:
    def __init__(self, sem_timeout=120):
        self.sem_map = dict()
        self.sem_timeout = sem_timeout

    def application(self, environ, start_response):
        response_headers = [('Content-type', 'text/plain')]
        response_headers = [('Access-Control-Allow-Origin', '*')]
        try:
            riter, response, headers = self.runner(environ, start_response, response_headers)
            start_response(response, headers)
            return riter
        except E4XX as ee:
            print "error", str(ee), repr(ee)
            start_response(repr(ee), response_headers)
            return iter([])

    class Sema:
        def __init__(self):
            self.sem = Semaphore()
            self.timestamp = datetime.datetime.now()
            self.count = 1
            self.sem.acquire(blocking=True)

        def join(self):
            self.count += 1
            self.sem.acquire(blocking=True)

        def release(self):
            for ii in xrange(self.count):
                self.sem.release()

    def timer(self):
        while True:
            gevent.sleep(10)
            now = datetime.datetime.now()
            for key, value in self.sem_map.items():
                age = now - value.timestamp
                if age.seconds > self.sem_timeout:
                    self.sem_map[key].release()
                    del self.sem_map[key]

    def runner(self, environ, start_response, headers):
        base, fun = os.path.split(environ['PATH_INFO'])

        IfNotAbort(base != '/bmanagea', 405, "invalid base '%s'" % base)
        if environ['REQUEST_METHOD'] == 'POST':
            query = urlparse.parse_qs(environ['wsgi.input'].read())
            if fun == 'release':
                IfNotAbort('bid' not in query, 400, "bid not in post")
                ritem = query['bid'][0]
                # print "base", base, "fun", fun, "ritem", ritem
                IfNotAbort(ritem not in self.sem_map, 405, "'%s' not in sem_map" % ritem)
                self.sem_map[ritem].release()
                del self.sem_map[ritem]
                return iter([]), '200 OK', headers
            else:
                raise E4XX(405, "invalid function '%s'" % fun)
        else:
            query = urlparse.parse_qs(environ['QUERY_STRING'])
            if fun == 'block':
                IfNotAbort('bid' not in query, 405, "bid not in query")
                ritem = query['bid'][0]
                # print "base", base, "fun", fun, "ritem", ritem
                IfNotAbort('okredir' not in query, 405, "'okredir' not in query")
                if ritem not in self.sem_map:
                    self.sem_map[ritem] = self.Sema()
                self.sem_map[ritem].join()
                headers.append(('Location', query['okredir'][0]))
                return iter([]), '301 Moved Permanently', headers
            else:
                raise E4XX(405, "invalid function '%s'" % fun)


if __name__ == '__main__':
    print 'Serving on 8088...'
    semapp = SemaApp()
    gevent.spawn(functools.partial(SemaApp.timer, semapp))
    WSGIServer(('0.0.0.0', 8088), functools.partial(SemaApp.application, semapp)).serve_forever()
