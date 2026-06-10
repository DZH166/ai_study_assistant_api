# AI Study Assistant API

本项目从 `module15_chat_api` 演进而来，当前定位是 `ai_study_assistant_api` 的第一版后端骨架。

它的目标不是只做一个普通聊天接口，而是逐步升级成 AI 学习陪跑助手，支持多场景 Prompt、结构化输出、多轮上下文、流式响应、工具调用和学习记录管理。

本项目从 Module15 的 `/chat` 接口升级而来。

Module15 重点：把 Prompt、messages、模型调用和 FastAPI 接口串成一个最小可运行的聊天接口。

Module16 重点：把模型供应商、API Key、base_url、model、timeout、是否使用 mock 等配置从代码里抽出来，统一交给 `.env` 和配置层管理。

## 文件结构

```text
app/
  main.py                 主应用入口，创建 FastAPI app 并挂载路由
  core/config.py          配置中心，负责读取 .env 和环境变量
  data/conversation_store.py  会话存储层，负责保存和读取多轮对话历史
  routers/chat.py         HTTP 接口层，负责接请求、调 service、返回响应
  schemas/chat.py         请求体和响应体结构，Pydantic 在这里做字段校验
  services/chat_service.py 聊天业务流程，负责组装 messages 并调用模型客户端
  services/memory_service.py 会话记忆压缩服务，负责生成和包装 summary memory
  llm_client/client_factory.py 统一模型调用入口，根据配置决定使用 mock 还是真实模型
  llm_client/mock_client.py 模拟大模型调用，后续可替换成真实模型 API
  llm_client/openai_compatible_client.py 真实 OpenAI-compatible HTTP 调用客户端
  llm_client/llm_error_handler.py 模型调用错误映射，把供应商错误转换成安全响应
  utils/response.py       统一响应格式
```

## 配置文件

项目根目录有两个配置文件：

```text
.env.example  配置模板，可以分享给别人
.env          本地真实配置，不应该提交到 GitHub
```

当前 `.env` 示例：

```text
APP_ENV=dev
USE_MOCK_LLM=true

LLM_PROVIDER=mock
LLM_API_KEY=
LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL_NAME=mock-chat-model-from-env
LLM_TIMEOUT=30
```

字段解释：

1. `APP_ENV`：当前运行环境，例如 dev、test、prod。
2. `USE_MOCK_LLM`：是否使用 mock 模型。学习阶段先用 true。
3. `LLM_PROVIDER`：模型供应商名称，例如 mock、deepseek、closeai、openai-compatible。
4. `LLM_API_KEY`：模型调用密钥，真实项目不能写死在代码里。
5. `LLM_BASE_URL`：模型服务地址。
6. `LLM_MODEL_NAME`：具体模型名称。
7. `LLM_TIMEOUT`：模型请求最多等待多少秒。

注意：真实 API Key 只能放在你本机 `.env` 或服务器环境变量里，不要写进 Python 文件，不要发到聊天窗口，不要提交到 GitHub。

## 切换真实模型

如果要调用 DeepSeek、CloseAI 或其他 OpenAI-compatible 平台，可以在 `.env` 中改成类似：

```text
USE_MOCK_LLM=false
LLM_PROVIDER=deepseek
LLM_API_KEY=你的真实密钥
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL_NAME=deepseek-chat
LLM_TIMEOUT=30
```

当前真实模型调用逻辑在：

```text
app/llm_client/openai_compatible_client.py
```

它负责构造 `headers`、`json` 请求体，发送 HTTP 请求，并从响应中提取 `answer` 和 `usage`。

## 启动方式

在项目根目录执行：

```powershell
python -m uvicorn app.main:app --reload
```

然后访问：

```text
http://127.0.0.1:8000/docs
```

健康检查：

```text
GET /health
```

返回里会展示安全配置摘要，例如 `use_mock_llm`、`llm_provider`、`llm_model_name`、`has_api_key`。不会返回真实 API Key。

## 测试请求

`POST /chat`

```json
{
  "message": "什么是 FastAPI router？",
  "mode": "study",
  "temperature": 0.3,
  "prompt_scene": "learning_assistant"
}
```

首次请求不需要传 `conversation_id`，后端会自动创建会话编号并返回。

多轮请求示例：

