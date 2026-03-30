# Enterprise LangGraph Agent

本项目是一个基于 LangGraph 重构的企业级 Agent 基础架构。项目彻底切断了原型和演示性质的遗留代码，实现了适用于生产环境的强隔离、高性能及长程防崩溃记忆。

## 🌟 核心工程特性 (Phase 1 & 2)

### 1. 安全与隔离机制
- **数据强物理隔离**：所有的会话存储（Checkpointer）均采用 `user_id:session_id` 联合构建的 `thread_id`，实现了多用户的物理数据防越权管控。

### 2. 高级会话记忆引擎 (Rolling Memory)
- **Token 限制与滑动窗口**：通过 `trim_messages` 和底层的字符换算器，严格阻断因超长会话引发的 LLM Provider 400 报错。
- **滚动摘要机制**：当历史会话达到特定阈值（暂定为10条），触发后台异步的 `summarize_conversation` 图谱节点，只保留最新工作视窗，将无用对话精简为全局历史 Summary，实现无缝的长短记忆更迭。

### 3. API 架构与流式输出
- **SSE 流式通讯**：集成了 LangChain 最新底层的 `astream_events` (v2)，暴露完整的 `Server-Sent Events` (SSE) 接口（`/chat/stream`），精准下发 Token 内容追踪、工具调度细节（Tool Calls）等。
- **Checkpointer 复用**：实现了基于 FastAPI Lifespan 和 Pydantic Settings 的依赖注入，异步 Postgres Saver 将通过连接池在整个应用周期中安全复用，杜绝逐请求实例化的性能瓶颈。
- **全局容灾中间件**：`exception_handlers.py` 实现统一的 JSON 异常封装阻断，防止敏感 Traceback 栈信息泄露溢出。

## 📂 核心代码拓扑

```text
src/
├── agent/
│   ├── graph.py       # LangGraph 核心图谱路由与长短记忆滚动处理引擎
│   ├── tools.py       # 工具库集成
│   ├── prompts.py     # 带有动静态绑定的系统提示词库
│   ├── state.py       # 图谱状态与 Context 定义
│   └── memory.py      # （待作废/重构：部分旧记忆引擎）
├── api/
│   ├── deps.py        # 鉴权和全局状态依赖注入 (DI)
│   └── v1/
│       ├── chat.py    # 核心文本/SSE问答接口
│       ├── history.py # 历史记录获取与长记忆摘要抽取接口
│       └── sessions.py# 用户对话列表获取接口
└── core/
    ├── config.py             # 基于 Pydantic 的工程环境变量配置
    ├── exception_handlers.py # 统一容错中间件
    └── logger.py             # 结构化日志装配
```

## 🚀 后续企业演进路线 (Phase 3 预留)
- 对接标准的 JWT / OAuth2 认证机制。
- 实现 `history.py` 中真正的物理层记忆终结接口 (`clear_history`)。
- 引入数据库迁移工具 (Alembic) 及向量检索 (Vector Retrieval) 扩展记忆池。
- 集成动态工具注册表 (Tool Registry) 实现热发插拔。

## 💻 启动与环境

```bash
cp .env.example .env
# 配置好您的 OPENAI_API_KEY 和 POSTGRES_URL

# 建议使用 Uvicorn 或其它 ASGI 容器启动 (具体视 main.py 挂载而定)
```
