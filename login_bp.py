# This contains our frontend; since it is a bit messy to use the @app.route
# decorator style when using application factories, all of our routes are
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
    flash,
    g
)
# from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator

# Import password / encryption helper tools
# AVOID flask-bcrypt extension, it does not work with python 3.x
import bcrypt

# FLask Login
from flask_login import (
    login_user,
    logout_user,
    current_user
)

# WTForms
from flask_wtf import Form, RecaptchaField
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired

# Let's start!
from nav import (
    nav,
    top_nav
)

login_bp = Blueprint('login_bp', __name__)

from topitup import db


# Structure of User data located in phpBB
class User(db.Model):
    __tablename__ = "phpbb_users"
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column('username_alias', db.String(63),
                         unique=True, index=True)
    password = db.Column('user_password', db.String(255))
    email = db.Column('user_email', db.String(100), unique=True, index=True)
    posts = db.Column('user_posts', db.Integer)
    avatar = db.Column('user_avatar', db.String(255))
    neuro = db.Column('neuro', db.Numeric(12, 2))

    def __init__(self, username, password, email, posts, avatar, neuro):
        self.username = username
        self.password = password
        self.email = email
        self.posts = posts
        self.avatar = avatar
        self.neuro = neuro

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __repr__(self):
        return '<User %r>' % (self.username)


# Login Form
class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    recaptcha = RecaptchaField('Spam protection')
    submit = SubmitField("Log me in")


@login_bp.before_request
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


@login_bp.route('/login', methods=('GET', 'POST'))
def index():
    form = LoginForm()
    if form.validate_on_submit():

        username = request.form['username']
        password = request.form['password']
        password = password.encode('utf-8')  # required by bcrypt

        remember_me = False
        if 'remember_me' in request.form:
            remember_me = True

        try:
            sql_user_query = User.query.filter_by(username=username).first()

            pwhash = sql_user_query.password.decode('utf-8')
            pwhash = pwhash.encode('utf-8')  # required by bcrypt
            userid = sql_user_query.id

            if userid and bcrypt.hashpw(password, pwhash) == pwhash:
                login_user(sql_user_query, remember=remember_me)
                flash('Logged in successfully', 'info')
                return redirect('/')
        except:
            flash('Username or Password is invalid', 'error')
            return redirect('/login')

    return render_template('login.html', form=form)


@login_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('frontend.index'))
