from flask import Flask, render_template, g
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from redis import StrictRedis
from config import env_config
from info.utils.common import myself_filter, user_login_data

app = Flask(__name__)
db = SQLAlchemy()   # 先创建数据库对象，CURRENT_APP中在再进行初始化
redis_store:StrictRedis = None  # 全局默认为None


def current_app(env_name):
    app.config.from_object(env_config[env_name])
    # 开启CSRF保护
    CSRFProtect(app)
    # 吧CSRF_TOKEN传递到前端，通过after_request请求钩子传递
    @app.after_request
    def after_request(response):
        # 生成CSRF_TOKEN值
        csrf_token = generate_csrf()
        response.set_cookie("csrf_token", csrf_token)
        return response

    @app.errorhandler(404)
    @user_login_data
    def bug(e):
        user = g.user
        data = {}
        if user:
            data = {
                "user_info": user.to_dict()
            }
        return render_template("news/404.html", data=data)

    # 将自定义的过滤器添加到app上
    app.add_template_filter(myself_filter, "rank_list")
    # 将配置的信息加载到Session中
    Session(app)
    # 生成MYSQL的数据库对象
    db.init_app(app)
    global redis_store
    # 创建Redis的对象
    redis_store = StrictRedis(host=env_config[env_name].HOST, port=env_config[env_name].PORT, decode_responses=True)
    from info.modules.index import index_blu
    app.register_blueprint(index_blu)
    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)
    from info.modules.news import news_blu
    app.register_blueprint(news_blu)
    from info.modules.user import user_blu
    app.register_blueprint(user_blu)
    from info.modules.admin import admin_blu
    app.register_blueprint(admin_blu)
    return app