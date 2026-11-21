# AI 智能伴侣（AIPartner）
# 由学习项目 Partner05.py 整理而来，功能保持一致：
# 1. 与 DeepSeek 大模型流式对话，可自定义伴侣名称与性格
# 2. 会话持久化：保存 / 加载 / 删除历史对话（sessions/*.json）
#
# 相对 Partner05 的工程化改动：
# - 修复 bug：保存用脚本所在目录，读取却用相对路径 'sessions'，
#   启动目录不同时历史会话会"消失"。现在统一用 SESSIONS_DIR。
# - logo 移入本仓库 assets/，不再依赖仓库外的文件。
# - 模型名可通过环境变量 DEEPSEEK_MODEL 配置。
# - 清理无用导入（ntpath.exists / shutil.which 等）。

import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st
from openai import OpenAI

# 所有磁盘路径都基于脚本所在目录，与启动目录无关。
BASE_DIR = Path(__file__).resolve().parent
SESSIONS_DIR = BASE_DIR / "sessions"

#设置页面配置
st.set_page_config(
    page_title="AI智能伴侣", #页面的标题
    page_icon="🧊",   #页面的图标（指的是游览器上方那个地址栏那里显示的图标)
    layout="wide",#布局方式：wide指的是streamlit的全部空间都占用，center是只用中间部分
    initial_sidebar_state="expanded",#设置侧边栏的状态
)

# session_state:这个东西是用来放一些每轮都用得到的变量的，因为对话历史记录每轮都要
# 所以我们要把其放进session_state: 用一个变量 messages 表示对话历史记录，包括用户提示词
# AI回答，AI分析之类的。

#Initialization
if 'messages' not in st.session_state:
    st.session_state.messages = []

#AI定制的姓名得保存在 session_state中，确保每一轮对话AI都知道自己的名字，不能 rerun之后就变成初始值了
if 'nick_name' not in st.session_state:
    st.session_state.nick_name = '求真' #最开始时设置一个默认名称
#同理，AI定制的性格也得保存好
if 'nature' not in st.session_state:
    st.session_state.nature = "一个性格温柔可爱的大姐姐,同时在知识上绝对不含糊,追求真理,力求准确的回答你的问题."

# 设置对话标识：也就是当前对话的名字（这里先以日期为名字，后面再更改成以概括当前对话为名字）
# 初始化时必须写回 st.session_state，这样 rerun 后它仍然存在。
if 'current_session' not in st.session_state:
    st.session_state.current_session = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def save_session():
    session_data = {
        'nick_name': st.session_state.nick_name,
        'nature': st.session_state.nature,
        'current_session': st.session_state.current_session,
        'messages': st.session_state.messages,
    }
    #exist_ok=True:如果文件夹存在，不报错，继续运行，如果不存在，创建
    SESSIONS_DIR.mkdir(exist_ok=True)
    # Windows 文件名不能包含冒号，所以日期时间使用下划线和短横线。
    session_file = SESSIONS_DIR / f"{st.session_state.current_session}.json"
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)


#会话管理：
#思路：1.根据sessions文件夹里面有几个json文件，从而创建几个对话历史的按钮。
#      2.所以显然我们先要拿到所有的json文件，统一管理，然后创建按钮
def get_sessions():
    sessions_list = []
    #健壮性判断：如果有sessions这个文件夹再说
    if SESSIONS_DIR.exists():
        for file in SESSIONS_DIR.iterdir():
            #如果当前文件名是以.json结尾，代表是我们要的对话文件
            if file.suffix == '.json':
                sessions_list.append(file.stem)
    sessions_list.sort(reverse=True)  #新的对话标识在上面，日期越大越在上面。
    return sessions_list


#点击一个对话记录时，需要加载对话记录，重新渲染一遍
def load_session(session_name):
    session_file = SESSIONS_DIR / f"{session_name}.json"
    if session_file.exists():
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            st.session_state.nature = session_data['nature']
            st.session_state.nick_name = session_data['nick_name']
            st.session_state.current_session = session_data['current_session']
            st.session_state.messages = session_data['messages']
            st.rerun()
        except Exception:
            st.error("加载对话记录失败")


