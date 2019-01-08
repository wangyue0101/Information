import re
from datetime import datetime
from flask import current_app, jsonify, request, abort, session
from info import constants, redis_store, db
from flask import request, render_template

from info.lib.yuntongxun.sms import CCP
from info.model import User
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import passport_blu


# 图片验证码的方法
@passport_blu.route("/image_code")
def image_passport():
    '''
        1.获取浏览器传过来的参数uuid
        2.校验参数
        3.生成图片验证码
        4.redis保存uuid和图验证码文本信息
        5.返回验证码图片
    '''
    # 1. 获取当前的图片编号ID
    image_code_id = request.args.get("code_id")

    # 2校验是否有参数
    if not image_code_id:
        current_app.logger.debug("未获取到参数")
        abort(403)

    # 3. 生成图片验证码
    name, text, image = captcha.generate_captcha()
    print(text)

    # 4. 将验证码保存到Redis中
    try:
        redis_store.set("ImageCode_" + image_code_id, text, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据保存错误")

    return image


# 发送短信验证码
@passport_blu.route("/sms_code", methods=['POST'])
def sms_passport():
    """
    1. 接收参数并判断是否有值
    2. 校验手机号是正确
    3. 通过传入的图片编码去redis中查询真实的图片验证码内容
    4. 进行验证码内容的比对
    5. 生成发送短信的内容并发送短信
    6. redis中保存短信验证码内容
    7. 返回发送成功的响应
    :return:
    """

    # 1接受请求值中的内容
    params_dict = request.json
    mobile = params_dict.get("mobile")
    input_text = params_dict.get("image_code")
    image_code_id = params_dict.get("image_code_id")

    # 检查参数是否全部传递了
    if not all([mobile, input_text, image_code_id]):
        return jsonify(errno=RET.DATAERR, errmsg="参数不全，请重新输入")

    # 检测输入的手机格式是否正确
    if not re.match(r"1[3-9]\d{9}", mobile):
        return jsonify(error=RET.DATAERR, errmsg="手机号码格式不正确，请重新输入")
    try:
        # redis_store.set("sms_" + mobile, mobile)
        result_image = redis_store.get("ImageCode_" + image_code_id)
        if result_image:
            redis_store.delete("ImageCode_" + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="没有查询到数据")

    # 判断验证码是否正确
    if input_text.upper() != result_image.upper():
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码错误")

    # 发送短信验证码
    import random
    psms_code = random.randint(100000, 999999)
    print("sms_code", psms_code)
    current_app.logger.debug("短信验证码的内容是： %s" % psms_code)
    result = CCP().send_template_sms(mobile, [psms_code, constants.SMS_CODE_REDIS_EXPIRES / 60], 1)
    try:
        redis_store.set("SMS_"+str(mobile), psms_code, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(errno=RET.DATAERR, errmsg="数据保存异常")
        return jsonify(errno=RET.DBERR, errmsg="短信验证码保存失败")
    return jsonify(errno=RET.OK, errmsg="发送成功")


# 点击注册功能
@passport_blu.route("/register", methods=['GET', 'POST'])
def register_validate():
    '''
    :return:
    '''
    # 获取参数
    params_dict = request.json
    mobile = params_dict.get("mobile")
    sms_code = params_dict.get("sms_code")
    password = params_dict.get("password")

    # 判断参数是否有值
    if not all([mobile, sms_code, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足，请重新输入")

    # 判断输入的SMS_CODE和数据库中的SMS_CODE是否一致
    try:
        resp_sms_code = redis_store.get("SMS_" + mobile)
    except Exception as e:
        return jsonify(errno=RET.DBERR, errmsg="数据查询1出错")
    if sms_code != resp_sms_code:
        return jsonify(errno=RET.PARAMERR, errmsg="短信验证码输入错误")

    # 判断密码输入是否规范
    if len(password) < 6:
        return jsonify(errno=RET.DATAERR, errmsg="密码不规范")

    # 判断手机号码是否已经注册
    user = None
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.warning(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询2出错")

    # 如果数据库可以查询到手机号码，则不能注册
    if user:
        return jsonify(errno=RET.DATAEXIST, errmsg="手机号码已经注册过")


    # 如果没有查询到，则将信息保存到数据库中
    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    user.password = password
    user.last_login = datetime.now()
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据提交出错")

    # 保存用户的登陆状态
    session["user_id"] = user.id
    session['nick_name'] = user.nick_name
    session['mobile'] = user.mobile
    session["is_admin"] = False
    # 返回注册的结果
    session.get("user_id")
    session.get("nick_name")
    session.get("mobile")
    return jsonify(errno=RET.OK, errmsg="OK")


# 登陆
@passport_blu.route("/login", methods=['POST'])
def login_validate():
    # 获取参数
    params_dict = request.json
    mobile = params_dict.get("mobile")
    password = params_dict.get("password")

    # 验证参数是否齐全
    if not all([mobile, password]):
        current_app.logger.warning("登陆参数不足")
        return jsonify(errno=RET.PARAMERR, errmsg="请填写登陆信息")

    # 判断手机号码是否已经注册
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.debug("数据库未查询到数据")
        return jsonify(errno=RET.DBERR, errmsg="查询错误")

    # 如果没有查询到，则提示注册
    if not user:
        return jsonify(errno=RET.UNKOWNERR, errmsg="用户不存在，请前往注册")

    # 判断密码和数据库中加密的密码是否一致
    if not user.check_passowrd(password):
        return jsonify(errno=RET.PARAMERR, errmsg="密码错误")

    # 保存用户登录状态
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    session["is_admin"] = user.is_admin
    # 记录用户的登陆时间
    user.last_login = datetime.now()

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据提交错误")

    #
    return jsonify(errno=RET.OK, errmsg="登陆成功")


# 退出控制
@passport_blu.route("/logout", methods=['POST'])
def logout_validate():
    session.pop("user_id", None)
    session.pop("mobile", None)
    session.pop("nick_name", None)
    session.pop('is_admin', None)

    return jsonify(errno=RET.OK, errmsg="推出成功")








