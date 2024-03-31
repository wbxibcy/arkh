class BaseConfig(object):
    DEBUG = False
    TESTING = False
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///yunhui.sqlite3'
    # SECRET_KEY = 'super-secret'
    # SESSION_TYPE = 'filesystem'
    # SESSION_PERMANENT = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = True


class TestingConfig(BaseConfig):
    DEBUG = False
    TESTING = True
