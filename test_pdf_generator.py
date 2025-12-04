from app.pdf_generator import generate_pdf
from datetime import datetime

# 模拟数据项类
class MockDataItem:
    def __init__(self, title, source, created_at):
        self.title = title
        self.source = source
        self.created_at = created_at

# 创建一些包含中文的数据项
mock_data = [
    MockDataItem("这是第一个中文标题测试", "来源A", datetime.now()),
    MockDataItem("第二个测试项目，包含更长的中文内容", "来源B", datetime.now()),
    MockDataItem("测试数据3，看看PDF是否能正确显示中文", "来源C", datetime.now())
]

# 生成PDF
print("正在生成测试PDF...")
pdf_path = generate_pdf("PDF中文显示测试报告", mock_data)
print(f"PDF生成成功！文件保存路径: {pdf_path}")
print("请检查PDF文件中的中文是否正常显示。")