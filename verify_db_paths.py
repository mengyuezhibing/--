#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证并更新数据库中的PDF路径
"""

import os
from app import create_app, db
from app.models import ReportData

def verify_and_update_paths():
    """
    验证并更新数据库中的PDF路径记录
    """
    app = create_app()
    with app.app_context():
        # 查询所有ReportData记录
        reports = ReportData.query.all()
        print(f"找到 {len(reports)} 条报告记录")
        
        # 特别检查包含'20251201_225000'的记录
        target_filename = 'report_20251201_225000_fallback.pdf'
        target_path = os.path.join('D:\任务\实训2\app\pdfs', target_filename)
        
        # 检查是否有记录指向这个文件
        updated = False
        for report in reports:
            if report.pdf_path and (target_filename in report.pdf_path or '20251201_225000' in report.pdf_path):
                print(f"\n找到匹配的记录：")
                print(f"ID: {report.id}")
                print(f"当前路径: {report.pdf_path}")
                print(f"标题: {report.title}")
                print(f"创建时间: {report.created_at}")
                
                # 确保路径正确指向我们刚刚创建的文件
                if not os.path.exists(report.pdf_path):
                    print(f"警告：路径 '{report.pdf_path}' 不存在")
                    # 更新为正确的路径
                    report.pdf_path = target_path
                    db.session.commit()
                    print(f"已更新路径为: {target_path}")
                    updated = True
                else:
                    print("路径正确，文件存在")
        
        if updated:
            print("\n数据库路径已成功更新")
        else:
            print("\n所有路径都已正确配置，无需更新")
        
        # 打印所有记录的路径信息
        print("\n所有报告记录的PDF路径：")
        for report in reports:
            status = "存在" if report.pdf_path and os.path.exists(report.pdf_path) else "不存在"
            print(f"ID: {report.id}, 路径: {report.pdf_path}, 状态: {status}")

if __name__ == "__main__":
    try:
        verify_and_update_paths()
    except Exception as e:
        print(f"错误：数据库检查失败 - {str(e)}")
