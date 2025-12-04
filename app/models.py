from . import db
from flask_login import UserMixin
from datetime import datetime
import hashlib

def hash_password(password):
    """简单的密码哈希函数"""
    return hashlib.md5(password.encode()).hexdigest()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    
    def check_password(self, password):
        """验证密码"""
        return self.password == hash_password(password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class ScrapedData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(500), nullable=True)
    source = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    saved = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<ScrapedData {self.title}>'

class ReportData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pdf_path = db.Column(db.String(500), nullable=True)
    
    def __repr__(self):
        return f'<ReportData {self.title}>'
