from flask import render_template, redirect, url_for, flash, request
from .forms import RegistrationForm, LoginForm
from .database import Database
from config.logger_config import logger_init
_logger = logger_init()
def register_routes(app, db:Database):
    @app.route('/register', methods=['GET','POST'])
    def register():
        form = RegistrationForm()
        #TODO CHECK valid data
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
        #TODO CHECK valid data
        if True:
            pass
        return render_template('login.html', form=form)

    @app.teardown_appcontext
    def teardown_db(exception):
        db.close()