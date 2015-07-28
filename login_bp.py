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
# AVOID flask-bcrypt extension, it does not work with python 3.x
import bcrypt

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
        #return unicode(self.id)
        return self.id

    def __repr__(self):
        return '<User %r>' % (self.username)

# Login Form
class LoginForm(Form):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    recaptcha = RecaptchaField('Spam protection')
    submit = SubmitField("Login")

@login_bp.route('/login', methods=('GET', 'POST'))
def index():
    form = LoginForm()
    if form.validate_on_submit():

        username = request.form['username']
        password = request.form['password']
        password = password.encode('utf-8') # required by bcrypt

        sql_user_query = User.query.filter_by(username=username).first()
        print(sql_user_query)

        pwhash = sql_user_query.password.decode('utf-8')
        pwhash = pwhash.encode('utf-8') # required by bcrypt
        userid = sql_user_query.id

        if username and bcrypt.hashpw(password, pwhash) == pwhash:
            login_user(sql_user_query)
            flash('Logged in successfully')
            return redirect('/')

        flash('Username or Password is invalid', 'error')
        return redirect('/login')
    return render_template('login.html', form=form)

