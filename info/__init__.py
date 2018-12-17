from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis

from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# 开启CSRF保护
CSRFProtect(app)

# 将配置的信息加载到Session中
Session(app)

# 生成MYSQL的数据库对象
db = SQLAlchemy(app)

# 创建Redis的对象
redis_store = StrictRedis(host=Config.HOST, port=Config.PORT, decode_responses=True)