from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from . import auth
from ..models import User, hash_password
from .. import login_manager, db

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 查找用户
        user = User.query.filter_by(username=username).first()
        
        # 使用哈希密码验证
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('用户名或密码错误')
    
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在，请选择其他用户名')
            return redirect(url_for('auth.register'))
        
        # 检查密码是否一致
        if password != confirm_password:
            flash('两次输入的密码不一致')
            return redirect(url_for('auth.register'))
        
        # 检查密码长度
        if len(password) < 6:
            flash('密码长度至少为6位')
            return redirect(url_for('auth.register'))
        
        # 创建新用户
        new_user = User(username=username, password=hash_password(password))
        db.session.add(new_user)
        db.session.commit()
        
        flash('注册成功，请登录')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')
