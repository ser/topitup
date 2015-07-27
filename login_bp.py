# This contains our frontend; since it is a bit messy to use the @app.route
# decorator style when using application factories, all of our routes are
# inside blueprints. This is the front-facing blueprint.
#
# You can find out more about blueprints at
# http://flask.pocoo.org/docs/blueprints/

# Flask modules
from flask import Blueprint, render_template, abort, redirect, url_for, session, request, flash, current_app, g
from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator

# Import password / encryption helper tools
from werkzeug import check_password_hash, generate_password_hash

# FLask Login
from flask_login import login_user, logout_user, current_user, login_required

# WTForms
from flask_wtf import Form, RecaptchaField
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired

# Let's start!

login_bp = Blueprint('login_bp', __name__)

from topitup import db
# Structure of User data located in phpBB
class User(db.Model):
    __tablename__ = "phpbb_users"
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column('username_alias', db.String(63), unique=True , index=True)
    password = db.Column('user_password' , db.String(255))
    email = db.Column('user_email', db.String(100), unique=True, index=True)

    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.username)

# Login Form
class LoginForm(Form):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    recaptcha = RecaptchaField('Spam protection')
    submit = SubmitField("Login")

@login_bp.route('/login', methods=('GET', 'POST'))
#def login():
def index():
    if request.method == 'GET':
        form = LoginForm()
#       if form.validate_on_submit():
        return render_template('login.html', form=form)

    username = request.form['username']
    password = request.form['password']

#    registered_user = User.query.filter_by(username=username,password=password).first()
    registered_user = User.query.filter_by(username=username).first()
    if registered_user and check_password_hash(registered_user.password, password):
        login_user(registered_user)
        #session['user_id'] = user.id
        flash('Logged in successfully')
        return redirect('/')
    flash('Username or Password is invalid', 'error')
    return redirect('/login')

