from flask import Blueprint, render_template, redirect, flash, url_for, request
from flask_login import login_user, current_user, login_required, logout_user
from flask_mail import Message, Mail
from werkzeug.security import generate_password_hash, check_password_hash

import main
from website import db
from website.forms import RegistrationForm, LoginForm, ResetPasswordForm, RequestResetForm
from website.models import User
auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('views.home'))
            flash(f'Welcome {form.email.data}!', category='success')
            return redirect(url_for('views.home'))
        else:
            flash('Login unsuccessful, please check email or password', category='error')
            return redirect(url_for('auth.login'))
    return render_template('login.html', title='Login', form=form)


@auth.route('/register', methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data,
                    password=generate_password_hash(form.password.data, method='sha256'))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f'Account created for {form.username.data}!', category='success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', title='Register', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.index'))


def send_reset_email(user,mail=Mail):
    mail.init_app(main.app)

    token = user.get_reset_token(user)
    msg = Message('Password Reset Request', sender='noreply@demo.com', recipients=[user.email])
    msg.body = f''' To reset your password, visit the following link: 
    {url_for('auth.reset_token', token=token, _external=True)}    
    
If you did not make this request please ignore this email and no changes will be made.
'''
    mail.send(msg,['kingwannyama01@gmail.com'])


@auth.route('/reset_password', methods=['POST', 'GET'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been send to reset your password.', category='info')
        return redirect(url_for('auth.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@auth.route('/reset_password/<token>', methods=['POST', 'GET'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('Invalid or Expired token', category='warning')
        return redirect(url_for('auth.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        login_user(user)
        flash('Your password has been updated, You can now login!', category='success')
        return redirect(url_for('auth.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)
