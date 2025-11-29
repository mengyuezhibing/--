import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, request, jsonify, redirect
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import json
import re
import os
import random
import requests

# 尝试导入OpenAI库（用于兼容其他AI API服务）
openai = None
try:
    import openai as openai_lib
    # 保存导入的库到变量
    openai = openai_lib
    # 设置API密钥
    openai.api_key = "sk-cpgqvljyhmugkkdtobnhurrxcenarmrvygfflwqzexgryjkm"
    # 可以选择设置API基础URL（如果使用其他AI服务）
    # openai.api_base = "https://api.example.com/v1"
    print("AI库导入成功并设置了API密钥")
except Exception as e:
    print(f"导入或配置AI库失败: {str(e)}")

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# 不使用新的客户端类，而是使用传统的API调用方式
client = None

# 同步网络搜索函数（将被异步调用）
def _sync_search_web(query):
    """使用网络搜索获取相关信息（同步版本）"""
    try:
        # 使用DuckDuckGo搜索API（无需API密钥）
        search_url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "no_redirect": 1
        }
        response = requests.get(search_url, params=params, timeout=5)  # 保持5秒超时
        response.raise_for_status()
        data = response.json()
        
        # 判断是否是专门查询网站或URL的请求
        is_url_query = any(keyword in query for keyword in ['官网', '网站', '网址', '链接', 'URL', '官网地址'])
        
        # 收集搜索结果
        search_results = []
        urls_collected = []  # 存储收集到的URL
        
        # 添加Abstract内容（如果有）
        if 'AbstractText' in data and data['AbstractText']:
            abstract_info = f"摘要: {data['AbstractText']}"
            # 只有在明确查询URL或摘要内容很重要时才添加URL
            if 'AbstractURL' in data and data['AbstractURL']:
                abstract_url = data['AbstractURL']
                urls_collected.append(abstract_url)
                # 如果是专门查询URL的请求，直接显示URL
                if is_url_query:
                    abstract_info += f"\n直达链接: {abstract_url}"
            search_results.append(abstract_info)
        
        # 添加RelatedTopics（如果有）
        if 'RelatedTopics' in data:
            for topic in data['RelatedTopics']:
                # 处理直接的topic项
                if 'Text' in topic and topic['Text']:
                    topic_info = topic['Text']
                    # 收集URL但不自动添加到每个结果中
                    if 'FirstURL' in topic and topic['FirstURL']:
                        first_url = topic['FirstURL']
                        # 确保URL是直达链接，不是中间页
                        if 'duckduckgo.com' not in first_url:
                            urls_collected.append(first_url)
                    search_results.append(topic_info)
                # 处理嵌套的Topics数组
                if 'Topics' in topic:
                    for sub_topic in topic['Topics']:
                        if 'Text' in sub_topic and sub_topic['Text']:
                            sub_topic_info = sub_topic['Text']
                            # 收集URL但不自动添加到每个结果中
                            if 'FirstURL' in sub_topic and sub_topic['FirstURL']:
                                first_url = sub_topic['FirstURL']
                                # 确保URL是直达链接，不是中间页
                                if 'duckduckgo.com' not in first_url:
                                    urls_collected.append(first_url)
                            search_results.append(sub_topic_info)
        
        # 去重URL列表
        unique_urls = list(dict.fromkeys(urls_collected))
        
        # 如果是专门查询URL的请求且收集到了URL，添加URL部分
        if is_url_query and unique_urls:
            # 添加标题提示
            search_results.append("\n找到的相关直达链接:")
            # 添加每个URL
            for url in unique_urls[:3]:  # 最多显示3个直达链接
                search_results.append(f"- {url}")
        
        # 如果没有获取到任何搜索结果
        if not search_results:
            if is_url_query:
                # 对于URL查询，说明未找到直达链接
                return "抱歉，未能找到相关的官方网站或直达链接。请尝试使用其他关键词重新查询。"
            else:
                # 对于普通查询，说明未找到相关信息
                return "抱歉，未能找到与你的问题相关的详细信息。请尝试使用其他关键词重新查询。"
        
        # 限制返回的结果数量
        return "\n\n".join(search_results[:5])  # 保持最多5条结果
    except Exception as e:
        print(f"网络搜索失败: {str(e)}")
        # 出错时提供友好的错误信息，不再直接提供搜索链接
        return "抱歉，在获取信息时遇到了一些技术问题。请稍后再试，或者尝试使用其他关键词重新查询。"

