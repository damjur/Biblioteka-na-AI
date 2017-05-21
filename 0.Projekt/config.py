class Config(object):
	SCHEDULER_API_ENABLED = True
	
class DevelopmentConfig(Config):
	DEBUG = True
	SQLALCHEMY_ECHO = True
	
class ProductionConfig(Config):
	DEBUG = False
	
app_config = {
	'development': DevelopmentConfig,
	'production': ProductionConfig
}
