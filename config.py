from redis import StrictRedis


class Config(object):
    # 开启debug模式
    DEBUG = True
    # 设置SECRET_KEY
    SECRET_KEY = 'XuZWm8FSIL6CwyYNvSCHLwCyOcJFpN6IVENCMoCXdDaygdVPy6UfxJcEMrpGtleQ'

    # Redis数据库的配置
    HOST = "127.0.0.1"
    PORT = 6379

    # 设置将SESSION保存到服务器中
    SESSION_TYPE = "redis"
    SESSION_REDIS = StrictRedis(host=HOST, port=PORT, decode_responses=True)
    SESSION_USE_SIGNER = True
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7

    # Mysql数据库配置
    SQLALCHEMY_DATABASE_URI = "mysql+mysqldb://root:python@127.0.0.1:3306/school?charset=utf8"
    SQLALCHEMY_TRACK_MODIFICATIONS = False