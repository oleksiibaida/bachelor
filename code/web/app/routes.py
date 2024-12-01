from flask import render_template, redirect, url_for, flash 

from .forms import RegistrationForm, LoginForm
from .database import Database
from config.logger_config import logger_init
_logger = logger_init()
def register_routes(app, db:Database):
    @app.route('/')
    def index():
        return redirect(url_for('login'))

    @app.route('/register', methods=['GET','POST'])
    def register():
        form = RegistrationForm()
        if form.validate_on_submit():
            user_data = {
                'username': form.username.data,
                'email': form.email.data,
                'password': form.password.data
            }
            _logger.debug(msg="ADDING USER")
            db.add_user(user_data)
            flash("ACC CREATED", 'success')
        return render_template('register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            login_data = {
                'username': form.username.data,
                'password': form.password.data
            }
            if not db.user_password_check(password=login_data['password'], username=login_data['username']):
                flash("LOGIN or PASS wrong", "danger")
            return redirect(url_for('index'))
        return render_template('login.html', form=form)

    @app.teardown_appcontext
    def teardown_db(exception):
        db.close()