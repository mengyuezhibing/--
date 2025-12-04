from app import create_app
import config

# 获取配置
config_obj = config.config['default']()

# 创建Flask应用实例
app = create_app()

if __name__ == '__main__':
    # 启动应用 - 从配置文件读取设置
    app.run(
        debug=config_obj.DEBUG,
        host=config_obj.HOST,
        port=config_obj.PORT_FLASK
    )
    print(f"应用已启动，访问地址: {config_obj.PUBLIC_URL}")