```json
{
  "conversation_id": "conv_76f8a110",
  "message": "那 schema 又是什么？",
  "mode": "study",
  "temperature": 0.3
}
```

Module23 之后，前端不再需要每次都传完整 `history`。前端只需要保存并回传 `conversation_id`，后端会根据这个编号读取最近几轮历史，再组装成大模型需要的 `messages`。

旧字段仍然兼容：

```json
{
  "question": "什么是 Prompt 工程化？",
  "prompt_scene": "interview_assistant",
  "temperature": 0.3
}
```

兼容旧字段的原因是：真实项目接口升级不能突然破坏已有前端、测试脚本或外部调用方。新字段 `message/mode` 让接口更业务化，旧字段 `question/prompt_scene` 保证历史调用还能继续运行。

## Prompt 场景

Module20 新增了 Prompt 模板工程化能力。Prompt 不再写死在 `service` 层，而是统一放在：

```text
app/prompts/chat_prompts.py
```

当前 `/chat` 支持 3 种 `prompt_scene`：

| prompt_scene | 场景 | 用途 |
|---|---|---|
| `learning_assistant` | 学习助手 | 解释概念、拆解知识点、辅助理解代码和工程意义 |
| `summary_assistant` | 总结助手 | 根据学习内容提炼重点、难点、易错点和面试点 |
| `interview_assistant` | 面试助手 | 把知识点整理成更接近面试表达的回答 |

请求示例：

```json
{
  "question": "什么是 Prompt 工程化？",
  "history": [],
  "temperature": 0.3,
  "prompt_scene": "interview_assistant"
}
```

工程意义：

1. `service` 层只负责业务流程，不维护大段 Prompt 文本。
2. Prompt 属于高频变化的业务资产，单独放在 `prompts` 层更方便维护和扩展。
3. 后续结构化输出、RAG Prompt、Agent Prompt 都可以复用这套拆分方式。

面试表达：

```text
我把 Prompt 从业务 service 中拆成独立 prompts 层，并通过 prompt_scene 支持学习助手、总结助手和面试助手等多场景切换。这样可以避免 Prompt 和业务流程耦合，后续扩展 RAG Prompt、结构化输出 Prompt 或 Agent Prompt 时，只需要扩展 Prompt 模板层。
```

## 学习笔记结构化提取

Module21 新增了结构化输出能力。接口不再让 AI 返回一段普通文本，而是把学习笔记提取成后端可继续处理的固定字段。

接口：

```text
POST /extract/study-note
```

请求示例：

```json
{
  "note": "今天学习了 Prompt 工程化。Prompt 不应该直接写死在 service 里，因为它是高频变化的业务资产。service 更适合负责业务流程，prompts 层负责管理不同场景的 system prompt。",
  "temperature": 0.2
}
```

响应中的 `data.extraction` 会包含：

| 字段 | 含义 |
|---|---|
| `core_concepts` | 核心知识点 |
| `weak_points` | 薄弱点 |
| `review_suggestions` | 复习建议 |
| `quiz_questions` | 知识点抽问题 |
| `interview_questions` | 面试题 |

工程链路：

```text
router 接收请求
-> schema 校验 note / temperature
-> service 组装结构化提取 Prompt
-> llm_client 调用 mock 或真实模型
-> output_parser 解析 JSON
-> Pydantic 校验输出结构
-> router 返回统一响应
```

工程意义：

1. 普通文本适合人看，但不适合后端继续处理。
2. 结构化输出可以继续用于前端展示、复习文档生成、知识卡片、数据库存储和后续统计。
3. Prompt 只能要求模型输出 JSON，后端还必须用解析器和 Pydantic 做结构校验。

面试表达：

```text
我在 AI 学习助手项目中实现了学习笔记结构化提取接口。用户输入一段学习笔记后，后端通过 Prompt 约束模型输出固定 JSON，再用 output_parser 解析成 Python dict，并用 Pydantic 校验字段结构，最终返回核心知识点、薄弱点、复习建议、抽问题和面试题。这样模型输出不再只是展示文本，而是可以继续被系统处理的数据。
```

## 模型输出修复

Module22 新增了结构化输出修复策略。结构化输出不能只依赖 Prompt，因为模型可能返回非法 JSON、缺字段、字段类型错误，或者在 JSON 前后添加多余解释。

当前 `/extract/study-note` 的处理链路升级为：

