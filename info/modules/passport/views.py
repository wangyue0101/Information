import re

from flask import current_app, jsonify, request, abort
from info import constants, redis_store
from flask import request, render_template

from info.lib.yuntongxun.sms import CCP
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import image_passport_blu, sms_passport_blu


# 图片验证码的方法
@image_passport_blu.route("/image_code")
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
        redis_store.set("ImageCode_" + str(image_code_id), text, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据保存错误")

    return image


# 发送短信验证码
@sms_passport_blu.route("/sms_code", methods=['POST'])
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
    print(params_dict)
    print(mobile, type(mobile))

    # 检查参数是否全部传递了
    if not all([mobile, input_text, image_code_id]):
        return jsonify(errno=RET.DATAERR, errmsg="参数不全，请重新输入")

    # 检测输入的手机格式是否正确
    if not re.match(r"1[3-9]\d{9}", str(mobile)):
        return jsonify(error=RET.DATAERR, errmsg="手机号码格式不正确，请重新输入")
    try:
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
    sms_code = random.randint(100000, 999999)
    current_app.logger.debug("短信验证码的内容是： %s" % sms_code)
    result = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60], 1)
    print("result", result)
    try:
        redis_store.set("SMS_"+str(mobile), sms_code, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(errno=RET.DATAERR, errmsg="数据保存异常")
        return jsonify(errno=RET.DBERR, errmsg="短信验证码保存失败")
    return jsonify(errno=RET.OK, errmsg="发送成功")
