# Flask modules
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    current_app,
    g,
)

# FLask Login
from flask_login import (
    current_user,
)

# WTForms
from flask_wtf import Form
from wtforms import (
    SubmitField,
    BooleanField,
    DecimalField,
)
from wtforms.validators import DataRequired

# Mail
from flask_mail import Message

# Modules required for communication with pypayd
import requests
import json

# Other modules
from datetime import datetime
from datetime import timedelta

# Our own modules
from topitup import db
from frontend import login_required
from nav import (
    nav,
    top_nav
)

# Let's start!


class Payd(db.Model):
    __bind_key__ = "topitup"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    time_creation = db.Column(db.DateTime)
    time_payment = db.Column(db.DateTime)
    order_id = db.Column(db.String(35), unique=True)
    native_price = db.Column(db.Integer)
    native_currency = db.Column(db.String(3))
    btc_price = db.Column(db.Integer)
    address = db.Column(db.String(35))
    txn = db.Column(db.Integer, default=0)

    def __init__(self, id, user_id, time_creation, time_payment, order_id,
                 native_price, native_currency, btc_price, address, txn):
        self.id = id
        self.user_id = user_id
        self.time_creation = time_creation
        self.time_payment = time_payment
        self.order_id = order_id
        self.native_price = native_price
        self.native_currency = native_currency
        self.btc_price = btc_price
        self.address = address
        self.txn = txn

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
    confirm_me = BooleanField('Please confirm you agree to TOC',
                              validators=[DataRequired()])
    submit = SubmitField("Buy Credits")


@siema.before_request
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


# run every minute from cron to check for payments
@siema.route('/invoices/checkitup')
def checkitup():
    # we collect all invoices which are not paid
    sql_query = Payd.query.filter_by(
        time_payment=datetime.fromtimestamp(0)).all()
    for invoice in sql_query:
        print(invoice)
        howold = current_app.config['WARRANTY_TIME']
        # ignore all invoices which are older than WARRANTY_TIME days
        if invoice.time_creation + timedelta(days=howold) > datetime.now():

            print(invoice.order_id)
            # initiate conversation with pypayd
            pypayd_headers = {'content-type': 'application/json'}
            pypayd_payload = {
                "method": "check_order_status",
                "params": {"order_id": invoice.order_id},
                "jsonrpc": "2.0",
                "id": 0,
            }
            #pypayd_response = requests.post(
            #    current_app.config['PYPAYD_URI'],
            #    data=json.dumps(pypayd_payload),
            #    headers=pypayd_headers).json()

            #print(pypayd_response)
            #invoice.txn = 0

            howmanyconfirmations = current_app.config['CONFIRMATIONS']
            confirmations = pypayd_response['result']['amount']
            # Huhu! We have a new payment!
            if invoice.txn == 0 and confirmations > howmanyconfirmations:

                # Send an email message if payment was registered
                # From: DEFAULT_MAIL_SENDER
                msg = Message()
                msg.add_recipient(current_user.email)
                msg.subject = "Payment confirmation"
                msg.body = ""

                # Register payment
                invoice.time_payment = datetime.now()

                # Register paid amount in the main database
                balance = current_user.credits
                current_user.credits = balance + pypayd_response['result']['amount']

            # Housekeeping
            invoice.txn = confirmations

    # register all transactions in databases
    db.session.commit()

    flash('Thank you.', 'info')
    return redirect(url_for('frontend.index'))



@siema.route('/invoices/id/<orderid>')
@login_required
def showinvoice(orderid):
    sql_query = Payd.query.filter_by(
        order_id=orderid).first()
    return render_template('invoice-id.html',
                           invoice=sql_query,
                           )


@siema.route('/invoices/new', methods=('GET', 'POST'))
@login_required
def new():
    form = LoginForm()
    if form.validate_on_submit():

        amount = request.form['amount']

        confirm_me = False
        if 'confirm_me' in request.form:
            confirm_me = True

        if confirm_me is False:
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
        pypayd_response = requests.post(
            current_app.config['PYPAYD_URI'],
            data=json.dumps(pypayd_payload),
            headers=pypayd_headers).json()

        print(pypayd_response)

        # insert stuff into our transaction database
        to_db = Payd(
            None,
            g.user_id,
            datetime.utcnow(),
            datetime.fromtimestamp(0),  # this is not a paid invoice, yet
            pypayd_response['result']['order_id'],
            amount,
            "EUR",
            pypayd_response['result']['amount'],
            pypayd_response['result']['receiving_address'],
            0,
        )
        db.session.add(to_db)
        db.session.commit()

        payme = {
            'credits': amount,
            'btc': pypayd_response['result']['amount'],
            'address': pypayd_response['result']['receiving_address'],
            'image': pypayd_response['result']['qr_image'],
        }

        # generate approximate time to pay the invoice
        pay_time = datetime.now() + timedelta(minutes=45)

        # and finally show an invoice to the customer
        return render_template('invoice-payme.html',
                               payme=payme,
                               pay_time=pay_time)

    return render_template('invoice-new.html', form=form)


# user has access to his own invoices only
@siema.route('/invoices/', defaults={'page': 1})
@siema.route('/invoices/page/<int:page>')
@login_required
def index(page):
    # downloading all records related to user
    sql_query = Payd.query.filter_by(
        user_id=g.user_id).paginate(page,
                                    current_app.config['INVOICES_PER_PAGE'])

    return render_template('invoices.html',
                           invoices=sql_query,
                           )


# admin has access to all invoices
@siema.route('/admin/', defaults={'page': 1})
@siema.route('/admin/page/<int:page>')
@login_required
def admin(page):
    # only user with id = 666 can enter this route
    if g.user_id == 666:
        sql_query = Payd.query.paginate(page, 50)
        return render_template('invoices.html',
                               invoices=sql_query,
                               )
    else:
        flash('You are not admin and you can see your own invoices only!',
              'warning')
        return redirect(url_for('siema.index'))
