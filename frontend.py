# This contains our frontend; since it is a bit messy to use the @app.route
# decorator style when using application factories, all of our routes are
# inside blueprints. This is the front-facing blueprint.
#
# You can find out more about blueprints at
# http://flask.pocoo.org/docs/blueprints/

# Flask modules
from flask import Blueprint, render_template, abort, redirect, url_for, session, request, flash, current_app, g
from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator
from flask_login import current_user, login_required
from functools import wraps

# Define Bootswatch CDN
#from flask_bootstrap import WebCDN
#BOOTSTRAP_VERSION = re.sub(r'^(\d+\.\d+\.\d+).*', r'\1', __version__)
#app.extensions['bootstrap']['cdns']['bootswatch'] = WebCDN(

# Let's start!

from nav import nav

frontend = Blueprint('frontend', __name__)

# We're adding a navbar as well through flask-navbar. In our example, the
# navbar has an usual amount of Link-Elements, more commonly you will have a
# lot more View instances.
#nav.register_element('frontend_top', Navbar(
#    View('TopItUp', '.index'),
#    Subgroup(
#        Text(topitup_user),
#        Text('Bootstrap'),
#    ),
#    View('Home', '.index'),
#    View('Debug-Info', 'debug.debug_root'),
#    Subgroup(
#        'Docs',
#        Link('Flask-Bootstrap', 'http://pythonhosted.org/Flask-Bootstrap'),
#        Link('Flask-AppConfig', 'https://github.com/mbr/flask-appconfig'),
#        Link('Flask-Debug', 'https://github.com/mbr/flask-debug'),
#        Separator(),
#        Text('Bootstrap'),
#        Link('Getting started', 'http://getbootstrap.com/getting-started/'),
#        Link('CSS', 'http://getbootstrap.com/css/'),
#        Link('Components', 'http://getbootstrap.com/components/'),
#        Link('Javascript', 'http://getbootstrap.com/javascript/'),
#        Link('Customize', 'http://getbootstrap.com/customize/'),
#    )
#))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login_bp.index', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# navbar itself
def top_nav(username, balance):
    if username == None:
        return Navbar(
            View('TopItUp', 'frontend.index'),
            View('Log in', 'login_bp.index'),
        )
    else:
        return Navbar(
            View('TopItUp', 'frontend.index'),
            Subgroup(
                username,
                View('Logout', 'login_bp.logout')
            ),
            Subgroup(
                "Your balance: "+str(balance),
                View('Add more credits', 'siema.new'),
                View('Your invoices history', 'siema.index'),
            ),
        )

@frontend.before_request
def before_request():
    try:
        g.user = current_user.username.decode('utf-8')
        g.email = current_user.email.decode('utf-8')
        # amount of Credits in user's account
        g.credits = current_user.neuro
    except:
        g.user = None
        g.credits = None
    nav.register_element('top_nav', top_nav(g.user, g.credits))

# Front page
@frontend.route('/')
@login_required
def index():
    return render_template('index.html')
