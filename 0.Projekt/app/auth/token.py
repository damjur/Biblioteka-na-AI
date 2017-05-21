from itsdangerous import URLSafeTimedSerializer

from flask import current_app as app

def generate_confirmation_token(email):
	serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
	return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])
	
def confirm_token(token, expiration=24*60*60):
	serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
	email = serializer.loads(token,salt=app.config['SECURITY_PASSWORD_SALT'],max_age=expiration)
	return email