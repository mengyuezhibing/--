# 网络数据抓取与分析系统

## 应用简介

本应用是一个综合性的网络数据抓取、分析和报告生成系统。它能够自动化地从指定来源抓取数据，进行清洗和多维度分析，并生成结构化的PDF分析报告。

## 主要功能

- **数据抓取**：自动化从网络获取数据并存储到数据库
- **数据清洗**：去重、过滤无效数据、处理缺失值
- **数据分析**：关键词分析、时间分布统计、来源分布统计、文本长度分析、文本摘要提取、智能洞察生成
- **报告生成**：将分析结果生成结构化的PDF报告
- **用户认证**：提供基本的用户登录和权限控制

## 技术栈

- **后端框架**：Flask
- **数据库**：SQLite
- **PDF生成**：通过WPS或文本格式作为备用方案
- **数据分析**：jieba分词、numpy
- **其他依赖**：详见requirements.txt

## 安装与配置

1. 克隆项目或下载源代码
2. 创建虚拟环境：
   ```bash
   python -m venv .venv
   ```
3. 激活虚拟环境：
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`
4. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

1. 启动应用服务器：
   ```bash
   python app.py
   ```
   - 此模式使用固定端口 **8081**
   - 访问地址：`http://localhost:8081`
   
   或使用简单服务器：
   ```bash
   python simple_server.py
   ```
   - 此模式使用固定端口 **8080**
   - 访问地址：`http://localhost:8080`

2. 使用管理员账户登录系统

3. 使用管理员账户登录系统

4. 配置抓取任务并执行数据抓取

5. 生成分析报告并下载PDF文件

## 项目结构

```
├── app.py              # 主应用入口
├── simple_server.py    # 简单服务器入口
├── app/                # 应用主目录
│   ├── __init__.py     # 应用初始化
│   ├── models.py       # 数据模型
│   ├── scraper.py      # 数据抓取模块
│   ├── data_analyzer.py # 数据分析模块
│   ├── pdf_generator.py # PDF生成模块
│   ├── data/           # 数据库目录
│   ├── pdfs/           # 生成的PDF报告目录
│   ├── templates/      # HTML模板
│   └── static/         # 静态资源
├── requirements.txt    # 依赖包列表
└── README.md           # 项目说明文档
```

## 注意事项

- 确保已安装jieba和numpy等必要的数据分析依赖
- PDF生成需要WPS或其他支持的办公软件
- 首次运行时系统会自动创建数据库
- 生成的报告保存在app/pdfs/目录下

## 维护与扩展

- 添加新的数据源：修改scraper.py
- 增强分析功能：扩展data_analyzer.py
- 自定义报告模板：调整pdf_generator.py
- 添加新功能模块：在app目录下创建新的模块

## 许可证

保留所有权利。本项目仅供学习和演示使用。

## 公网访问配置

### 配置文件说明

应用通过 `config.py` 文件集中管理所有配置，包括公网访问设置。主要配置项包括：

- `PUBLIC_HOST`：公网域名或IP地址
- `PUBLIC_PORT_HTTP`/`PUBLIC_PORT_HTTPS`：公网访问端口
- `ENABLE_HTTPS`：是否启用HTTPS

### 启用公网访问步骤

1. **修改配置文件**：
   编辑 `config.py` 文件，根据实际部署环境更新以下配置：
   ```python
   # 在ProductionConfig类中修改
   PUBLIC_HOST = 'your-public-domain.com'  # 修改为您的公网域名或IP
   ENABLE_HTTPS = True  # 可选：启用HTTPS
   ```

2. **端口映射配置**：
   - 如果使用云服务器，确保防火墙开放8080和8081端口
   - 如果在本地服务器上部署，需要在路由器上配置端口映射，将公网端口映射到本地端口

3. **域名解析**（如使用域名）：
   - 将您的域名解析到服务器的公网IP地址
   - 配置A记录或CNAME记录

4. **运行应用**：
   ```bash
   # 使用生产环境配置运行Flask应用
   set FLASK_ENV=production  # Windows
   # 或
   export FLASK_ENV=production  # Linux/Mac
   python app.py
   ```

### 反向代理配置（推荐）

对于生产环境，推荐使用Nginx作为反向代理，可以提供更好的性能和安全性：

```nginx
server {
    listen 80;
    server_name your-public-domain.com;
    
    # 重定向HTTP到HTTPS（如果启用HTTPS）
    # return 301 https://$host$request_uri;
    
    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTPS配置示例
# server {
#     listen 443 ssl;
#     server_name your-public-domain.com;
#     
#     ssl_certificate /path/to/cert.pem;
#     ssl_certificate_key /path/to/key.pem;
#     
#     location / {
#         proxy_pass http://127.0.0.1:8081;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#         proxy_set_header X-Forwarded-Proto $scheme;
#     }
# }
```

### 安全提示

- 生产环境务必修改 `SECRET_KEY` 为强密钥
- 建议启用HTTPS加密传输
- 定期更新依赖包以修复潜在安全漏洞
- 配置适当的访问控制和认证机制