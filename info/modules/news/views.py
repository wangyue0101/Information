from flask import render_template, g, abort, jsonify, request
from info import current_app, constants
from info.model import News, Comment, CommentLike, User
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import news_blu
from info import db


@news_blu.route("/<int:news_id>")
@user_login_data
def news_details(news_id):
    user = g.user
    # 查询数据库中id所对应的那条新闻
    news_data = None
    try:
        news_data = News.query.get(news_id)
    except Exception as e:
        current_app.logger.debug(e)
        abort(404)

    user_info = None
    try:
        user_info = User.query.get(news_data.user_id)
    except Exception as e:
        print(e)


    fans_count = 0
    news_count = 0
    is_follow = False
    if user:
        if user_info:
            if user_info in user.followers:
                is_follow = True
            else:
                is_follow = False

            # fans_news_count = []
            # # 粉丝数和发表的新闻量
            # fans_news_count["fans_count"] = user_info.followed.count()
            # fans_news_count['']
            fans_count = user_info.followed.count() if user_info else 0
            news_count = user_info.news_list.count() if user_info else 0


    # 新闻点击之后，点击次数加1
    news_data.clicks += 1
    try:
        db.session.commit()
    except Exception as e:
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    # 查询数据库当前新闻下的所有评论
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).\
            order_by(Comment.create_time.desc()).all()
    except Exception as e:
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    commnent_likes_ids = []
    if user:
        try:
            comment_ids = [comment.id for comment in comments]
            # 获取当前用户在当前新闻下所有评论点赞的记录
            comment_likes = CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids),
                                                     CommentLike.user_id==user.id).all()

            # 取出记录中所有评论的ID
            comment_likes_ids = [comment_like.comment_id for comment_like in comment_likes]

        except Exception as e:
            current_app.logger.debug(e)



    comment_list = []
    for comment in comments if comments else []:
        comment_dict = comment.to_dict()
        # 是否点赞
        comment_dict["is_like"] = False
        if user and comment.id in comment_likes_ids:
            comment_dict["is_like"] = True
        comment_list.append(comment_dict)



    # 查询数据库中点击数最高的10条,点击排行
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    # 查询出的每条结果追加各个字段，并添加到新列表中
    click_new_dict = []
    for new in news_list:
        click_new_dict.append(new.to_basic_dict())

    # 是否收藏
    is_landing = False
    if user:
        if news_data in user.collection_news:
            is_landing = True

    data = {
        "news": news_data.to_dict(),
        "click_news": click_new_dict,
        "user_info": user.to_dict() if user else None,
        "front_comment": comment_list,
        "is_landing": is_landing,
        "is_follow": is_follow,
        "fans_count": fans_count,
        "news_count": news_count,
    }
    return render_template("news/detail.html", data=data)


# 新闻收藏
@news_blu.route("/news_collect", methods=['POST'])
@user_login_data
def news_collect():
    user = g.user
    news_id = request.json.get("news_id")
    action = request.json.get("action")
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    if not all([news_id, action]):
        current_app.logger.debug("参数不足")
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    if action not in ("collect", "cancel_collect"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    if action == "collect":
        if news_id not in user.collection_news:
            user.collection_news.append(news)
    elif action == "cancel_collect":
        user.collection_news.remove(news)


    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存失败")

    return jsonify(errno=RET.OK, errmsg="收藏成功")


# 评论
@news_blu.route("/news_comment", methods=['POST'])
@user_login_data
def news_comment():
    user = g.user

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    news_id = request.json.get("news_id")
    comment_str = request.json.get("comment")
    parent_id = request.json.get("parent_id")

    if not all([news_id, comment_str]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news_id = int(news_id)
        if parent_id:
            parent_id = int(parent_id)
    except Exception as e:
        return jsonify(errno=RET.DATAERR, errmsg="数据转换错误")

    try:
        news = News.query.get(news_id)
    except Exception as e:
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    if not news:
        return jsonify(errno=RET.PARAMERR, errmsg="没有这条新闻")

    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = comment_str
    if parent_id:
        comment.parent_id = parent_id

    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    return jsonify(errno=RET.OK, errmsg="操作成功", data=comment.to_dict())

# 点赞
@news_blu.route("/comment_like", methods=["POST"])
@user_login_data
def show_comment_like():
    user = g.user

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    comment_id = request.json.get("comment_id")
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    if not all([comment_id, news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ["add", "remove"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 当前评论
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    comment_like = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                            CommentLike.user_id == user.id).first()


    if action == "add":
        if not comment_like:
            comment_like = CommentLike()
            comment_like.user_id = user.id
            comment_like.comment_id = comment_id
            comment.like_count += 1
            db.session.add(comment_like)
    else:
        if comment_like:
            # db.session.delete(comment_like)
            comment.like_count -= 1
            # if comment.like_count <= 0:
            db.session.delete(comment_like)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")
    return jsonify(errno=RET.OK, errmsg="操作成功")

# 关注
@news_blu.route("/followed_user", methods=['POST'])
@user_login_data
def followed_user():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    user_id = request.json.get("user_id")
    action = request.json.get("action")

    if not all([user_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    if action not in ['follow', 'unfollow']:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不对")

    user_info = None
    try:
        user_info = User.query.get(user_id)
    except Exception as e:
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    if action == "follow":
        if user_id not in user.followers:
            user.followers.append(user_info)
    elif action == "unfollow":
        # if user_id in user.followers:
        user.followers.remove(user_info)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存错误")

    return jsonify(errno=RET.OK, errmsg="成功")
