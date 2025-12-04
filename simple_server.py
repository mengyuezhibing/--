import http.server
import socketserver
import config

# 获取配置
config_obj = config.config['default']()

handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer((config_obj.HOST, config_obj.PORT_SIMPLE), handler) as httpd:
    print(f"简单HTTP服务器运行在 {config_obj.HOST}:{config_obj.PORT_SIMPLE}")
    print(f"公网访问地址: {config_obj.PUBLIC_URL.replace(str(config_obj.PORT_FLASK), str(config_obj.PORT_SIMPLE))}")
    httpd.serve_forever()
