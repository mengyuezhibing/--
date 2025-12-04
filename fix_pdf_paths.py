#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复数据库中PDF路径的脚本
直接将所有非.pdf结尾的路径改为.pdf结尾
"""
import os
import re
from app import create_app, db
from app.models import ReportData

app = create_app()

with app.app_context():
    # 查询所有非.pdf结尾的pdf_path记录
    all_reports = ReportData.query.all()
    reports_to_fix = []
    
    for report in all_reports:
        if report.pdf_path and not report.pdf_path.endswith('.pdf'):
            reports_to_fix.append(report)
    
    if not reports_to_fix:
        print("没有发现需要修复的PDF路径记录")
    else:
        print(f"发现{len(reports_to_fix)}条需要修复的记录")
        
        for report in reports_to_fix:
            old_path = report.pdf_path
            # 使用正则表达式替换扩展名
            # 保留文件名和_fallback标识，只修改扩展名
            base_name = os.path.splitext(old_path)[0]
            new_path = base_name + '.pdf'
            
            # 直接更新数据库
            report.pdf_path = new_path
            print(f"已修复: {old_path} -> {new_path}")
        
        # 提交更改到数据库
        try:
            db.session.commit()
            print("数据库更新完成")
            
            # 再次检查以确认修复
            updated_reports = ReportData.query.filter(~ReportData.pdf_path.like('%.pdf')).all()
            if updated_reports:
                print(f"警告: 仍有{len(updated_reports)}条记录未能修复")
            else:
                print("所有记录已成功修复为.pdf扩展名")
        except Exception as e:
            db.session.rollback()
            print(f"数据库更新失败: {str(e)}")

