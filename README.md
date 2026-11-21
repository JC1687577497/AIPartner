# AIPartner · AI 智能伴侣

一个基于 Streamlit + DeepSeek API 的对话应用：可自定义伴侣的名称与性格，支持流式输出、会话持久化与历史会话管理。

这是学习路线的第一个工程化项目，后续将升级为 RAG 知识库问答应用（FastAPI + PostgreSQL/pgvector）。

## 功能

- 流式对话：逐字输出，带打字光标效果
- 伴侣定制：侧边栏随时修改名称与性格（注入 system prompt）
- 会话管理：新建 / 加载 / 删除历史对话，JSON 落盘，重启不丢
- 多轮上下文：完整历史随每次请求发送

## 架构

```
浏览器 (Streamlit UI)
   │  st.session_state 保存当前会话
   ▼
app.py ──► OpenAI SDK ──► DeepSeek API（流式）
   │
   ▼
sessions/*.json（会话持久化，不进 Git）
```

## 技术栈

Python 3.14 · Streamlit · openai SDK · DeepSeek API

## 快速开始

1. 创建并激活虚拟环境：

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. 配置 API key（用户级环境变量，配置一次即可，重开终端生效）：

   ```powershell
   setx DEEPSEEK_API_KEY "你的key"
   ```

   可选：`setx DEEPSEEK_MODEL "模型名"` 覆盖默认模型。

3. 启动：

   ```powershell
   streamlit run app.py
   ```

## 目录结构

```
AIPartner/
├── app.py              # 主程序
├── assets/logo.png     # 页面 logo
├── sessions/           # 会话存档（gitignore，仅本地）
├── docs/               # 学习笔记
├── requirements.txt
└── README.md
```

## 已知限制（下一步改造方向）

- 会话存 JSON 文件而非数据库，无法多用户 / 并发
- 无鉴权，仅适合本机使用
- 全量历史随请求发送，长对话 token 成本高