```text
第一次模型输出
-> JSON 解析和 Pydantic 校验
-> 如果失败，构造 repair prompt
-> 让模型只修复上一轮坏输出
-> 再解析和校验一次
-> 仍失败则返回统一错误
```

成功响应会记录修复状态：

```json
{
  "repaired": true,
  "repair_reason": "第一次输出缺少字段"
}
```

这两个字段用于排查模型输出稳定性。真实项目中可以统计修复比例，用来判断 Prompt 是否需要优化、schema 是否过严、模型是否不稳定。

面试表达：

```text
我没有只依赖 Prompt 保证模型输出格式，而是在结构化提取接口中增加了解析、Pydantic 校验和一次 repair 重试。第一次输出不符合 JSON 或字段结构时，后端会把原始输出、错误原因和目标 schema 交给模型做格式修复；修复成功后记录 repaired 和 repair_reason，修复失败则返回统一错误。这样可以提升 AI 输出稳定性，同时保留可观测性。
```

## 多轮对话上下文管理

Module23 新增了后端会话管理能力。以前的 `/chat` 接口如果要多轮对话，需要前端每次把完整 `history` 传给后端；这会让前端承担过多上下文管理责任，也容易导致历史格式混乱、请求体越来越大。

当前升级后的链路是：

```text
第一次请求不传 conversation_id
-> 后端创建 conv_xxxxxxxx
-> 调用模型并保存 user/assistant 两条消息
-> 返回 conversation_id 给前端

第二次请求带 conversation_id
-> 后端读取最近 N 轮历史
-> 组装 system + recent_history + 当前 user
-> 调用模型
-> 继续保存本轮 user/assistant
```

核心文件：

| 文件 | 职责 |
|---|---|
| `app/data/conversation_store.py` | 临时会话仓库，负责创建会话、读取会话、追加消息、截取最近历史 |
| `app/schemas/chat.py` | 定义 `MessageItem`、`Conversation`、`ChatRequest`、`ChatResponse` 等结构 |
| `app/services/chat_service.py` | 组织聊天主流程，决定创建新会话还是读取旧会话，并组装大模型 `messages` |

当前历史截取策略：

```text
MAX_HISTORY_ROUNDS = 3
```

也就是每次调用大模型时，最多带最近 3 轮上下文。一轮通常包含一条 `user` 消息和一条 `assistant` 消息，所以最多带 6 条历史消息，再加上当前 `system` 和当前 `user`。

这样做的原因：

1. 避免上下文无限增长，导致请求越来越慢、token 成本越来越高。
2. 避免很久以前的低价值历史干扰当前回答。
3. 为后续升级摘要记忆、长期记忆、RAG 记忆和 Agent 状态管理打基础。

典型响应字段：

| 字段 | 含义 |
|---|---|
| `conversation_id` | 当前会话编号，前端后续请求要继续带回来 |
| `messages_count` | 本次真正发给大模型的消息数量 |
| `history_rounds` | 当前会话已经保存的对话轮数 |
| `stored_messages_count` | 当前会话内存中保存的消息条数 |

面试表达：

```text
我把聊天接口从单次问答升级成了后端管理上下文的多轮对话接口。第一次请求时后端创建 conversation_id，并在模型回答成功后保存 user 和 assistant 消息；后续请求只需要带 conversation_id，后端会读取最近几轮历史，组装成 system + recent_history + current_user 后再调用模型。同时我限制了历史窗口大小，避免上下文无限增长，为后续摘要记忆、长期记忆和 Agent 状态管理打基础。
```

## 会话记忆压缩

Module24 新增了 `summary memory`。Module23 解决的是“后端能保存并读取多轮历史”，Module24 解决的是“历史变长后，不能只靠最近几轮，也不能把全部历史都塞给模型”。

当前策略：

```text
较早历史 -> 压缩成 summary_memory
最近 3 轮 -> 保留原文
当前问题 -> 放在最后
```

最终发给大模型的 messages 顺序：

```text
system
summary_memory
recent_history
current_user
```

为什么要这样做：

1. 完整历史会让 token 成本和响应时间持续增长。
2. 只保留最近几轮可能丢失长期学习目标、薄弱点和任务状态。
3. 摘要记忆能保留长期主线，最近历史能保留当前语境。
4. 这是后续 RAG 记忆、Agent 状态管理和长期学习记录的基础。

