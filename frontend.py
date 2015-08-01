# inside blueprints. This is the front-facing blueprint.
#
# You can find out more about blueprints at
# http://flask.pocoo.org/docs/blueprints/

# Flask modules
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    g
)
from flask_login import (
    current_user,
)
from nav import (
    nav,
    top_nav
)

from functools import wraps

# Define Bootswatch CDN
# from flask_bootstrap import WebCDN
# BOOTSTRAP_VERSION = re.sub(r'^(\d+\.\d+\.\d+).*', r'\1', __version__)
# app.extensions['bootstrap']['cdns']['bootswatch'] = WebCDN(

# Let's start!

frontend = Blueprint('frontend', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login_bp.index', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@frontend.before_request
def before_request():
    try:
        g.user = current_user.username.decode('utf-8')
        g.email = current_user.email.decode('utf-8')
        # amount of Credits in user's account
        g.credits = current_user.neuro
        g.user_id = current_user.id
    except:
        g.user = None
        g.credits = None
    nav.register_element('top_nav', top_nav(g.user, g.credits))


# Front page
@frontend.route('/')
@login_required
def index():
    return render_template('index.html')
