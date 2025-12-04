#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试数据库中的PDF路径修复是否成功
"""
from app import create_app, db
from app.models import ReportData

app = create_app()

with app.app_context():
    # 获取所有报告记录
    all_reports = ReportData.query.all()
    print(f"总共有{len(all_reports)}条报告记录")
    
    # 检查所有记录的pdf_path是否都以.pdf结尾
    all_correct = True
    for report in all_reports:
        if report.pdf_path:
            if not report.pdf_path.endswith('.pdf'):
                print(f"错误: 记录ID {report.id} 的路径不是PDF格式: {report.pdf_path}")
                all_correct = False
            else:
                print(f"正确: 记录ID {report.id} 的路径是PDF格式: {report.pdf_path}")
        else:
            print(f"警告: 记录ID {report.id} 的路径为空")
    
    if all_correct:
        print("\n✅ 所有PDF路径已修复成功！")
    else:
        print("\n❌ 仍有错误的PDF路径需要修复")