核心文件：

| 文件 | 职责 |
|---|---|
| `app/services/memory_service.py` | 判断哪些旧消息需要压缩，调用模型生成 summary memory，并包装成可放入 messages 的 system 消息 |
| `app/data/conversation_store.py` | 保存 `summary_memory` 和 `summarized_messages_count`，避免重复压缩同一批消息 |
| `app/services/chat_service.py` | 在聊天主流程中刷新摘要记忆，并按 `system + summary + recent + user` 组装上下文 |

响应中新增记忆状态字段：

| 字段 | 含义 |
|---|---|
| `memory_summary` | 当前会话已生成的摘要记忆 |
| `memory_summary_used` | 本次调用是否把摘要记忆放入 messages |
| `memory_summary_updated` | 本次调用是否更新了摘要记忆 |
| `memory_summary_failed` | 本次是否尝试更新摘要但失败 |
| `memory_summary_error` | 摘要失败的错误原因 |

摘要压缩不是无损的。它会保留主线、目标、关键知识点、薄弱点和任务状态，但可能丢失原始措辞、细节顺序、语气和一些低频上下文。所以当前策略不是“只用摘要”，而是：

```text
摘要记忆负责长期主线
最近 3 轮负责当前语境
```

面试表达：

```text
我在多轮聊天接口中加入了 summary memory 机制。当会话历史超过最近 3 轮窗口后，后端会把更早且尚未压缩的 user/assistant 消息压缩成摘要记忆，并记录 summarized_messages_count，避免重复压缩同一批历史。后续调用模型时，messages 会按 system + summary_memory + recent_history + current_user 组装。这样既控制了上下文长度和 token 成本，又尽量保留长期学习目标、薄弱点和任务状态，为后续 RAG 记忆和 Agent 状态管理打基础。
```

## Module25：会话持久化

Module25 解决的是“服务重启后会话丢失”的问题。Module23 和 Module24 都已经让后端具备了多轮历史和摘要记忆能力，但它们默认保存在 Python 进程的内存对象里。只要服务停止、电脑关机、进程重启，内存里的 `_CONVERSATIONS` 就会清空。

本模块先使用 JSON 文件做轻量持久化，不直接上数据库。这样做的目的不是说 JSON 比数据库更专业，而是先把“持久化的本质”学清楚：

```text
内存对象 -> 序列化 -> JSON 文件
JSON 文件 -> 反序列化 -> 内存对象
```

保存内容包括：

| 字段 | 为什么必须保存 |
|---|---|
| `conversation_id` | 让前端下次还能继续找到同一段会话 |
| `messages` | 原始 user/assistant 历史，是最重要的原始数据 |
| `summary_memory` | Module24 生成的摘要记忆，避免重启后丢失长期主线 |
| `summarized_messages_count` | 记录已经压缩到哪里，避免重复压缩旧消息 |
| `created_at/updated_at` | 用于后续排序、排查和会话管理 |

核心文件：

| 文件 | 职责 |
|---|---|
| `app/data/conversation_file_store.py` | 负责 Conversation 对象和 JSON 文件之间的序列化、反序列化、保存、读取 |
| `app/data/conversation_store.py` | 仍然作为会话仓库入口，先查内存，内存没有再从 JSON 文件恢复 |
| `app/storage/conversations/` | 保存运行时会话 JSON 文件，真实数据被 `.gitignore` 忽略 |

调用行为：

```text
创建会话 -> 写入内存 -> 保存 JSON
追加 user 消息 -> 更新内存 -> 保存 JSON
追加 assistant 消息 -> 更新内存 -> 保存 JSON
更新 summary_memory -> 更新内存 -> 保存 JSON
服务重启后再次传 conversation_id -> 内存没有 -> 从 JSON 恢复
```

为什么不只保存 `summary_memory`：

```text
summary_memory 是加工后的摘要，不是原始数据。
messages 是原始对话记录。
原始数据可以重新生成摘要，但摘要不能完整还原原始对话。
```

面试表达：

