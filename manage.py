from flask import session
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import db, current_app
from info import model
from info.model import User

app = current_app("development")
# 设置应用程序在命令行启动与数据库迁移
manager = Manager(app)
Migrate(app, db)
manager.add_command("db", MigrateCommand)
print(app.url_map)


# 添加管理员,使用flask-script扩展添加命令行相关逻辑操作
# 命令行执行python manage.py superuser(创建管理员的函数名字) -n 用户名 -p 密码
@manager.option("-n", "-name", dest="name")
@manager.option("-p", "-password", dest="password")
def superuser(name, password):
    if not all([name, password]):
        print("参数不足")

    user = User()
    user.mobile = name
    user.nick_name = name
    user.password = password
    user.is_admin = True

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()

    session["nick_name"] = user.nick_name
    session['user_id'] = user.id
    session['is_admin'] = True
    session['mobile'] = user.mobile


if __name__ == "__main__":
    manager.run()