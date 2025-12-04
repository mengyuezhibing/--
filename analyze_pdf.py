import os
import sys

# 尝试使用PyPDF2或PyPDF4库
pdflib = None
try:
    import PyPDF4 as pdflib
    print("使用PyPDF4库分析PDF")
except ImportError:
    try:
        import PyPDF2 as pdflib
        print("使用PyPDF2库分析PDF")
    except ImportError:
        print("无法导入PDF处理库，请安装PyPDF2或PyPDF4")

# PDF文件路径
pdf_path = "d:\\任务\\实训2\\app\\pdfs\\report_20251201_231804.pdf"

print(f"分析PDF文件: {pdf_path}")
print(f"文件大小: {os.path.getsize(pdf_path)} 字节")
print(f"文件是否存在: {os.path.exists(pdf_path)}")

# 检查文件头是否为PDF
with open(pdf_path, 'rb') as f:
    header = f.read(10)
    print(f"文件头: {header}")
    if header.startswith(b'%PDF-'):
        print("✓ 文件头正确，符合PDF标准")
    else:
        print("✗ 文件头不正确，可能不是标准PDF文件")

# 尝试使用PDF库打开并检查
if pdflib:
    try:
        with open(pdf_path, 'rb') as file:
            reader = pdflib.PdfFileReader(file)
            print(f"PDF版本: {reader.getDocumentInfo()}")
            print(f"页数: {reader.getNumPages()}")
            
            # 尝试读取第一页内容
            if reader.getNumPages() > 0:
                page = reader.getPage(0)
                text = page.extractText()
                print(f"第一页文本长度: {len(text)} 字符")
                print("第一页文本前200字符:")
                print(text[:200] + "...")
                print("✓ PDF文件可读且包含文本内容")
            else:
                print("✗ PDF文件不包含页面")
    except Exception as e:
        print(f"✗ 使用PDF库分析时出错: {str(e)}")