# 网络搜索函数（异步版本）
def search_web(query):
    """异步使用网络搜索获取相关信息"""
    try:
        # 使用eventlet.spawn异步执行网络请求
        greenlet = eventlet.spawn(_sync_search_web, query)
        # 等待执行完成并获取结果，设置超时时间
        return greenlet.wait(timeout=8)  # 增加超时时间到8秒，给网络请求足够的完成时间
    except eventlet.timeout.Timeout:
        print("网络搜索超时")
        # 超时也提供DuckDuckGo搜索链接作为备选
        duckduckgo_search_link = f"https://duckduckgo.com/?q={requests.utils.quote(query)}"
        return f"搜索超时，但你可以访问以下链接查看搜索结果：\n{duckduckgo_search_link}"
    except Exception as e:
        print(f"异步搜索处理失败: {str(e)}")
        # 出错时也提供DuckDuckGo搜索链接作为备选
        duckduckgo_search_link = f"https://duckduckgo.com/?q={requests.utils.quote(query)}"
        return f"处理搜索请求时出错，但你可以访问以下链接查看搜索结果：\n{duckduckgo_search_link}"

# 存储在线用户信息
users = {}
# 存储系统用户（常驻在线）
system_users = {'萝卜子'}
room = 'main_room'
# 存储用户与AI的对话状态，记录哪些用户已经@过萝卜子
user_ai_conversation = {}

import socket

# 从配置文件读取服务器列表并添加本机局域网IP
def get_servers():
    # 获取本机局域网IP地址
    def get_local_ip():
        try:
            # 创建一个UDP套接字连接到外部地址
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return '127.0.0.1'
    
    local_ip = get_local_ip()
    local_servers = [f'http://{local_ip}:9999', 'http://localhost:9999']
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            config_servers = config.get('servers', [])
            # 合并并去重
            all_servers = local_servers + [s for s in config_servers if s not in local_servers]
            return all_servers
    except:
        return local_servers

@app.route('/')
def login():
    servers = get_servers()
    return render_template('login.html', servers=servers)

@app.route('/chat')
def chat():
    username = request.args.get('username')
    if not username:
        return redirect('/')
    return render_template('chat.html', username=username)

@app.route('/check_username', methods=['POST'])
def check_username():
    username = request.json.get('username')
    if username in users.values():
        return jsonify({'valid': False})
    return jsonify({'valid': True})

@socketio.on('connect')
def handle_connect():
    print('Client connected')

def update_user_list():
    """更新房间中的用户列表"""
    all_users = list(users.values()) + list(system_users)
    emit('update_users', all_users, room=room)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in users:
        username = users[sid]
        del users[sid]
        # 如果用户在AI对话状态中，也删除该记录
        if username in user_ai_conversation:
            del user_ai_conversation[username]
        leave_room(room)
        emit('user_left', {'username': username}, room=room)
        update_user_list()

@socketio.on('join')
def handle_join(data):
    username = data['username']
    sid = request.sid
    users[sid] = username
    join_room(room)
    emit('user_joined', {'username': username}, room=room)
    update_user_list()

