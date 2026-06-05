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
