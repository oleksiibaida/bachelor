from flask import render_template, redirect, url_for, flash, Blueprint
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from .forms import RegistrationForm, LoginForm
from app.db.models import User, UserDevice
from ..db import db
from ..db.models import User, UserDevice
# from .services import validate_user
from wtforms import ValidationError
from ..config import Config
_logger = Config.logger_init()

bp = Blueprint('webserver', __name__)

@bp.route('/')
def index():
    form = LoginForm()
    if form.validate_on_submit():
        _logger.info("PUNKT")
        user_data = {
            'username': form.username.data,
            'password': form.password.data
        }
        if validate_user_login(username=user_data['username'], password=user_data['password']):
            _logger.info(msg="User {username} LOGIN")
            return redirect(url_for('home'), username=user_data['username'])
    return render_template('index.html', form=form)

@bp.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user_data = {
            'username': form.username.data,
            'email': form.email.data, 
            'password': form.password.data
        }
        _logger.debug(msg="ADDING USER")
        if validate_username(username=user_data['username']) and validate_email(email=user_data['email']):
            _logger.debug(msg=f"ADDING USER {user_data}")
            db.add(User(user_data))
            db.commit()
            return redirect('/')
    return render_template('register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        _logger.info("PUNKT")
        login_data = {
            'username': form.username.data,
            'password': form.password.data
        }
        if validate_user_login(username=login_data['username'], password=login_data['password']):
            _logger.info(msg=f"User {login_data['username']} LOGIN")
            return redirect(url_for('home'), username=login_data['username'])
    return render_template('login.html', form=form)

@bp.route('/home')
def home():
    return render_template('home.html')

def validate_username(username):
        if db.query(User).filter(User.username == username).count() > 0:
            raise ValidationError('Email already exists. Please choose a different one.')
        else: return True

def validate_email(email):
    if db.query(User).filter(User.email == email).count() > 0:
        raise ValidationError('Email already exists. Please choose a different one.')
    else: return True

def validate_user_login(username, password):
    _logger.info(msg="LOGIN")
    user = db.query(User).filter(User.username == username).first()
    _logger.info(msg=f"USER:{user}")
    if user:
        return user.pasword == password