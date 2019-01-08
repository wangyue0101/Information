from datetime import datetime, timedelta
import time
from flask import render_template, request, redirect, url_for, g, session, jsonify

from info import user_login_data, constants, db
from info.model import User, News, Category
from info.utils.response_code import RET
from info.utils.storage import storage
from . import admin_blu

# 后台主页
@admin_blu.route("/admin_index")
@user_login_data
def admin_index():
    user = g.user
    return render_template("admin/index.html", user=user.to_dict())

# 后台登陆页面
@admin_blu.route("/admin_login", methods=['GET', 'POST'])
def admin_login():
    if request.method == 'GET':
        if session.get("user_id") and session.get('is_admin'):
            return redirect(url_for("admin.admin_index"))
        return render_template("admin/login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    if not all([username, password]):
        return render_template("admin/login.html", errmsg="用户名或密码为空")

    user = None
    try:
        user = User.query.filter(User.nick_name == username).first()
    except Exception as e:
        print(e)

    if not user:
        return render_template("admin/login.html", errmsg="管理员不存在")

    if not user.check_passowrd(password):
        return render_template("admin/login.html", errmsg="用户名或密码错误")

    if not user.is_admin:
        return render_template("admin/login.html", errmsg="用户权限错误")

    session['nick_name'] = user.nick_name
    session['mobile'] = user.mobile
    session['is_admin'] = True
    session["user_id"] = user.id
    return redirect(url_for("admin.admin_index"))


@admin_blu.route("/user_count")
@user_login_data
def user_count():
    # 查询总人数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin==False).count()
    except Exception as e:
        print(e)

    # 查询月新增数
    month_count = 0
    t = time.localtime()
    month_time = datetime(t.tm_year, t.tm_mon, 1)

    try:
        month_count = User.query.filter(User.is_admin==False, User.create_time>=month_time).count()
    except Exception as e:
        print(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    # 查询日新增用户数
    day_count = 0
    day_time = datetime(t.tm_year, t.tm_mon, t.tm_mday)
    try:
        day_count = User.query.filter(User.is_admin==False, User.create_time>=day_time).count()
    except Exception as e:
        print(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    # 获取当天00：00：00时间
    now_date = datetime(t.tm_year, t.tm_mon, t.tm_mday)
    # 定义空数组，保存数据
    active_date = []
    active_count = []

    # 一次添加数据，再反转
    for i in range(0, 31):
        start_date = now_date - timedelta(days=i)
        end_date = now_date - timedelta(days=(i-1))
        count = 0
        try:
            count = User.query.filter(User.is_admin==False, User.last_login>=start_date,\
                                      User.last_login<=end_date).count()
            active_count.append(count)
            active_date.append(start_date.strftime("%Y-%m-%d"))
        except Exception as e:
            return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    active_count.reverse()
    active_date.reverse()

    data = {
        "user_count": total_count,
        "mon_count": month_count,
        "day_count": day_count,
        "active_date": active_date,
        "active_count": active_count,
    }

    return render_template("admin/user_count.html", data=data)

# 用户列表显示
@admin_blu.route("/user_list")
def user_list():
    # 获取参数
    page = request.args.get("page", 1)
    try:
        page = int(page)
    except Exception as e:
        print(e)

    items = None
    current_page = 1
    total_pages = 1

    # 查询所有用户
    try:
        paginate = User.query.filter(User.is_admin==False).order_by(User.create_time.desc()).paginate(
            page, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
        items = paginate.items
        current_page = paginate.page
        total_pages = paginate.pages
    except Exception as e:
        print(e)

    user_list = []
    for user in items:
        user_list.append(user.to_admin_dict())

    data = {
        "user_list": user_list,
        "current_page": current_page,
        "total_page": total_pages,
    }
    return render_template("admin/user_list.html", data=data)


# 新闻审核界面
@admin_blu.route("/news_review")
def news_review():
    page = request.args.get("p", 1)
    keywords = request.args.get("keywords", "")
    try:
        page = int(page)
    except Exception as e:
        return render_template("admin/news_review.html", errmsg="数据错误")

    items = []
    current_page = 1
    total_page = 1
    filters = [News.status!=0]
    if keywords:
        filters.append(News.title.contains(keywords))
    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(
            page, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)
        items = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        return render_template("admin/news_review.html", errmsg="数据库查询错误")

    news_list = []
    for new in items:
        news_list.append(new.to_review_dict())

    data = {
        "news_list": news_list,
        "current_page": current_page,
        "total_page": total_page,
    }
    return render_template("admin/news_review.html", data=data)


# 新闻审核详情页
@admin_blu.route("/news_review_detail", methods=['GET', 'POST'])
def news_review_detail():
    if request.method == 'GET':
        news_id = request.args.get("news_id", None)

        if not news_id:
            return render_template('admin/news_review_detail.html', errmsg='参数')

        try:
            news_id = int(news_id)
        except Exception as e:
            return render_template('admin/news_review_detail.html', errmsg='数据转换错误')

        try:
            news = News.query.get(news_id)
        except Exception as e:
            return render_template('admin/news_review_detail.html', errmsg='数据库查询错误')

        if not news:
            return render_template('admin/news_review_detail.html', errmsg='没有这条新闻')

        data = {
            "news": news.to_dict()
        }
        return render_template("admin/news_review_detail.html", data=data)

    # POST请求
    action = request.json.get("action")
    another_news_id = request.json.get("news_id")

    try:
        another_news_id = int(another_news_id)
    except Exception as e:
        return render_template('admin/news_review_detail.html', errmsg="参数错误")

    if not all([action, another_news_id]):
        return render_template('admin/news_review_detail.html', errmsg='参数不足')

    if action not in ['accept', 'reject']:
        return render_template('admin/news_review_detail.html', errmsg="参数错误")

    try:
        another_news = News.query.get(another_news_id)
    except Exception as e:
        return render_template('admin/news_review_detail.html', errmsg="数据库查询失败")

    if not another_news:
        return render_template('admin/news_review_detail.html', errmsg="参数错误")

    if action == "accept":
        another_news.status = 0
    else:
        reason = request.json.get("reason")

        if not reason:
            return render_template('admin/news_review_detail.html', errmsg="参数不足")

        another_news.status = -1
        another_news.reason = reason

    try:
        db.session.add(another_news)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return render_template('admin/news_review_detail.html', errmsg="数据库保存失败")

    return jsonify(errno=RET.OK, errmsg="ok")

# 新闻编辑
@admin_blu.route("/news_edit")
def news_edit():
    page = request.args.get("p", 1)
    keywords = request.args.get("keywords", "")

    try:
        page = int(page)
    except Exception as e:
        print(e)

    filters = []
    if keywords:
        filters.append(News.title.contains(keywords))

    items = []
    current_page = 1
    total_page = 1
    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(
            page, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)
        items = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        print(e)

    news_list = []
    for news in items:
        news_list.append(news.to_review_dict())

    data = {
        "news_list": news_list,
        "current_page": current_page,
        "total_page": total_page
    }
    return render_template("admin/news_edit.html", data=data)

# 新闻编辑详情页
@admin_blu.route("/news_edit_detail", methods=['GET', 'POST'])
def news_edit_detail():
    if request.method == 'GET':
        news_id = request.args.get("news_id")
        if not news_id:
            return render_template("admin/news_edit_detail.html", data={"errmsg": "没有这条新闻"})

        news = None
        try:
            news = News.query.get(news_id)
        except Exception as e:
            print(e)

        if not news:
            return render_template("admin/news_edit_detail.html", data={"errmsg": "没有这条新闻"})

        categories = None
        try:
            categories = Category.query.all()
        except Exception as e:
            print(e)

        if not categories:
            return render_template("admin/news_edit_detail.html", data={"errmsg": "没有这条新闻"})

        categories.pop(0)

        categories_list = []
        for category in categories:
            c_dict = category.to_dict()
            c_dict['is_selected'] = False
            if c_dict.get("id") == news.category_id:
                c_dict['is_selected'] = True
            categories_list.append(c_dict)

        data = {
            "news": news.to_dict(),
            "categories": categories_list
        }

        return render_template("admin/news_edit_detail.html", data=data)

    news_id = request.form.get("news_id")
    title = request.form.get("title")
    category_id = request.form.get("category_id")
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")

    if not all([news_id, title, category_id, digest, content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")

    if index_image:
        index_image = index_image.read()
        try:
            key = storage(index_image)
            news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
        except Exception as e:
            return jsonify(errno=RET.NODATA, errmsg="没有这个图片信息")

    news.title = title
    news.digest = digest
    news.content = content
    news.category_id = category_id

    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据库保存失败")

    return jsonify(errno=RET.OK, errmsg="ok")

# 分类展示
@admin_blu.route("/news_type", methods=['GET', 'POST'])
def news_type():
    if request.method == 'GET':
        try:
            categories = Category.query.all()
        except Exception as e:
            print(e)

        categories.pop(0)

        category_list = []
        for category in categories:
            category_list.append(category.to_dict())

        data = {
            "categories": category_list
        }
        return render_template("admin/news_type.html", data=data)

# 新闻分类修改
@admin_blu.route("/add_category", methods=['POST'])
def add_category():
    category_id = request.json.get("id", None)
    category_name = request.json.get("name", None)
    action = request.json.get("action", None)

    if category_id:
        try:
            category = Category.query.get(category_id)
        except Exception as e:
            return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

        if not category:
            return jsonify(errno=RET.NODATA, errmsg="没有这个数据")

        category.name = category_name
    else:
        category = Category()
        category.name = category_name

    try:
        if action != "removes":
            db.session.add(category)
        else:
            db.session.delete(category)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据库操作123失败")

    return jsonify(errno=RET.OK, errmsg="ok")
