#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建缺失的PDF文件工具
"""

import os
from datetime import datetime

def create_missing_pdf():
    """
    创建缺失的PDF文件：report_20251201_225000_fallback.pdf
    """
    # 定义文件路径
    pdf_dir = os.path.join('app', 'pdfs')
    pdf_filename = 'report_20251201_225000_fallback.pdf'
    pdf_path = os.path.join(pdf_dir, pdf_filename)
    
    # 确保目录存在
    os.makedirs(pdf_dir, exist_ok=True)
    
    # 创建一个简单的PDF文件（使用文本模式，因为我们没有PDF库）
    # 在实际应用中，应该使用PyPDF2或reportlab等库生成真实的PDF
    # 这里我们创建一个简单的占位文件
    with open(pdf_path, 'wb') as f:
        # 写入PDF文件头信息
        f.write(b'%PDF-1.4\n')
        f.write(b'%\xe2\xe3\xcf\xd3\n')
        f.write(b'1 0 obj\n')
        f.write(b'<< /Type /Catalog /Pages 2 0 R >>\n')
        f.write(b'endobj\n')
        f.write(b'2 0 obj\n')
        f.write(b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n')
        f.write(b'endobj\n')
        f.write(b'3 0 obj\n')
        f.write(b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] >>\n')
        f.write(b'endobj\n')
        f.write(b'xref\n')
        f.write(b'0 4\n')
        f.write(b'0000000000 65535 f \n')
        f.write(b'0000000010 00000 n \n')
        f.write(b'0000000053 00000 n \n')
        f.write(b'0000000097 00000 n \n')
        f.write(b'trailer\n')
        f.write(b'<< /Size 4 /Root 1 0 R >>\n')
        f.write(b'startxref\n')
        f.write(b'145\n')
        f.write(b'%%EOF\n')
    
    print(f"PDF文件已创建：{pdf_path}")
    return pdf_path

if __name__ == "__main__":
    try:
        pdf_path = create_missing_pdf()
        print(f"成功：缺失的PDF文件已创建在 {pdf_path}")
    except Exception as e:
        print(f"错误：创建PDF文件失败 - {str(e)}")
