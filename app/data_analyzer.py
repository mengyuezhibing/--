import re
import jieba
import jieba.analyse
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import numpy as np

class DataAnalyzer:
    """
    数据分析器，提供数据清洗和分析功能
    """
    
    def __init__(self):
        # 初始化停用词列表
        self.stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到',
            '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '与', '对', '吗', '呢', '吧',
            '啊', '哦', '呀', '嘛', '啦', '嗯', '哼', '哈', '嘿', '喂', '哎', '哟', '哦', '哇', '哒', '啦',
            '但是', '如果', '因为', '所以', '不过', '虽然', '但是', '而且', '并且', '然而', '可是', '或者',
            '还是', '不仅', '而是', '就是', '只是', '不是', '关于', '对于', '为了', '随着', '通过', '由于',
            '根据', '按照', '因此', '于是', '总之', '综上所述', '由此可见', '显而易见', '事实上', '实际上',
            '其实', '确实', '看来', '据说', '听说', '据悉', '据悉', '据了解', '据报道', '据分析', '据估计',
            '可以', '能够', '应该', '必须', '需要', '可能', '或许', '也许', '大概', '大约', '左右', '前后',
            '上下', '之间', '其中', '之后', '之前', '当时', '现在', '将来', '过去', '目前', '最近', '未来'
        }
        
        # 初始化jieba
        self._init_jieba()
    
    def _init_jieba(self):
        """初始化jieba分词器"""
        # 可以在这里添加自定义词典
        try:
            # 尝试加载停用词（如果有）
            pass
        except:
            pass
    
    def clean_data(self, data_items):
        """
        数据清洗
        1. 去重
        2. 过滤无效数据
        3. 处理缺失值
        """
        # 去重 - 基于标题和URL/Source
        unique_items = {}
        for item in data_items:
            # 安全地构建用于去重的键
            key = item.title
            # 只有当item有url属性且不为None时才添加到key中
            if hasattr(item, 'url') and item.url:
                key = f"{item.title}_{item.url}"
            elif hasattr(item, 'source') and item.source:
                # 如果有source属性，可以用作备选去重条件
                key = f"{item.title}_{item.source}"
            unique_items[key] = item
        
        cleaned_items = list(unique_items.values())
        
        # 过滤无效数据
        valid_items = []
        for item in cleaned_items:
            # 确保有标题
            if not item.title or len(item.title.strip()) < 5:
                continue
            
            # 确保有内容或URL（安全地检查URL属性）
            has_content = bool(getattr(item, 'content', ''))
            has_url = hasattr(item, 'url') and bool(item.url)
            if not has_content and not has_url:
                continue
            
            valid_items.append(item)
        
        # 处理缺失值
        for item in valid_items:
            # 为缺失的source设置默认值
            if not getattr(item, 'source', ''):
                item.source = "未知来源"
            
            # 为缺失的content设置默认值
            if not hasattr(item, 'content') or not getattr(item, 'content', ''):
                setattr(item, 'content', f"{item.title} - 暂无详细内容")
        
        return valid_items
    
    def analyze_keywords(self, data_items, top_n=20):
        """
        关键词分析 - 优化版
        返回结构化的关键词分析结果，包括词频和格式化报告
        """
        if not data_items:
            return {"top_keywords": [], "keyword_report": "暂无数据"}
        
        # 合并所有文本内容
        all_text = ''
        for item in data_items:
            all_text += f"{item.title} "
            all_text += f"{getattr(item, 'content', '')} "
        
        # 清理文本
        all_text = re.sub(r'[\s\n\r\t]+', ' ', all_text)  # 替换空白字符
        all_text = re.sub(r'[\xa0]+', ' ', all_text)  # 替换非断行空格
        
        # 使用jieba分词
        words = jieba.lcut(all_text)
        
        # 过滤停用词和单字符
        filtered_words = [
            word for word in words 
            if word not in self.stop_words 
            and len(word) > 1 
            and re.match(r'^[\u4e00-\u9fa5]+$', word)  # 只保留中文
        ]
        
        # 统计词频
        word_counts = Counter(filtered_words)
        top_keywords_with_freq = word_counts.most_common(top_n)
        
        # 生成格式化的关键词报告
        keyword_report = ""
        if top_keywords_with_freq:
            keyword_report = "高频关键词（按出现频率排序）：\n"
            # 将关键词分为多个组，每组5个，便于阅读
            for i in range(0, len(top_keywords_with_freq), 5):
                group = top_keywords_with_freq[i:i+5]
                group_str = ", ".join([f"{word}({freq})" for word, freq in group])
                keyword_report += f"  - {group_str}\n"
        
        return {
            "top_keywords": [word for word, _ in top_keywords_with_freq],
            "keyword_counts": dict(word_counts),
            "keyword_report": keyword_report,
            "total_unique_words": len(word_counts),
            "top_keywords_with_freq": top_keywords_with_freq
        }
    
    def analyze_time_distribution(self, data_items, days=7):
        """
        时间分布分析
        返回最近days天的数据分布
        """
        time_distribution = defaultdict(int)
        today = datetime.now().date()
        
        for item in data_items:
            if item.created_at:
                # 转换为日期（去掉时间部分）
                item_date = item.created_at.date()
                # 只统计最近days天的数据
                if (today - item_date).days <= days:
                    date_str = item_date.strftime('%Y-%m-%d')
                    time_distribution[date_str] += 1
        
        # 确保所有日期都有记录，包括没有数据的日期
        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in time_distribution:
                time_distribution[date_str] = 0
        
        # 按日期排序
        sorted_distribution = sorted(time_distribution.items(), key=lambda x: x[0])
        
        return sorted_distribution
    
    def analyze_source_distribution(self, data_items):
        """
        来源分布分析
        返回各来源的数据数量和百分比
        """
        source_counts = Counter([item.source for item in data_items])
        total = len(data_items)
        
        # 计算百分比并排序
        source_distribution = []
        for source, count in source_counts.most_common():
            percentage = (count / total * 100) if total > 0 else 0
            source_distribution.append({
                'source': source,
                'count': count,
                'percentage': round(percentage, 1)
            })
        
        return source_distribution
    
    def analyze_text_length(self, data_items):
        """
        文本长度分析
        返回标题和内容长度的统计信息
        """
        title_lengths = []
        content_lengths = []
        
        for item in data_items:
            title_lengths.append(len(item.title))
            content = getattr(item, 'content', '')
            content_lengths.append(len(content) if content else 0)
        
        # 计算统计信息
        if title_lengths:
            title_stats = {
                'min': min(title_lengths),
                'max': max(title_lengths),
                'avg': round(np.mean(title_lengths), 1),
                'median': round(np.median(title_lengths), 1)
            }
        else:
            title_stats = None
        
        if content_lengths and sum(content_lengths) > 0:
            content_stats = {
                'min': min([cl for cl in content_lengths if cl > 0]),
                'max': max(content_lengths),
                'avg': round(np.mean(content_lengths), 1),
                'median': round(np.median(content_lengths), 1)
            }
        else:
            content_stats = None
        
        return {
            'title_stats': title_stats,
            'content_stats': content_stats
        }
    
    def extract_text_summaries(self, data_items, max_summaries=5):
        """
        提取文本摘要
        返回最相关的几个文本摘要
        """
        # 简单实现：返回内容最长的几个项
        items_with_content = [
            item for item in data_items 
            if getattr(item, 'content', '') 
            and len(getattr(item, 'content', '')) > 20
        ]
        
        # 按内容长度排序
        sorted_items = sorted(
            items_with_content,
            key=lambda x: len(getattr(x, 'content', '')),
            reverse=True
        )
        
        # 返回前max_summaries个
        return sorted_items[:max_summaries]
    
    def generate_insights(self, data_items, keyword_results, source_distribution=None):
        """
        生成优化的分析洞察
        提供结构化的洞察和建议，使报告更加直观易读
        """
        insights = []
        suggestions = []
        
        # 关键词洞察
        if keyword_results and "top_keywords_with_freq" in keyword_results:
            top_keywords = keyword_results["top_keywords_with_freq"]
            if top_keywords:
                insights.append({
                    'title': '核心主题识别',
                    'content': f'数据主要围绕 {"、".join([f"{word}({freq})".format(word=word, freq=freq) for word, freq in top_keywords[:3]])} 等核心主题展开。'
                })
        elif keyword_results:  # 兼容旧格式
            if isinstance(keyword_results, list):
                top_keywords = [kw[0] for kw in keyword_results[:5]]
                insights.append({
                    'title': '核心主题识别',
                    'content': f'数据主要围绕 {"、".join(top_keywords)} 等核心主题展开。'
                })
        
        # 来源洞察
        if source_distribution and len(source_distribution) > 1:
            primary_source = source_distribution[0]
            if primary_source['percentage'] > 50:
                insights.append({
                    'title': '信息来源集中',
                    'content': f'超过 {primary_source["percentage"]}% 的数据来自 {primary_source["source"]}，建议拓展其他信息源以获得更全面的视角。'
                })
        
        # 数据量洞察
        total_items = len(data_items)
        if total_items < 10:
            insights.append({
                'title': '数据量评估',
                'content': f'当前仅有{total_items}条有效数据记录，样本量较小可能影响分析结果的代表性。'
            })
        elif total_items < 50:
            insights.append({
                'title': '数据量评估',
                'content': f'当前有{total_items}条有效数据记录，样本量适中，可以提供基本的趋势分析。'
            })
        else:
            insights.append({
                'title': '数据量评估',
                'content': f'当前有{total_items}条有效数据记录，样本量充足，分析结果具有较高的可信度。'
            })
        
        # 文本复杂度分析
        if data_items:
            text_lengths = []
            for item in data_items:
                if hasattr(item, 'content') and getattr(item, 'content', ''):
                    text_lengths.append(len(getattr(item, 'content', '')))
                elif hasattr(item, 'title'):
                    text_lengths.append(len(item.title))
            
            if text_lengths:
                avg_length = sum(text_lengths) / len(text_lengths)
                insights.append({
                'title': '内容复杂度分析',
                'content': f'平均文本长度为{avg_length:.0f}字符，{"内容较为简洁" if avg_length < 200 else "内容相对详细" if avg_length < 500 else "内容非常详尽"}。'
            })
        
        # 提供结构化建议
        suggestions.append({
            'title': '建议行动',
            'content': '基于当前数据分析，建议：\n1. 定期更新数据，保持信息时效性\n2. 根据关键词分析结果，调整后续数据采集策略\n3. 深入分析高频主题的相关内容\n4. 结合其他维度的数据进行交叉分析'
        })
        
        # 关键词深度分析建议
        if keyword_results and "total_unique_words" in keyword_results:
            unique_words = keyword_results["total_unique_words"]
            top_keywords = keyword_results.get("top_keywords", [])[:3]
            suggestions.append({
                "title": "深化主题分析",
                "content": f"识别出{unique_words}个独特关键词，建议对核心关键词如{'、'.join(top_keywords)}进行专项深度分析。"
            })
        
        # 生成格式化报告
        formatted_insights = "\n".join([f"• {insight['title']}: {insight['content']}" for insight in insights])
        formatted_suggestions = "\n".join([f"• {suggestion['title']}: {suggestion['content']}" for suggestion in suggestions])
        
        return {
            "insights": insights,
            "suggestions": suggestions,
            "formatted_insights": formatted_insights,
            "formatted_suggestions": formatted_suggestions
        }
    
    def perform_full_analysis(self, data_items):
        """
        执行完整的数据分析 - 优化版
        返回结构化的综合分析报告，使结果更加直观易读
        """
        # 第一步：数据清洗
        cleaned_data = self.clean_data(data_items)
        
        # 第二步：各项分析
        keywords = self.analyze_keywords(cleaned_data)
        time_distribution = self.analyze_time_distribution(cleaned_data)
        source_distribution = self.analyze_source_distribution(cleaned_data)
        text_length_stats = self.analyze_text_length(cleaned_data)
        key_summaries = self.extract_text_summaries(cleaned_data)
        
        # 获取结构化的洞察
        insights_data = self.generate_insights(cleaned_data, keywords, source_distribution)
        
        # 生成格式化的综合报告
        formatted_report = {
            "title": "数据分析综合报告",
            "sections": [
                {
                    "title": "1. 数据质量概览",
                    "content": f"""
数据处理统计：
- 原始数据总量：{len(data_items)} 条
- 清洗后有效数据：{len(cleaned_data)} 条
- 数据清洗率：{(len(data_items) - len(cleaned_data)) / len(data_items) * 100:.1f}% 
                    """.strip()
                },
                {
                    "title": "2. 关键词分析",
                    "content": keywords.get("keyword_report", "\n".join([f"• {word}({freq})" for word, freq in (keywords[:10] if isinstance(keywords, list) else [])]))
                },
                {
                    "title": "3. 数据洞察",
                    "content": insights_data.get("formatted_insights", "\n".join([f"• {insight['title']}: {insight['content']}" for insight in (insights_data if isinstance(insights_data, list) else [])]))
                },
                {
                    "title": "4. 优化建议",
                    "content": insights_data.get("formatted_suggestions", "基于当前数据分析，建议：\n1. 定期更新数据，保持信息时效性\n2. 根据关键词分析结果，调整后续数据采集策略\n3. 深入分析高频主题的相关内容\n4. 结合其他维度的数据进行交叉分析")
                }
            ]
        }
        
        # 第三步：整合分析结果
        analysis_result = {
            'raw_count': len(data_items),
            'cleaned_count': len(cleaned_data),
            'keywords': keywords,
            'time_distribution': time_distribution,
            'source_distribution': source_distribution,
            'text_length_stats': text_length_stats,
            'key_summaries': key_summaries,
            'insights': insights_data,
            'formatted_report': formatted_report,
            'pdf_content': {
                "quality_summary": f"原始数据 {len(data_items)} 条，清洗后得到 {len(cleaned_data)} 条有效记录，清洗率 {(len(data_items) - len(cleaned_data)) / len(data_items) * 100:.1f}%",
                "keyword_highlights": ", ".join([f"{word}({freq})" for word, freq in (keywords[:5] if isinstance(keywords, list) else keywords.get("top_keywords_with_freq", [])[:5])]),
                "main_insights": insights_data.get("formatted_insights", ""),
                "key_suggestions": insights_data.get("formatted_suggestions", "")
            }
        }
        
        return analysis_result
