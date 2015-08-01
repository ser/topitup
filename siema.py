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

    def __init__(self, id, user_id, time_creation, time_payment, order_id,
                 native_price, native_currency, btc_price, address):
        self.id = id
        self.user_id = user_id
        self.time_creation = time_creation
        self.time_payment = time_payment
        self.order_id = order_id
        self.native_price = native_price
        self.native_currency = native_currency
        self.btc_price = btc_price
        self.address = address

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
