from redis import StrictRedis
import logging

class Config(object):
    # 开启debug模式
    DEBUG = True
    # 设置SECRET_KEY
    SECRET_KEY =     'XuZWm8FSIL6CwyYNvSCHLwCyOcJFpN6IVENCMoCXdDaygdVPy6UfxJcEMrpGtleQ'

    # Redis数据库的配置
    HOST = "127.0.0.1"
    PORT = 6379

    # 设置将SESSION保存到服务器中
    SESSION_TYPE = "redis"
    SESSION_REDIS = StrictRedis(host=HOST, port=PORT)
    SESSION_USE_SIGNER = True
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7

    # 链接MYSQL的配置
    SQLALCHEMY_DATABASE_URI = "mysql+mysqldb://root:python@127.0.0.1:3306/information?charset=utf8"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = logging.DEBUG


class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = logging.WARNING

env_config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}