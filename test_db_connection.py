from app import create_app, db
from flask import Flask

print("正在测试数据库连接...")

# 创建应用实例
app = create_app()

# 在应用上下文中测试数据库连接
try:
    with app.app_context():
        # 尝试执行一个简单的数据库操作
        result = db.engine.execute("SELECT 1")
        print("数据库连接成功!")
        print(f"测试结果: {result.fetchone()[0]}")
        
        # 尝试检查表结构
        from app.models import User
        tables = db.engine.table_names()
        print(f"数据库中的表: {tables}")
        
        # 尝试查询用户表
        users = User.query.all()
        print(f"用户数量: {len(users)}")
        for user in users:
            print(f"用户名: {user.username}")
            
except Exception as e:
    print(f"数据库连接失败: {str(e)}")
    import traceback
    traceback.print_exc()

print("测试完成。")