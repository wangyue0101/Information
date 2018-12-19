from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis
from config import env_config

app = Flask(__name__)
db = SQLAlchemy()   # 先创建数据库对象，CURRENT_APP中在再进行初始化
redis_store:StrictRedis = None  # 全局默认为None


def current_app(env_name):
    app.config.from_object(env_config[env_name])
    # 开启CSRF保护
    # CSRFProtect(app)
    # 将配置的信息加载到Session中
    Session(app)
    # 生成MYSQL的数据库对象
    db.init_app(app)
    global redis_store
    # 创建Redis的对象
    redis_store = StrictRedis(host=env_config[env_name].HOST, port=env_config[env_name].PORT, decode_responses=True)
    from info.modules.index import index_blu
    app.register_blueprint(index_blu)
    from info.modules.passport import image_passport_blu, sms_passport_blu
    app.register_blueprint(image_passport_blu)
    app.register_blueprint(sms_passport_blu)
    return app