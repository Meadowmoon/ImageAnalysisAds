class Config(object):
    SECRET_KEY = 'key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig(Config):
    DEBUG = False


class DebugConfig(Config):
    DEBUG = True
