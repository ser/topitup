# You can find out more about blueprints at
# http://flask.pocoo.org/docs/blueprints/

# Flask modules
from flask import Blueprint, render_template, abort, redirect, url_for, session, request, flash, current_app, g
from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator

# FLask Login
from flask_login import login_user, logout_user, current_user, login_required

# WTForms
from flask_wtf import Form, RecaptchaField
from wtforms import SubmitField, BooleanField, DecimalField
from wtforms.validators import DataRequired

# Let's start!

siema = Blueprint('siema', __name__)

# Buy credits Form
class LoginForm(Form):
    amount = DecimalField('Amount of Credits', validators=[DataRequired()])
    confirm_me = BooleanField('Please confirm you agree to TOC', validators=[DataRequired()])
    submit = SubmitField("Buy Credits")

@siema.route('/siema', methods=('GET', 'POST'))
@login_required
def index():
    form = LoginForm()
    if form.validate_on_submit():

        amount = request.form['amount']

        confirm_me = False
        if 'confirm_me' in request.form:
            confirm_me = True

        if confirm_me == False:
            pass

    return render_template('siema.html', form=form)
