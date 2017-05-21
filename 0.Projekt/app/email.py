from flask_mail import Message

from flask import current_app as app
from . import mail

def send_email(to,subject,template):
	msg = Message(subject,recipients=[to],html=template,sender=app.config['MAIL_DEFAULT_SENDER'])
	print(msg)
	mail.send(msg)