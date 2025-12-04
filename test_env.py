print("Python环境测试")
print("尝试导入基本模块...")

try:
    import sys
    print(f"Python版本: {sys.version}")
except Exception as e:
    print(f"导入sys模块失败: {e}")

try:
    # 尝试简单的HTTP服务器
    import http.server
    import socketserver
    print("HTTP模块可用")
except Exception as e:
    print(f"导入HTTP模块失败: {e}")
