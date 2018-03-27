# -*- coding:utf-8 -*-
from mashapeanalytics.middleware import FlaskMiddleware as MashapeAnalytics
from flask import Flask

app = Flask(__name__)
app.wsgi_app = MashapeAnalytics(app.wsgi_app, 'SERVICE_TOKEN', 'production') # Attach middleware with environment, `production`

@app.route('/')
def hello_world():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()