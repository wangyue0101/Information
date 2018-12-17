from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_script import Manager
from flask_session import Session


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


app = Flask(__name__)
app.config.from_object(Config)

# 生成MYSQL的数据库对象
db = SQLAlchemy(app)

# 创建Redis的对象
redis_store = StrictRedis(host=Config.HOST, port=Config.PORT, decode_responses=True)


@app.route("/")
def Index():
    return "Index"


if __name__ == "__main__":
    app.run()