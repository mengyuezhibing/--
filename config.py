"""应用配置文件

此文件包含应用的所有配置参数，包括公网访问设置、端口配置等。
请根据实际部署环境修改相应配置。
"""

import os
from datetime import timedelta


class Config:
    """基础配置类"""
    # 应用名称
    APP_NAME = "网络数据抓取与分析系统"
    
    # 密钥配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app/data/app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 文件上传配置
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # PDF生成配置
    PDF_FOLDER = 'app/pdfs'
    
    # ====== 网络访问配置 ======
    
    # 主机配置 - '0.0.0.0' 允许所有网络接口访问
    HOST = '0.0.0.0'
    
    # 端口配置
    PORT_FLASK = 8081  # Flask应用端口
    PORT_SIMPLE = 8080  # 简单服务器端口
    
    # ====== 公网访问配置 ======
    
    # 公网地址配置 - 请根据实际情况修改
    # 以下为示例配置，需要根据实际部署环境填写
    PUBLIC_HOST = 'example.com'  # 公网域名或IP地址
    
    # 公网端口 - 通常为80(HTTP)或443(HTTPS)
    PUBLIC_PORT_HTTP = 80
    PUBLIC_PORT_HTTPS = 443
    
    # 是否启用HTTPS
    ENABLE_HTTPS = False
    
    # 公网完整URL构建
    @property
    def PUBLIC_URL(self):
        protocol = 'https' if self.ENABLE_HTTPS else 'http'
        port = self.PUBLIC_PORT_HTTPS if self.ENABLE_HTTPS else self.PUBLIC_PORT_HTTP
        # 如果是标准端口(80/443)，则不需要在URL中显示端口
        if (protocol == 'http' and port == 80) or (protocol == 'https' and port == 443):
            return f"{protocol}://{self.PUBLIC_HOST}"
        else:
            return f"{protocol}://{self.PUBLIC_HOST}:{port}"
    

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    # 开发环境下的公网访问示例
    PUBLIC_HOST = 'localhost'  # 开发环境通常使用localhost
    PUBLIC_PORT_HTTP = 8081  # 与Flask应用端口保持一致


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # 生产环境必须设置强密钥
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # 生产环境公网配置
    PUBLIC_HOST = 'your-public-domain.com'  # 修改为实际公网域名
    ENABLE_HTTPS = True  # 生产环境建议启用HTTPS


# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


# ====== 网络通道配置说明 ======
"""
如果需要公网访问，可能需要配置以下内容：

1. 端口映射配置：
   - 在云服务器或路由器上配置端口映射
   - 将公网IP的80/443端口映射到应用服务器的8080/8081端口

2. 防火墙配置：
   - 确保服务器防火墙允许8080和8081端口的入站连接
   - 配置命令示例（Linux）：
     sudo ufw allow 8080/tcp
     sudo ufw allow 8081/tcp

3. 域名解析（如果使用域名）：
   - 将域名解析到公网IP地址
   - 配置A记录或CNAME记录

4. HTTPS配置（可选）：
   - 可以使用Nginx反向代理并配置SSL证书
   - 或使用Let's Encrypt获取免费SSL证书

5. 反向代理配置示例（Nginx）：
   server {
       listen 80;
       server_name your-public-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8081;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
"""
