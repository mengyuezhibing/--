from flask import render_template, request, redirect, url_for, jsonify, flash, send_file
from flask_login import login_required
from . import main
from .. import db
from ..models import ScrapedData, ReportData
from ..scraper import scrape_baidu
from ..pdf_generator import generate_pdf
import os
from datetime import datetime

@main.route('/')
@login_required
def index():
    # 获取统计数据
    total_data = ScrapedData.query.filter_by(saved=True).count()
    total_reports = ReportData.query.count()
    
    # 获取最近活动记录
    recent_activities = []
    
    # 添加最近爬取记录
    recent_scrapes = ScrapedData.query.filter_by(saved=False).order_by(ScrapedData.created_at.desc()).limit(3).all()
    for scrape in recent_scrapes:
        recent_activities.append({
            'time': scrape.created_at.strftime('%Y-%m-%d %H:%M'),
            'action': f'爬取关键词: {scrape.keyword}'
        })
    
    # 添加最近保存记录
    recent_saves = ScrapedData.query.filter_by(saved=True).order_by(ScrapedData.created_at.desc()).limit(3).all()
    for save in recent_saves:
        recent_activities.append({
            'time': save.created_at.strftime('%Y-%m-%d %H:%M'),
            'action': f'保存数据: {save.title[:30]}...'
        })
    
    # 添加最近报告生成记录
    recent_reports = ReportData.query.order_by(ReportData.created_at.desc()).limit(3).all()
    for report in recent_reports:
        recent_activities.append({
            'time': report.created_at.strftime('%Y-%m-%d %H:%M'),
            'action': f'生成报告: {report.title[:30]}...'
        })
    
    # 按时间排序并限制数量
    recent_activities.sort(key=lambda x: x['time'], reverse=True)
    recent_activities = recent_activities[:5]
    
    return render_template('main/index.html', 
                           total_data=total_data, 
                           total_reports=total_reports, 
                           recent_activities=recent_activities)

@main.route('/scrape', methods=['POST'])
@login_required
def scrape():
    keyword = request.form.get('keyword')
    if not keyword:
        flash('请输入关键词')
        return redirect(url_for('main.index'))
    
    # 调用百度爬虫
    results = scrape_baidu(keyword)
    
    # 保存爬取结果到数据库（临时状态）
    for result in results:
        data = ScrapedData(
            keyword=keyword,
            title=result['title'],
            content=result.get('content', ''),
            url=result.get('url', ''),
            source='百度',
            saved=False
        )
        db.session.add(data)
    db.session.commit()
    
    return redirect(url_for('main.results', keyword=keyword))

@main.route('/results')
@login_required
def results():
    keyword = request.args.get('keyword')
    if keyword:
        data = ScrapedData.query.filter_by(keyword=keyword, saved=False).all()
    else:
        data = []
    return render_template('main/results.html', data=data, keyword=keyword)

@main.route('/save_data', methods=['POST'])
@login_required
def save_data():
    data_ids = request.form.getlist('data_ids')
    if not data_ids:
        flash('请选择要保存的数据')
        return redirect(url_for('main.index'))
    
    # 更新数据状态为已保存
    ScrapedData.query.filter(ScrapedData.id.in_(data_ids)).update({'saved': True})
    db.session.commit()
    
    flash('数据保存成功')
    return redirect(url_for('main.data_warehouse'))

@main.route('/data_warehouse')
@login_required
def data_warehouse():
    # 获取所有已保存的数据
    data = ScrapedData.query.filter_by(saved=True).order_by(ScrapedData.created_at.desc()).all()
    
    # 按日期分组
    data_by_date = {}
    for item in data:
        date_key = item.created_at.strftime('%Y-%m-%d')
        if date_key not in data_by_date:
            data_by_date[date_key] = []
        data_by_date[date_key].append(item)
    
    return render_template('main/data_warehouse.html', data_by_date=data_by_date)

@main.route('/search_data', methods=['POST'])
@login_required
def search_data():
    keyword = request.form.get('search_keyword')
    if not keyword:
        return redirect(url_for('main.data_warehouse'))
    
    # 搜索包含关键词的数据
    results = ScrapedData.query.filter(
        ScrapedData.saved == True,
        (ScrapedData.title.contains(keyword) | ScrapedData.content.contains(keyword) | ScrapedData.keyword.contains(keyword))
    ).all()
    
    # 按日期分组
    data_by_date = {}
    for item in results:
        date_key = item.created_at.strftime('%Y-%m-%d')
        if date_key not in data_by_date:
            data_by_date[date_key] = []
        data_by_date[date_key].append(item)
    
    return render_template('main/data_warehouse.html', data_by_date=data_by_date, search_keyword=keyword)

@main.route('/generate_pdf', methods=['POST'])
@login_required
def generate_pdf_report():
    data_ids = request.form.getlist('selected_data')
    if not data_ids:
        flash('请选择要生成PDF的数据')
        return redirect(url_for('main.data_warehouse'))
    
    # 获取选中的数据
    selected_data = ScrapedData.query.filter(ScrapedData.id.in_(data_ids)).all()
    
    # 使用文章标题作为报告标题
    if len(selected_data) == 1:
        # 如果只选了一篇文章，直接使用该文章标题
        article_title = selected_data[0].title
        report_title = f'报告: {article_title}'
    else:
        # 如果选了多篇文章，使用关键词或第一篇文章的标题加上数量
        first_title = selected_data[0].title[:30]  # 取前30个字符
        report_title = f'报告: {first_title}... 等{len(selected_data)}篇文章'
    
    # 生成PDF
    pdf_path = generate_pdf(report_title, selected_data)
    
    # 保存报告信息到数据库
    report_content = '\n\n'.join([f'标题: {item.title}\n内容: {item.content}' for item in selected_data])
    report = ReportData(
        title=report_title,
        content=report_content,
        pdf_path=pdf_path
    )
    db.session.add(report)
    db.session.commit()
    
    # 检查文件扩展名，确保正确设置MIME类型
    file_ext = os.path.splitext(pdf_path)[1].lower()
    mimetype = 'application/pdf' if file_ext == '.pdf' else 'text/plain'
    
    print(f"发送文件: {pdf_path}, 扩展名: {file_ext}, MIME类型: {mimetype}")
    
    return send_file(pdf_path, as_attachment=True, download_name=f'{report_title}{file_ext}', mimetype=mimetype)

@main.route('/reports')
@login_required
def reports():
    reports = ReportData.query.order_by(ReportData.created_at.desc()).all()
    return render_template('main/reports.html', reports=reports)

@main.route('/view_pdf/<int:report_id>')
@login_required
def view_pdf(report_id):
    report = ReportData.query.get_or_404(report_id)
    return send_file(report.pdf_path, mimetype='application/pdf')

@main.route('/download_pdf/<int:report_id>')
@login_required
def download_pdf(report_id):
    report = ReportData.query.get_or_404(report_id)
    return send_file(report.pdf_path, as_attachment=True)

@main.route('/delete_pdf/<int:report_id>', methods=['POST'])
@login_required
def delete_pdf(report_id):
    # 获取报告记录
    report = ReportData.query.get_or_404(report_id)
    
    # 删除PDF文件
    if report.pdf_path and os.path.exists(report.pdf_path):
        try:
            os.remove(report.pdf_path)
        except Exception as e:
            flash(f'删除文件时出错: {str(e)}')
    
    # 从数据库中删除报告记录
    db.session.delete(report)
    db.session.commit()
    
    flash('报告删除成功')
    return redirect(url_for('main.reports'))
