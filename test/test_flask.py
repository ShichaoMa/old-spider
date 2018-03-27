# -*- coding:utf-8 -*-

from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor
from twisted.web.server import Site
from flask import Flask, request
from werkzeug.serving import run_simple
from werkzeug.debug import DebuggedApplication
app = Flask(__name__)


from bottle import run
@app.route('/', methods=["GET", "POST"])
def hello_world():
    print(request.data)
    return "Hello"
app.debug = True
# resource = WSGIResource(reactor, reactor.getThreadPool(), DebuggedApplication(app, evalex=True))
# reactor.listenTCP(5000, Site(resource))
# reactor.run()
run_simple("0.0.0.0", 5000, app, use_reloader=True, use_debugger=True)
# run(app, host="0.0.0.0", port=5000)
#app.run("0.0.0.0", 3333, True)