#删除会话
def delete_session(session_name):
    session_file = SESSIONS_DIR / f"{session_name}.json"
    if session_file.exists():
        session_file.unlink()
        #如果删除的是当前会话，重置为空对话
        if st.session_state.current_session == session_name:
            st.session_state.messages = []
            st.session_state.current_session = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


#设置侧边栏
with st.sidebar:
    st.subheader("AI控制面板")
    if st.button("新建对话", width='stretch'):
        #程序健壮性判断：只有当有对话记录时才保存，空对话不保存。
        if st.session_state.messages:
            save_session()
            st.session_state.current_session = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            st.session_state.messages = []
    st.text("对话管理")
    session_list = get_sessions()
    #columns():方法负责在同一行中划分多列 [4,1]:表示的是 一行 四一 分
    for session in session_list:
        col1, col2 = st.columns([4, 1])
        #key关键字：指定button的内置编号，避免不同会话的按钮编号重复报错
        with col1:
            if st.button(session, width='stretch', key=f"load{session}", icon='📄',
                         type='primary' if st.session_state.current_session == session else 'secondary'):
                load_session(session)
        with col2:
            if st.button('', width='stretch', key=f"delete{session}", icon='❌'):
                delete_session(session)
                st.rerun()
    st.divider()
    st.subheader("伴侣信息")
    nick_name = st.text_input("伴侣名称", placeholder="请输入伴侣的名称", value=st.session_state.nick_name)
    st.session_state.nick_name = nick_name
    nature = st.text_area("伴侣性格", placeholder="请输入伴侣的性格", value=st.session_state.nature)
    st.session_state.nature = nature


#设置页面标题
st.title("AI智能伴侣")

# API key 只从环境变量读取，绝不写进代码（工程铁律）。
api_key = os.environ.get('DEEPSEEK_API_KEY')
if not api_key:
    st.error("未检测到环境变量 DEEPSEEK_API_KEY，请先配置后再启动。配置方法见 README.md。")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
# 模型名可用环境变量 DEEPSEEK_MODEL 覆盖，默认沿用原项目的配置。
model_name = os.environ.get('DEEPSEEK_MODEL', 'deepseek-flash')

system_prompt = "性格:%s,名称:%s,以伴侣的方式回答问题。"

#设置Logo（已随仓库携带，不再依赖外部目录）
st.logo(BASE_DIR / "assets" / "logo.png")

#设置对话框
prompt = st.chat_input("say something")

#先渲染历史会话记录，再处理本轮输入
for message in st.session_state.messages:
    st.chat_message(message['role']).write(message['content'])

if prompt:
    st.chat_message("user").write(f":{prompt}")
    st.session_state.messages.append({'role': 'user', 'content': prompt})

    #调用大语言模型 DeepSeek（流式）
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt % (nature, nick_name)},
            *st.session_state.messages  #解包历史消息，格式与 API 要求一致
        ],
        stream=True,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}}
    )

    # 【知识注解 1：with】
    # with 创建了一个作用范围，下面缩进的内容都会放进
    # st.chat_message("assistant") 创建出来的助手消息气泡中。
    # 详细说明见：docs/Partner03_知识注解.md 的第 1 节。
    with st.chat_message("assistant"):
        # 【知识注解 3：st.empty() 和 .markdown()】
        # st.empty() 在页面中预留一个空位置并返回容器对象，
        # 对同一容器反复调用 .markdown()，新内容会覆盖旧内容。
        # 详细说明见：docs/Partner03_知识注解.md 的第 3 节。
        content_placeholder = st.empty()
        answer_content = ""

        # response 是流式响应，每次循环拿到一个 chunk（新增的一小段）。
        for chunk in response:
            delta = chunk.choices[0].delta
            # 【知识注解 2：getattr()】
            # getattr(对象, "属性名", 默认值)：属性不存在时返回默认值，
            # 避免不同 chunk 字段不同导致的 AttributeError。
            # 详细说明见：docs/Partner03_知识注解.md 的第 2 节。
            answer_piece = getattr(delta, "content", None)
            if answer_piece:
                answer_content += answer_piece
                # “▌”是光标效果，表示模型还在继续输出。
                content_placeholder.markdown(answer_content + "▌")

        # 流式输出结束后再覆盖一次，去掉光标。
        content_placeholder.markdown(answer_content)

    st.session_state.messages.append({'role': 'assistant', 'content': answer_content})
    #AI响应后，就保存结果
    save_session()
