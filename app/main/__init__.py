from flask import Blueprint

main = Blueprint('main', __name__)


# 为什么在末尾导入？避免循环导入/依赖/import
# https://segmentfault.com/q/1010000010937917
# 狗书中文版P90
from app.main import views
from app.main import models
from app.main import forms
from app.main import errors