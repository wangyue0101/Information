from flask import g, session
import functools



def myself_filter(rank):
    if rank == 1:
        return "first"
    elif rank == 2:
        return "second"
    elif rank == 3:
        return 'third'
    else:
        return ""

def user_login_data(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 从session中获取user_id
        user_id = session.get("user_id")
        user = None
        if user_id:
            from info.model import User
            # 在数据库中查询user对象
            user = User.query.get(user_id)
        g.user = user

        return func(*args, **kwargs)
    return wrapper



