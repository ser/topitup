#!/usr/bin/env python

import time

# Server engine
import cherrypy
# Framework
from flask import Flask
# Tune our log file
from paste.translogger import TransLogger
# Twitter Bootstrap
from flask_bootstrap import Bootstrap
# Flask Appconfig
from flask_appconfig import AppConfig
# i18n support 
from flask_babel import Babel
# Debug Toolbar
from flask_debugtoolbar import DebugToolbarExtension
# SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
# Login manager
from flask_login import LoginManager

app = Flask('topitup')

# Comment all of this for production!!!!!!!!!!!!!!!!!!!!!!
from flask_debug import Debug
app.debug = True
Debug(app)
# for developement, always pass captcha
app.testing = True

# Install Flask-Appconfig extension
AppConfig(app)

# Install and connect SQLAlchemy
db = SQLAlchemy(app)

# Install Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

from login_bp import User
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# Install Bootstrap extension
Bootstrap(app)

# Install Babel extension and set the locale from the browser
babel = Babel(app)
from flask import request
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(['en', 'pl'])

# if app.debug = True, show a toolbar, please
DebugToolbarExtension(app)

# Build pages from skeleton
from frontend import frontend
from nav import nav
from login_bp import login_bp

# Register bluprints
app.register_blueprint(frontend)
app.register_blueprint(login_bp)

# Initializing the navigation
nav.init_app(app)

class FotsTransLogger(TransLogger):
    # Borrowed from:
    # https://fgimian.github.io/blog/2012/12/08/setting-up-a-rock-solid-python-development-web-server/
    def write_log(self, environ, method, req_uri, start, status, bytes):
        """ We'll override the write_log function to remove the time offset so
        that the output aligns nicely with CherryPy's web server logging

        i.e.

        [08/Jan/2013:23:50:03] ENGINE Serving on 0.0.0.0:5000
        [08/Jan/2013:23:50:03] ENGINE Bus STARTED
        [08/Jan/2013:23:50:45 +1100] REQUEST GET 200 / (192.168.172.1) 830

        becomes

        [08/Jan/2013:23:50:03] ENGINE Serving on 0.0.0.0:5000
        [08/Jan/2013:23:50:03] ENGINE Bus STARTED
        [08/Jan/2013:23:50:45] REQUEST GET 200 / (192.168.172.1) 830
        """

        if bytes is None:
            bytes = '-'
        remote_addr = '-'
        if environ.get('HTTP_X_FORWARDED_FOR'):
            remote_addr = environ['HTTP_X_FORWARDED_FOR']
        elif environ.get('REMOTE_ADDR'):
            remote_addr = environ['REMOTE_ADDR']
        d = {
            'REMOTE_ADDR': remote_addr,
            'REMOTE_USER': environ.get('REMOTE_USER') or '-',
            'REQUEST_METHOD': method,
            'REQUEST_URI': req_uri,
            'HTTP_VERSION': environ.get('SERVER_PROTOCOL'),
            'time': time.strftime('%d/%b/%Y:%H:%M:%S', start),
            'status': status.split(None, 1)[0],
            'bytes': bytes,
            'HTTP_REFERER': environ.get('HTTP_REFERER', '-'),
            'HTTP_USER_AGENT': environ.get('HTTP_USER_AGENT', '-'),
        }
        message = self.format % d
        self.logger.log(self.logging_level, message)


def run_server():
    # Enable custom Paste access logging
    log_format = (
        '[%(time)s] REQUEST %(REQUEST_METHOD)s %(status)s %(REQUEST_URI)s '
        '(%(REMOTE_ADDR)s) %(bytes)s %(HTTP_USER_AGENT)s'
    )
    app_logged = FotsTransLogger(app, format=log_format)

    # Mount the WSGI callable object (app) on the root directory
    cherrypy.tree.graft(app_logged, '/')

    # Set the configuration of the web server
    cherrypy.config.update({
        'engine.autoreload.on': True,
        'log.screen': True,
        'server.socket_port': 1234,
        'server.socket_host': '0.0.0.0'
    })

    # Start the CherryPy WSGI web server
    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__ == "__main__":
    run_server()
