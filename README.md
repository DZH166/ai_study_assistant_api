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
  "question": "什么是 FastAPI router？",
  "history": [],
  "temperature": 0.3,
  "prompt_scene": "learning_assistant"
}
```

多轮示例：

```json
{
  "question": "那 schema 又是什么？",
  "conversation_id": "conv_demo",
  "history": [
    {
      "role": "user",
      "content": "什么是 router？"
    },
    {
      "role": "assistant",
      "content": "router 是接口分组和请求分发层。"
    }
  ],
  "temperature": 0.3,
  "prompt_scene": "learning_assistant"
}
```

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
