from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis


class Config(object):
    # 开启debug模式
    DEBUG = True
    # Mysql数据库配置
    SQLALCHEMY_DATABASE_URI = "mysql+mysqldb://root:python@127.0.0.1:3306/school?charset=utf8"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis数据库的配置
    HOST = "127.0.0.1"
    POST = 6379


app = Flask(__name__)
app.config.from_object(Config)

# 生成MYSQL的数据库对象
db = SQLAlchemy(app)

# 创建Redis的对象
redis_store = StrictRedis(host=Config.HOST, port=Config.PORT, decode_responses=True)


if __name__ == "__main__":
    app.run()