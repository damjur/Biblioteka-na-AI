from flask import flash, redirect, render_template,url_for
from flask_login import login_required, login_user, logout_user
from datetime import datetime, timedelta

from . import auth
from .token import generate_confirmation_token, confirm_token
from .forms import LoginForm, RegistrationForm
from .. import db, scheduler
from ..models import User
from ..email import send_email


def delete_unconfirmed_user(id):
	with db.app.app_context():
		user = User.query.get(id)
		if not user.confirmed:
			db.session.delete(user)
			db.session.commit()	

@auth.route('/register', methods=['GET','POST'])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(email = form.email.data,
					username = form.username.data,
					password = form.password.data)
		db.session.add(user)
		db.session.commit()
		
		token = generate_confirmation_token(user.email)
		confirm_url = url_for('auth.confirm_email', token=token, _external=True)
		html = render_template('auth/email.html',confirm_url = confirm_url)
		subject = "Please confirm your email"
		send_email(user.email,subject,html)
		
		d = datetime.now() + timedelta(days=60)
		scheduler.add_job(delete_unconfirmed_user, 'date', run_date=d, args=[user.id], id=str(user.id))
		
		flash('Thou hast successfully registered! Email for authentication hath been send.')
		
		return redirect(url_for('auth.login'))
	return render_template('auth/register.html',form=form,title='Registration')

@auth.route('/confirm/<token>', methods=['GET','POST'])
def confirm_email(token):
	try:
		x = confirm_token(token)
		user = User.query.filter_by(email=x).first_or_404()
		if user.confirmed:
			flash('Account hath been already confirmed. Please login.','success')
		else:
			user.confirmed = True
			db.session.add(user)
			db.session.commit()
			flash('Thou hast confirmed thine account, Thanks!','success')
	except:
		flash('This confirmation link is invalid or hath expired','danger')
	return redirect(url_for('auth.login'))
	
@auth.route('/login', methods=['GET','POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email = form.email.data).first()
		if user is not None and user.verify_password(form.password.data):
			login_user(user)
			return redirect(url_for('home.homepage'))
		else:
			flash('Either password or email is incorrect or unconfirmed.')
			
	return render_template('auth/login.html',form=form,title='Login')
			
@auth.route('/logout', methods=['GET','POST'])
@login_required
def logout():
	logout_user()
	flash('Thou hast been successfully logged out')
	return redirect(url_for('auth.login'))