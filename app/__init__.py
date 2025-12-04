from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# 初始化数据库
db = SQLAlchemy()
# 初始化登录管理器
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    # 创建Flask应用
    app = Flask(__name__)
    
    # 配置应用
    app.config['SECRET_KEY'] = 'your-secret-key'
    # 使用应用内部的数据库路径
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'data', 'app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    
    # 确保数据目录存在
    os.makedirs(os.path.join(app.root_path, 'data'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'templates'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'pdfs'), exist_ok=True)
    
    # 注册蓝图
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        # 创建默认管理员用户
        from .models import User, hash_password
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password=hash_password('admin888'))
            db.session.add(admin)
            db.session.commit()
    
    return app