```text
我在多轮聊天项目中加入了轻量级会话持久化。之前会话历史和 summary memory 都保存在 Python 进程内存里，服务重启后会丢失。现在我把 Conversation 对象序列化成 JSON 文件保存，并在内存找不到 conversation_id 时从文件反序列化恢复。这样既保留了 Module23 的多轮历史，也保留了 Module24 的摘要记忆状态。这个版本先用 JSON 理解持久化本质，后续可以平滑替换成 SQLite、MySQL 或 PostgreSQL。
```

## Module26：SSE 流式输出

Module26 新增了 `POST /chat/stream`。它不是替代普通 `/chat`，而是在聊天、长文本讲解、报告生成这类需要等待模型输出的场景下，提供更好的交互体验。

普通 `/chat` 的响应模式是：

```text
前端发送请求
-> 后端等待模型完整生成
-> 一次性返回 JSON
```

`/chat/stream` 的响应模式是：

```text
前端发送请求
-> 后端开始处理
-> 后端持续推送 start / metadata / chunk / done / error 事件
-> 前端收到 chunk 就可以逐步显示内容
```

SSE 的本质是：

```text
text/event-stream 响应类型 + event/data 事件格式
```

其中 `yield` 不是 SSE 本身。`yield` 只是 Python 生成器用来分段产出内容的方式；真正让客户端按 SSE 事件流理解响应的，是 `media_type="text/event-stream"` 和下面这种事件格式：

```text
event: chunk
data: {"content": "一小段回答"}

```

核心链路：

```text
service 生产事件 dict
-> router 转成 SSE 文本
-> StreamingResponse 带着 text/event-stream 类型持续返回
-> 前端根据 start/chunk/done/error 判断当前生成状态
```

核心文件：

| 文件 | 职责 |
|---|---|
| `app/routers/chat.py` | 新增 `/chat/stream`，把 service 事件包装成 SSE 文本，并用 `StreamingResponse` 返回 |
| `app/services/chat_service.py` | 新增 `stream_chat_events()`，复用现有聊天链路并生成 `start/metadata/chunk/done/error` 事件 |

事件含义：

| 事件 | 作用 |
|---|---|
| `start` | 告诉前端流已经开始，并返回 `conversation_id`、`messages_count` 等初始化信息 |
| `metadata` | 返回模型名、usage、fallback 状态等模型调用元信息 |
| `chunk` | 返回真正的回答片段，前端把 `content` 持续拼接到页面上 |
| `done` | 告诉前端本次生成正常结束，可以停止 loading、恢复输入框、保存最终状态 |
| `error` | 告诉前端流式过程中发生错误，避免连接突然断开但前端不知道原因 |

调用示例：

```powershell
curl.exe -N -X POST "http://127.0.0.1:8000/chat/stream" -H "Content-Type: application/json" -d '{\"message\":\"请用一句话解释SSE\",\"mode\":\"study\",\"temperature\":0.3}'
```

返回示例：

```text
event: start
data: {"conversation_id": "conv_xxxxxxxx", "messages_count": 2, "memory_summary_used": false}

event: metadata
data: {"conversation_id": "conv_xxxxxxxx", "model": "mock-chat-model-from-env", "usage": {...}}

event: chunk
data: {"content": "这是 mock 模型回答"}

event: done
data: {"conversation_id": "conv_xxxxxxxx", "history_rounds": 1, "stored_messages_count": 2}
```

当前版本使用 mock 模型模拟流式输出：模型先一次性生成完整 `answer`，后端再按固定长度切成多个 `chunk`。真实大模型 streaming 是模型在生成过程中持续返回 token 或文本片段，后端收到一段就转发一段。Module26 的重点是先跑通 SSE 接口设计、事件格式和前端接收方式，后续接入真实 streaming SDK 时替换底层 `llm_client` 即可。

面试表达：

```text
我在 AI 学习助手项目中新增了 /chat/stream 流式接口。后端通过 FastAPI 的 StreamingResponse 返回 text/event-stream 响应，并把模型生成内容包装成 start、metadata、chunk、done、error 等 SSE 事件持续推送给前端。普通 /chat 继续保留，用于一次性结构化 JSON 返回；/chat/stream 用于长文本生成和聊天场景，前端可以边接收边渲染，提升首字响应速度和用户等待体验。为了保持分层清晰，我让 service 层只生产 event/data 业务事件，router 层再把事件转换成 SSE 文本格式，这样后续即使替换成 WebSocket 或真实模型 streaming，也不会破坏核心业务流程。
```