@socketio.on('message')
def handle_message(data):
    username = data['username']
    message = data['message']
    
    # 广播用户消息给房间内所有人
    emit('message', {
        'username': username,
        'message': message
    }, room=room)
    
    # 检查是否是@电影命令，如果是则不触发AI回复，因为前端会处理
    is_movie_command = '@电影' in message
    
    if is_movie_command:
        # 对于@电影命令，前端会处理，后端不需要额外操作
        return
    
    # 检查是否包含@萝卜子指令，或者用户已经在与AI对话中
    is_ai_conversation = '@萝卜子' in message or username in user_ai_conversation
    
    if is_ai_conversation:
        # 提取用户的问题（如果包含@萝卜子，则去掉标记）
        question = message.replace('@萝卜子', '').strip()
        
        # 如果是第一次@萝卜子，记录用户到对话状态中
        if '@萝卜子' in message:
            user_ai_conversation[username] = True
        
        try:
            # 生成更详细的AI回复
            ai_reply = generate_ai_response(question)
            
            # 以"萝卜子"的身份发送回复
            emit('message', {
                'username': '萝卜子',
                'message': ai_reply
            }, room=room)
        except Exception as e:
            print(f"处理AI回复时出错: {str(e)}")
            # 出错时也发送一个基本回复，确保用户收到响应
            emit('message', {
                'username': '萝卜子',
                'message': '抱歉，我刚才处理你的请求时遇到了一些问题。请再试一次。'
            }, room=room)

