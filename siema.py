# Flask modules
from flask import Blueprint, render_template, abort, redirect, url_for, session, request, flash, current_app, g
from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator

# FLask Login
from flask_login import login_user, logout_user, current_user, login_required

# WTForms
from flask_wtf import Form, RecaptchaField
from wtforms import SubmitField, BooleanField, DecimalField
from wtforms.validators import DataRequired

# Modules required for communication with pypayd
import requests, json

# Other modules
from datetime import datetime

# Our own modules
from topitup import db
from topitup import app
from login_bp import User

# Let's start!

class Payd(db.Model):
    __bind_key__ = "topitup"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    time_creation = db.Column(db.DateTime)
    time_payment = db.Column(db.DateTime)
    order_id =  db.Column(db.String(28), unique=True)
    native_price =  db.Column(db.Integer)
    native_currency =  db.Column(db.String(3))
    btc_price = db.Column(db.Integer)

    def __init__(self, id, user_id, time_creation, time_payment, order_id, native_price, native_currency, btc_price):
        self.id = id
        self.user_id = user_id
        self.time_creation = time_creation
        self.time_payment = time_payment
        self.order_id = order_id
        self.native_price = native_price
        self.native_currency = native_currency
        self.btc_price = btc_price

    def __repr__(self):
        return '<Payd %r>' % self.id

# create sqlite database if it does not exist
try:
    db.create_all(bind='topitup')
except:
    pass

# Blueprint 
siema = Blueprint('siema', __name__)

# Buy credits Form
class LoginForm(Form):
    amount = DecimalField('Amount of Credits', validators=[DataRequired()])
    confirm_me = BooleanField('Please confirm you agree to TOC', validators=[DataRequired()])
    submit = SubmitField("Buy Credits")

@siema.before_request
def before_request():
    try:
        g.user = current_user.username.decode('utf-8')
        g.email = current_user.email.decode('utf-8')
        g.user_id = current_user.id
        # amount of Credits in user's account
        g.neuro = current_user.neuro
    except: pass

@siema.route('/invoices/new', methods=('GET', 'POST'))
@login_required
def new():
    form = LoginForm()
    if form.validate_on_submit():

        amount = request.form['amount']

        confirm_me = False
        if 'confirm_me' in request.form:
            confirm_me = True

        if confirm_me == False:
            pass

        # get a new transaction id 
        sql_query = Payd.query.all()
        new_local_transaction_id = len(sql_query)
        # TODO: deal with an unlikely event of concurrency

        # initiate conversation with pypayd
        pypayd_headers = {'content-type': 'application/json'}
        pypayd_payload = {
            "method": "create_order",
            "params": {"amount": amount, "qr_code": True},
            "jsonrpc": "2.0",
            "id": new_local_transaction_id,
        }
        pypayd_response = requests.post(app.config['PYPAYD_URI'],
            data=json.dumps(pypayd_payload),
            headers=pypayd_headers).json()

        print(pypayd_response)

        # insert stuff into our transaction database
        to_db = Payd(
            None,
            g.user_id,
            datetime.utcnow(),
            datetime.fromtimestamp(0), # this is not a paid invoice, yet
            pypayd_response['result']['order_id'],
            amount,
            "EUR",
            pypayd_response['result']['amount'],
        )
        db.session.add(to_db)
        db.session.commit()

        # and finally show an invoice to the customer
        #return render_template('invoice-payme.html')

    return render_template('invoice-new.html', form=form)

#@siema.route('/invoices/', methods=('GET', 'POST'))
@siema.route('/invoices/', defaults={'page': 1})
@siema.route('/invoices/page/<int:page>')
@login_required
def index(page):
    # downloading all records related to user
    #sql_query = Payd.query.filter_by(id=g.user_id).paginate(1)
    sql_query = Payd.query.paginate(page)

    return render_template('invoices.html', 
                           invoices=sql_query,
                           )
