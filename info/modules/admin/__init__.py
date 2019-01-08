from flask import Blueprint

admin_blu = Blueprint("admin", __name__, url_prefix="/admin")

from .views import *


@admin_blu.before_request
def before_request():
    # 不是登陆页面的请求
    if not request.url.endswith(url_for('admin.admin_login')):
        user_id = session.get('user_id', None)
        is_admin = session.get('is_admin', False)

        if not user_id or not is_admin:
            return redirect('/')