def generate_ai_response(question):
    """尝试使用AI API生成回复，如果失败则使用增强的模拟回复，同时集成网络搜索功能"""
    # 判断是否需要进行网络搜索的关键词
    search_keywords = [
        '什么', '哪个', '哪里', '如何', '怎样', '为什么', '何时', '是多少', 
        '最新', '现在', '今天', '最近', '2024', '2025',
        '是什么', '什么是', '有哪些', '包括哪些',
        '为什么', '原因', '介绍', '解释', '定义', '含义',
        '2023', '2024', '2025', '时间', '日期', '地点',
        '哪里', '哪里有', '怎么去', '路线', '地址',
        '价格', '多少钱', '费用', '成本', '花费',
        '历史', '由来', '起源', '发展', '演变',
        '区别', '比较', '对比', '不同', '差异',
        '功能', '特点', '特性', '优势', '劣势',
        '方法', '步骤', '教程', '攻略', '指南',
        '推荐', '建议', '意见', '评价', '看法',
        '问题', '解决', '修复', '处理', '应对',
        '新闻', '资讯', '动态', '消息', '报道'
        # URL相关关键词不再包含在这里，单独处理
    ]
    
    # 检查问题是否包含搜索关键词，需要实时信息的问题优先进行网络搜索
    should_search = any(keyword in question for keyword in search_keywords)
    
    # 获取网络搜索结果（如果需要）
    search_info = ""
    if should_search:
        print(f"正在搜索网络信息: {question}")
        search_info = search_web(question)
        print(f"搜索结果: {search_info}")
    
    # 首先尝试使用OpenAI API
    try:
        # 检查OpenAI库是否已成功导入
        if openai is not None:
            # 构建消息，包含网络搜索结果（如果有）
            messages = [
                {
                    "role": "system",
                    "content": "你是萝卜子，一个友好可爱的AI助手。请用详细、友好的语言回答用户问题，提供丰富的信息和有用的建议。如果有网络搜索结果，请基于这些信息来回答。回答内容要充实，不要太简短，确保用户能够获得有价值的回应。如果问题中包含URL或需要提供链接，请直接在回答中包含相关网址。"
                }
            ]
            
            # 如果有搜索结果，添加到用户消息中
            if search_info and search_info != "无法获取网络信息":
                user_content = f"问题: {question}\n\n网络搜索结果:\n{search_info}\n\n请基于以上信息回答问题。"
            else:
                user_content = question
            
            messages.append({
                "role": "user",
                "content": user_content
            })
            
            # 使用兼容的AI API调用方式，并添加超时控制
            with eventlet.timeout.Timeout(8):  # 设置8秒超时
                # 尝试使用ChatCompletion接口（兼容多种AI服务）
                response = openai.ChatCompletion.create(
                    # 使用通用模型名称，大多数兼容服务都支持
                    model="gpt-3.5-turbo",  # 或根据实际服务要求修改为其他模型
                    messages=messages,
                    temperature=0.7,
                    max_tokens=500  # 增加最大token数，允许更长的回复
                )
            
            # 提取生成的回复内容
            ai_response = response.choices[0].message.content.strip()
            
            # 如果进行了网络搜索，可以在回复中提及
            if should_search and search_info != "无法获取网络信息":
                return f"我刚刚查询了相关信息，为你整理如下：\n\n{ai_response}"
            return ai_response
    except Exception as e:
        print(f"AI API调用失败: {str(e)}")
    
    # 如果API调用失败，使用增强的模拟回复作为备用，同时利用网络搜索结果（如果有）
    
    # 如果有网络搜索结果，将其整合到模拟回复中
    if should_search and search_info and search_info != "无法获取网络信息":
        search_responses = [
            f"根据我查到的信息：\n{search_info}\n\n希望这些信息对你有帮助！如果你需要更详细的解释，随时告诉我。",
            f"我刚刚搜索了相关内容，发现：\n{search_info}\n\n这些是目前的最新信息，希望能解答你的问题。",
            f"通过查询，我找到了以下信息：\n{search_info}\n\n这应该能帮助你了解相关情况。还有其他问题吗？"
        ]
        return random.choice(search_responses)
    
    # 检查是否包含URL或需要网址的问题
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    contains_url = bool(url_pattern.search(question))
    
    # 尝试识别是否是询问网站或URL的请求
    url_keywords = ['官网', '网站', '网址', '链接', 'URL', '官网地址']
    is_url_query = any(keyword in question for keyword in url_keywords)
    website_name = None
    
    if contains_url:
        # 提取URL
        urls = url_pattern.findall(question)
        return f"我注意到你分享了链接。以下是你提到的网址：\n\n{chr(10).join(urls)}\n\n这些链接看起来很有趣！你想了解关于这些网站的什么信息呢？或者你想让我搜索这些网站的相关内容？"
    
    if is_url_query:
        # 关于网址的问题，增强网站名称识别能力
        # 模式1: 直接匹配 "XX官网" 或 "XX网站" 格式
        direct_pattern = re.compile(r'([一-龥\w]+)(官网|网站|网址|链接)', re.IGNORECASE)
        direct_match = direct_pattern.search(question)
        
        # 模式2: 匹配 "XX的官网" 或 "XX的网站" 格式
        with_de_pattern = re.compile(r'([一-龥\w]+)(?:的|是)(官网|网站|网址|链接)', re.IGNORECASE)
        de_match = with_de_pattern.search(question)
        
        # 模式3: 匹配 "查找XX"、"搜索XX" 等格式
        search_pattern = re.compile(r'(?:查找|搜索|查询|了解|获取)([一-龥\w]+)', re.IGNORECASE)
        search_match = search_pattern.search(question)
        
        # 确定网站名称
        if direct_match:
            website_name = direct_match.group(1)
        elif de_match:
            website_name = de_match.group(1)
        elif search_match:
            website_name = search_match.group(1)
        
        # 如果识别出网站名称且是URL查询，专门搜索其官网
        if website_name:
            print(f"正在搜索网站信息: {website_name}")
            # 增强搜索查询，使用更精确的关键词组合
            search_query = f"{website_name} 官方网站 官网 网址 链接 官网地址"
            search_info = search_web(search_query)
            # 不再额外添加链接提示，因为_sync_search_web函数会根据查询类型自动处理
            return f"我为您搜索到了关于{website_name}的官网信息：\n\n{search_info}"
        
        # 通用的网址回答
        return "关于网址的问题，我可以帮你查找各种网站的链接！\n1. 你可以直接告诉我网站名称，比如'百度官网'或'淘宝官网'\n2. 也可以询问特定类型的网站，比如'新闻网站推荐'或'学习编程的网站'\n3. 我会为你搜索最新的官方网址和相关信息\n\n请告诉我你想查找什么网站的链接？"
    
    # 增强的回复库
    responses = [
        "你好！很高兴和你聊天~ 我是萝卜子，一个喜欢帮助人的AI助手。你有什么想聊的话题或者需要帮助的事情吗？",
        "这个问题很有趣呢，让我仔细想想... 首先，我认为这涉及到几个方面的考虑，比如实用性、可行性和用户体验等。",
        "谢谢你的提问，我很乐意帮助你！让我为你提供一些详细的信息和建议，希望能够帮到你。",
        "今天天气真不错，你在做什么呢？是在工作、学习还是在休息放松？不管你在做什么，希望你一切顺利！",
        "我是萝卜子，一个AI助手。我可以回答你的问题，陪你聊天，或者帮你查找信息。你想要我为你做什么呢？",
        "这个想法很棒呢！我觉得这不仅有创意，而且很实用。也许我们可以进一步探讨一下具体的实现方案和可能遇到的挑战。",
        "我理解你的意思，让我来试试回答... 基于我的理解，你可能需要考虑以下几点：首先... 其次... 最后...",
        "嗯，这是个好问题！让我从多个角度来分析一下这个问题，希望能够给你提供全面的见解。",
        "很高兴认识你，让我们成为好朋友吧！我们可以聊任何话题，无论是日常生活、学习工作，还是兴趣爱好，我都很乐意倾听和回应。",
        "你今天心情怎么样？不管怎样，希望我能给你带来一些快乐和帮助。如果有什么烦恼，也可以和我说说哦！",
        "针对你的问题，我需要了解更多细节才能给出准确的回答。你能再详细描述一下你的需求或者疑问吗？",
        "这个问题涉及到多个方面，让我为你一一分析...",
        "从技术角度来看，这个问题可以通过以下几种方法解决...",
        "我认为这个问题的关键在于理解其中的原理和机制...",
        "根据我的理解，这个问题可能是由于以下原因造成的...",
        "解决这个问题的步骤可以分为以下几个部分...",
        "对于这种情况，我建议采取以下措施...",
        "要回答这个问题，我们需要考虑几个重要因素...",
        "从不同的角度来看，这个问题可以有不同的解决方案...",
        "我需要更具体的信息才能给你一个有针对性的回答。你能再提供一些背景或细节吗？"
    ]
    
    # 增强的关键词匹配系统，支持更多类型的问题
    if question:
        # 数学问题处理 - 识别并计算基本算术表达式
        # 定义数学运算符和数字的正则表达式模式
        math_pattern = re.compile(r'\b(\d+(\.\d+)?)\s*([+\-*/])\s*(\d+(\.\d+)?)\b')
        math_match = math_pattern.search(question)
        
        # 检查是否包含数学运算
        contains_math_terms = any(term in question for term in ['加', '减', '乘', '除', '等于', '等于多少', '='])
        
        if math_match or contains_math_terms:
            try:
                # 处理数字+运算符+数字的模式
                if math_match:
                    num1 = float(math_match.group(1))
                    operator = math_match.group(3)
                    num2 = float(math_match.group(4))
                    
                    # 执行计算
                    if operator == '+':
                        result = num1 + num2
                    elif operator == '-':
                        result = num1 - num2
                    elif operator == '*':
                        result = num1 * num2
                    elif operator == '/':
                        if num2 == 0:
                            return "除数不能为零哦！请检查你的数学问题。"
                        result = num1 / num2
                    else:
                        return "对不起，我只支持基本的加减乘除运算。让我来帮你解答其他问题吧！"
                    
                    # 格式化结果
                    if result.is_integer():
                        result = int(result)
                    
                    return f"计算结果是：{num1} {operator} {num2} = {result}"
                
                # 处理中文表述的数学问题
                if contains_math_terms:
                    # 简单的中文数学问题解析
                    if '1+1' in question or '一加一' in question or '1加1' in question:
                        return "1+1=2，这是最基本的数学运算哦！"
                    elif '2+2' in question or '二加二' in question or '2加2' in question:
                        return "2+2=4，这个问题对我来说很简单！"
                    elif '5-3' in question or '五减三' in question or '5减3' in question:
                        return "5-3=2，减法运算也难不倒我！"
                    elif '3*4' in question or '三乘四' in question or '3乘4' in question:
                        return "3*4=12，乘法运算也很简单！"
                    elif '10/2' in question or '十除以二' in question or '10除以2' in question:
                        return "10/2=5，除法运算我也会！"
                    else:
                        return "我可以帮你计算简单的数学问题！请尝试使用数字和运算符（+、-、*、/）来提问，或者用中文告诉我你想计算什么。"
                
            except Exception as e:
                print(f"数学计算出错: {str(e)}")
                return "抱歉，我在计算过程中遇到了问题。请尝试使用更简单的数学表达式，比如'2+3'或'10-5'。"
        
        # 问候语
        if any(word in question for word in ['你好', '嗨', '哈喽']):
            return "你好呀！我是萝卜子，很高兴见到你！第一次见到你，我感到非常开心。你今天过得怎么样？有什么有趣的事情发生吗？我很期待和你成为好朋友！"
        # 身份相关
        elif any(word in question for word in ['名字', '谁']):
            return "我是萝卜子，一个可爱又聪明的AI助手！我的名字是不是很有趣？我可以帮助你回答各种问题，陪你聊天解闷，还能给你提供有用的信息。只要你有需要，随时告诉我！"
        # 帮助相关
        elif any(word in question for word in ['帮助', '怎么', '如何']):
            # 更具体的帮助问题
            if any(word in question for word in ['编程', '代码', '开发']):
                return "关于编程的问题，我很乐意帮助你！请告诉我你遇到了什么具体的编程问题，比如哪种编程语言、具体的错误信息或者你想实现什么功能。我会尽力提供详细的解决方案。"
            elif any(word in question for word in ['学习', '考试', '作业']):
                return "学习方面的问题我也可以帮忙！请告诉我你在学习什么科目，遇到了什么具体的困难，我会尝试用简单易懂的方式为你解释。"
            else:
                return "当然可以帮助你！你可以问我任何问题，比如学习上的难题、生活中的困惑，或者是想了解的知识。我会尽力为你提供详细的解答和实用的建议。让我知道你具体需要什么帮助吧！"
        # 搜索相关
        elif any(word in question for word in ['搜索', '查找', '查询']):
            # 专门的搜索指令关键词
            if should_search:
                # 提取搜索内容（去掉搜索指令词）
                search_content = question
                for keyword in ['搜索', '查找', '查询']:
                    search_content = search_content.replace(keyword, '').strip()
                if search_content:
                    search_info = search_web(search_content)
                    if search_info and search_info != "无法获取网络信息":
                        return f"我为你搜索了'{search_content}'，结果如下：\n\n{search_info}\n\n希望这些信息对你有帮助！"
        # 聊天相关
        elif any(word in question for word in ['聊天', '说话']):
            return "我很喜欢聊天呢！我们可以聊任何话题，比如你的兴趣爱好、最近的生活、未来的计划等等。只要你想聊，我就会一直在这里倾听和回应。让我们开始一段愉快的对话吧！"
        # 感谢相关
        elif any(word in question for word in ['谢谢', '感谢']):
            return "不用客气！能够帮助到你我感到非常开心。如果你还有其他问题或者需要进一步的帮助，随时都可以告诉我。我会一直在这里为你服务的！"
        # 告别相关
        elif any(word in question for word in ['再见', '拜拜']):
            return "再见啦！希望我们下次还能再聊。祝你有愉快的一天！如果你想继续和我聊天，随时都可以回来找我哦！"
        # 具体问题相关
        elif any(word in question for word in ['是什么', '什么是', '定义', '含义']):
            return "这是一个关于定义的问题。要准确回答，我需要了解你具体想知道什么的定义。例如，如果你问'人工智能是什么'，我可以解释人工智能是模拟人类智能的计算机系统。请告诉我你想了解什么的定义。"
        elif any(word in question for word in ['为什么', '原因', '因为']):
            return "关于原因的问题，我可以从多个角度为你分析。请告诉我你想了解具体什么事情的原因，我会尝试给出合理的解释。"
        elif any(word in question for word in ['怎么做', '如何做', '步骤', '方法']):
            return "关于操作步骤的问题，我需要知道你想了解什么具体操作的步骤。例如，如果你想知道'如何学习编程'，我可以给出从入门到进阶的学习路径。请告诉我你想了解什么具体操作的方法。"
        # 技术相关问题
        elif any(word in question for word in ['电脑', '手机', '软件', '硬件', '技术']):
            return "关于技术相关的问题，我很感兴趣！请告诉我你具体想了解哪方面的技术知识，或者遇到了什么技术问题，我会尽力为你解答。"
        # 生活相关问题
        elif any(word in question for word in ['生活', '日常', '健康', '饮食']):
            return "生活方面的问题也很重要！请告诉我你在生活中遇到了什么具体的问题或想了解什么生活知识，我会给你一些建议。"
        # 时间相关
        elif any(word in question for word in ['时间', '几点', '今天', '明天', '现在']):
            return "关于时间的问题，我可以告诉你一些基本信息。不过由于我的时钟是固定的，建议你查看当地时间以获得最准确的信息。你想了解什么具体的时间信息呢？"
    
    # 根据问题长度选择更合适的回复
    if len(question) > 20:  # 较长的问题可能更具体
        detailed_responses = [
            "这个问题比较详细，让我为你分析一下...",
            "从你的问题中，我理解你想了解的是...",
            "根据你提供的信息，我认为...",
            "你的问题涉及多个方面，让我逐一解答...",
            "针对你提出的问题，我有以下几点想法..."
        ]
        return random.choice(detailed_responses)
    
    # 返回随机回复
    return random.choice(responses)

