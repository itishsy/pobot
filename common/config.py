import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret'
    DB_HOST = '192.168.0.113'
    # DB_HOST = 'localhost'
    DB_PORT = 3306
    DB_USER = 'root'
    DB_PASSWD = 'root'
    DB_DATABASE = 'a_quant'
    DB_CANDLE = 'a_candle'
    ITEMS_PER_PAGE = 20
    JWT_AUTH_URL_RULE = '/api/auth'
    PREFIX = ['00', '60', '30', '51']
    FREQ = [102, 101, 120, 60, 30]
    URL_PREFIX = '/69f2aeb7fa0e11edad01f46b8c05cf04'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    PRODUCTION = True


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
