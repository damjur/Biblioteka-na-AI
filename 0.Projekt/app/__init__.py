from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler

from config import app_config

mail = Mail()
db = SQLAlchemy()
login_manager = LoginManager()
scheduler = BackgroundScheduler(
	job_defaults={'misfire_grace_time': 24*60*60}
)

def create_app(config_name):
	app = Flask(__name__,instance_relative_config = True)
	app.config.from_object(app_config[config_name])
	app.config.from_pyfile('config.py')
	db.init_app(app)
	db.app = app
	
	scheduler.add_jobstore('sqlalchemy', url=app.config['SQLALCHEMY_DATABASE_URI'])
	scheduler.start()
	
	mail.init_app(app)
	
	Bootstrap(app)
	
	login_manager.init_app(app)
	login_manager.login_message = "You must be logged in to view this page"
	login_manager.login_view = "auth.login"
	
	migrate = Migrate(app,db)
	from app import models
	
	from .auth import auth as auth_blueprint
	app.register_blueprint(auth_blueprint)

	from .home import home as home_blueprint
	app.register_blueprint(home_blueprint)
		
	return app