# 以下是原始的OpenAI API调用函数（保留但注释掉，供将来配置API密钥后使用）
# def generate_ai_response_with_openai(question):
#     # 使用OpenAI API生成AI回复
#     # 检查client是否已初始化
#     # if client is None:
#     #     return "AI服务暂未初始化，请检查配置。"
#     
#     # 获取API密钥
#     # api_key = os.environ.get("OPENAI_API_KEY")
#     
#     # 如果没有设置有效的API密钥
#     # if not api_key or api_key == "你的OpenAI API密钥":
#     #     return "AI服务需要配置有效的API密钥。"
#     
#     # try:
#     #     # 使用OpenAI的chat completions API
#     #     response = client.chat.completions.create(
#     #         model="gpt-3.5-turbo",
#     #         messages=[
#     #             {
#     #                 "role": "system",
#     #                 "content": "你是萝卜子，一个友好可爱的AI助手。请用简洁、友好的语言回答用户问题。"
#     #             },
#     #             {
#     #                 "role": "user",
#     #                 "content": question
#     #             }
#     #         ],
#     #         temperature=0.7,
#     #         max_tokens=150
#     #     )
#     #     
#     #     # 提取生成的回复内容
#     #     return response.choices[0].message.content.strip()
#     # except Exception as e:
#     #     print(f"OpenAI API调用失败: {str(e)}")
#     #     return "抱歉，我现在无法连接到AI服务。请稍后再试或检查API密钥配置。"

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=9999, debug=True, use_reloader=False)