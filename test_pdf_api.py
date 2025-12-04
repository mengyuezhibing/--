import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入PDF生成模块
from app.pdf_generator import generate_pdf

class MockDataItem:
    """模拟数据项类，用于测试PDF生成"""
    def __init__(self, title, source, created_at):
        self.title = title
        self.source = source
        self.created_at = created_at
        self.content = f"这是测试内容：{title}"

def main():
    """测试PDF生成功能"""
    print("开始测试PDF生成功能...")
    
    # 创建测试数据
    test_items = [
        MockDataItem("测试标题1", "来源A", datetime(2025, 12, 1)),
        MockDataItem("测试标题2", "来源B", datetime(2025, 12, 2)),
        MockDataItem("测试标题3", "来源A", datetime(2025, 12, 3))
    ]
    
    # 测试标题
    test_title = "API生成PDF测试报告"
    
    try:
        # 调用PDF生成函数
        pdf_path = generate_pdf(test_title, test_items)
        print(f"测试成功！生成的PDF路径: {pdf_path}")
        print("PDF生成功能正常工作。")
        return 0
    except Exception as e:
        print(f"测试失败！错误信息: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())