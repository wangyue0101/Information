from datetime import datetime

from flask import render_template, g, redirect, request, jsonify, session

from info import db, constants, current_app
from info.model import Category, News, Comment, User
from info.utils.storage import storage
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import user_blu


@user_blu.route("/user_info")
@user_login_data
def show_user_info():
    user = g.user

    if not user:
        return redirect("/")
    data = {
        "user_info": user.to_dict()
    }
    return render_template("news/user.html", data=data)


# 基础资料
@user_blu.route("/base_info", methods=['GET', 'POST'])
@user_login_data
def show_base_user():
    user = g.user
    data = {
        "user_info": user.to_dict()
    }

    if request.method == 'GET':
        return render_template("news/user_base_info.html", data=data)

    signature = request.json.get("signature")
    nick_name = request.json.get("nick_name")
    gender = request.json.get("gender")

    if not all([signature, nick_name, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    if gender not in ['MAN', 'WOMAN']:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据库操作失败")

    session["nick_name"] = nick_name

    return jsonify(errno=RET.OK, errmsg="数据更新成功")


# 密码修改
@user_blu.route("/pass_info", methods=['GET', 'POST'])
@user_login_data
def update_pass_info():
    user = g.user
    data = {
        "user_info": user.to_dict()
    }
    if request.method =='GET':
        return render_template("news/user_pass_info.html", data=data)

    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")

    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if not user.check_passowrd(old_password):
        return jsonify(errno=RET.PWDERR, errmsg="密码错误")

    user.password = new_password
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据库提交错误")

    return jsonify(errno=RET.OK, errmsg="修改密码成功")


# 头像
@user_blu.route("/pic_info", methods=['GET', 'POST'])
@user_login_data
def update_pic_info():
    user = g.user
    data = {
        "user_info": user.to_dict()
    }
    if request.method == 'GET':
        return render_template("news/user_pic_info.html", data=data)

    #　获取上传的文件
    files = request.files.get("avatar")
    if not files:
        return jsonify(errno=RET.NODATA, errmsg="没有上传图片")

    files = files.read()

    # 将图片上传到七牛云
    try:
        url = storage(files)
    except Exception as e:
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")
    user.avatar_url = url
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户数据错误")

    return jsonify(errno=RET.OK, errmsg="头像上传成功", data={"avatar_url": constants.QINIU_DOMIN_PREFIX+url})


# 收藏新闻展示
@user_blu.route("/collection_info")
@user_login_data
def update_collection_info():
    user = g.user
    p = request.args.get("page", 1)
    try:
        page = int(p)
    except Exception as e:
        return jsonify(errno=RET.PARAMERR, errmsg="数据转换出错")

    items = []
    page = 1
    total_page = 1
    try:
        paginate = user.collection_news.paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)

        items = paginate.items
        page = paginate.page
        total_page = paginate.pages

    except Exception as e:
        return jsonify(errno=RET.DBERR, errmsg="数据库出错")

    collection_news = []
    for new in items:
        collection_news.append(new.to_basic_dict())

    data = {
        "user_info": user.to_dict(),
        "collection_news": collection_news
    }
    return render_template("news/user_collection.html", data=data)


# 新闻发布
@user_blu.route("/release_info", methods=['GET', 'POST'])
@user_login_data
def update_release_info():
    user = g.user
    if request.method == 'GET':
        categories = Category.query.all()

        categories.pop(0)

        data = {
            "user_info": user.to_dict(),
            "category": categories
        }
        return render_template("news/user_news_release.html", data=data)

    title = request.form.get("title")
    source = "个人发布"
    category_id = request.form.get("category_id")
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")


    if not all([title, source, category_id, digest, index_image, content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    index_image = index_image.read()
    try:
        url = storage(index_image)
    except Exception as e:
        return jsonify(errno=RET.THIRDERR, errmsg="图片保存错误")


    try:
        news = News()
        news.title = title
        news.source = source
        news.digest = digest
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + url
        news.content = content
        news.create_time = datetime.now()
        news.category_id = category_id
        news.user_id = user.id
        # 待审核状态
        news.status = 1
    except Exception as e:
        return jsonify(errno=RET.DBERR, errmsg="数据库错误1")

    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据库错误2")

    return jsonify(errno=RET.OK, errmsg="发布成功")


@user_blu.route("/user_news_list")
@user_login_data
def user_news_list():
    user = g.user
    p = request.args.get("page", 1)
    try:
        page = int(p)
    except Exception as e:
        return jsonify(errno=RET.PARAMERR, errmsg="数据转换错误")

    items = []
    page = 1
    total_page = 1
    try:
        paginate = News.query.filter(News.user_id == user.id).paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
        items = paginate.items
        page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    user_news_list = []
    for new in items:
        user_news_list.append(new.to_review_dict())

    data = {
        "user_info": user.to_dict(),
        "user_news_list": user_news_list,
        "page": page,
        "total_page": total_page
    }
    return render_template("news/user_news_list.html", data=data)


@user_blu.route("/<int:news_id>")
@user_login_data
def review(news_id):
    user = g.user
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        print(e)

    # 查询当前新闻下的所有评论
    comments = []
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.decs()).all()
    except Exception as e:
        print(e)

    comment_list = []
    for comment in comments:
        comment_list.append(comment.to_dict())

    data={
        "user_info": user.to_dict(),
        "news": news,
        "comment_list": comment_list
    }

    return render_template("news/user_review_news.html", data=data)


# 个人中心关注
@user_blu.route("/follow")
@user_login_data
def follow():
    user = g.user
    page = request.args.get("p", 1)


    items = None
    current_page = 1
    total_page = 1
    try:
        paginate = user.followers.paginate(page, constants.USER_FOLLOWED_MAX_COUNT, False)
        items = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        return render_template("news/user_follow.html", errmsg="查询错误")

    user_info_list = []
    for us_info in items:
        us_dict = us_info.to_dict()
        us_dict["fans"] = us_info.followed.count()
        us_dict["news"] = News.query.filter(News.user_id==us_info.id).count()
        user_info_list.append(us_dict)

    data = {
        "user_info": user_info_list,
        "current_page": current_page,
        "total_page": total_page,
    }

    return render_template("news/user_follow.html", data=data)

# 其他人
@user_blu.route("/other", methods=['GET', 'POST'])
@user_login_data
def other():
    user = g.user

    user_id = request.args.get("user_id")
    page = request.args.get("p", 1)

    user_info = None
    try:
        user_info = User.query.get(user_id)
    except Exception as e:
        print(e)

    if user:
        is_follow = False
        if user_info in user.followers:
            is_follow = True
        else:
            is_follow = False
    else:
        is_follow = False

    items = None
    current_page = 1
    total_page = 1
    try:
        paginate = user_info.news_list.paginate(page, constants.OTHER_NEWS_PAGE_MAX_COUNT, False)
        items = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        print(e)

    other_news_list = []
    for news in items:
        other_news_list.append(news.to_review_dict())

    data = {
        "user_info": user.to_dict() if user else [],
        "user": user_info.to_dict(),
        "news_list": other_news_list,
        "is_follow": is_follow
    }

    return render_template("news/other.html", data=data)