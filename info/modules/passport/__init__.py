from flask import Blueprint

image_passport_blu = Blueprint("image_passport", __name__, url_prefix="/passport")
sms_passport_blu = Blueprint("sms_passport", __name__, url_prefix="/passport")


from .views import *
