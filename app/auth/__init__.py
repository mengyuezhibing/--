from flask import Blueprint

# 创建认证蓝图
auth = Blueprint('auth', __name__)

# 导入视图
from . import views
