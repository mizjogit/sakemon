#!/usr/bin/env python
import functools
import urlparse
import os

from gevent.pywsgi import WSGIServer
from gevent.coros import Semaphore


class E405(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class SemaApp:
    def __init__(self):
        self.sem_map = dict()
        self.sem_count = dict()

    def application(self, environ, start_response):
        response_headers = [('Content-type', 'text/plain')]
        response_headers = [('Access-Control-Allow-Origin', '*')]
        try:
            riter, response, headers = self.runner(environ, start_response, response_headers)
            start_response(response, headers)
            return riter
        except E405 as ee:
            print "error", str(ee)
            start_response('405 Bad Request', response_headers)
            return iter([])

    def timer():
        print "hello"

    def runner(self, environ, start_response, headers):
        base, fun = os.path.split(environ['PATH_INFO'])

        if base != '/bmanagea': raise E405("invalid base '%s'" % base)
        print "base", base, "fun", fun
        if environ['REQUEST_METHOD'] == 'POST':
            query = urlparse.parse_qs(environ['wsgi.input'].read())
            if fun == 'release':
                if 'bid' not in query: raise E405("bid not in post")
                ritem = query['bid'][0]
                if ritem not in self.sem_count: raise E405("%s not in sem_map" % ritem)
                rcount = self.sem_count[ritem]
                sem = self.sem_map[ritem]
                del self.sem_count[ritem]
                del self.sem_map[ritem]
                for ii in xrange(rcount):
                    sem.release()
                return iter([]), '200 OK', headers
            else:
                raise E405("invalid function '%s'" % fun)
        else:
            query = urlparse.parse_qs(environ['QUERY_STRING'])
            if fun == 'block':
                if 'bid' not in query: raise E405("bid not in query")
                ritem = query['bid'][0]
                if 'okredir' not in query: raise E405("'okredir' not in query")
                if ritem not in self.sem_map:
                    self.sem_map[ritem] = Semaphore()
                    self.sem_map[ritem].acquire(blocking=True)
                    self.sem_count[ritem] = 1
                self.sem_count[ritem] += 1
                self.sem_map[ritem].acquire(blocking=True)
                headers.append(('Location', query['okredir'][0]))
                return iter([]), '301 Moved Permanently', headers
            else:
                raise E405("invalid function '%s'" % fun)


if __name__ == '__main__':
    print 'Serving on 8088...'
    semapp = SemaApp()
    appruna = functools.partial(SemaApp.application, semapp)
    WSGIServer(('0.0.0.0', 8088), appruna).serve_forever()
