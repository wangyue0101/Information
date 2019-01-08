from info import constants
from info.model import User, News, Category
from info.utils.response_code import RET
from . import index_blu
from flask import render_template, current_app, session, jsonify, request


@index_blu.route("/")
def index():
    user_id = session.get("user_id")
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.warning("user_id在数据库中查询错误")

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
    print("click_new_dict", click_new_dict)

    # 查询新闻类别数据，上方新闻类别
    try:
        categorys = Category.query.all()
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")


    categories_new_dict = []
    for ctgory in categorys:
        categories_new_dict.append(ctgory.to_dict())
    print("categories_new_dict", categories_new_dict)

    data = {
        "user_info": user.to_dict() if user else None,
        "click_news": click_new_dict,
        "category_news": categories_new_dict,
    }
    return render_template("news/index.html", data=data)


# 各分类下的的新闻列表
@index_blu.route("/news_list")
def get_news_list():
    """
    获取指定分类新闻的列表
    1. 获取参数
    2. 校验参数
    3. 查询数据
    4. 返回数据
    :return:
    """
    # 获取参数
    pramas_dict = request.args
    current_cid = pramas_dict.get("cid", "1")
    page = pramas_dict.get("page", "1")
    per_page = pramas_dict.get("per_page", "10")

    # 校验参数
    try:
        current_cid = int(current_cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数转换错误")

    # 查询条件列表
    result_filter = [News.status == 0]
    if current_cid != 1:
        result_filter.append(News.category_id == current_cid)

    # 查询数据库将最新时间的新闻放在上面，并且分页
    try:
        paginates = News.query.filter(*result_filter).order_by(
            News.create_time.desc()).paginate(page, per_page, False)

        # 当前页所有记录内容
        items = paginates.items
        # 当前页数
        current_page = paginates.page
        # 总页数
        total_page = paginates.pages
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    # 定义一个空列表，保存每条新闻的信息
    news_info_dict = []
    for new in items:
        news_info_dict.append(new.to_basic_dict())

    data = {
        "cid": current_cid,
        "current_page": current_page,
        "total_pages": total_page,
        "news_info": news_info_dict,
    }

    return jsonify(errno=RET.OK, errmsg="Ok", data=data)




@index_blu.route("/favicon.ico")
def favicon():
    return current_app.send_static_file("news/favicon.ico")