# Lovart 模型接口接入开发文档（已据真实契约修订）

> 目标：在不破坏现有 API / ModelScope / RunningHub / 火山引擎 / 即梦 CLI 架构的前提下，把 Lovart 作为一个独立模型平台接入 `daxiong-Canvas`。第一阶段支持图片和视频生成；第二阶段扩展音频、3D、Lovart 项目管理和模式切换。
>
> **本版本说明**：本文档已逐条核对官方 `lovart-skill/agent_skill.py`（约 1015 行）真实源码与 `SKILL.md` 契约，修正了上一版中**请求体结构、模式语义、确认流程、状态机、产物提取、视频同步**等关键错误，并已纳入产品负责人拍板的 6 项决策（见 §1.6）。凡标注「✅ 已核对源码」的，均来自 `agent_skill.py` 实际实现，不再是推测。

---

## 1. 背景和结论

Lovart 的 `lovart-skill` 不是 OpenAI 兼容接口。它是一个面向 AI Agent 的 Skill：客户端通过 Lovart OpenAPI 把自然语言 prompt 提交给 Lovart Agent，Agent 自己规划并调用具体生成工具（GPT Image / Midjourney / Kling / Veo / Seedance / Tripo 等），最终把产物挂在一个 thread 下。

官方仓库：`https://github.com/lovartai/lovart-skill`
核心客户端：`skills/lovart-skill/agent_skill.py`（**所有接口契约以此为准**）

能力概览：

| 类型 | 能力 |
| --- | --- |
| 图片 | 文生图、图生图、海报、Logo、插画、Banner、Mockup、封面等 |
| 视频 | 文生视频、图生视频、产品视频、短片、动画等 |
| 音频 | BGM、歌曲、音效等（README 提及，工具名未在源码硬编码） |
| 编辑 | 图片/视频放大、重构图、风格迁移等 |
| 3D | 文本或图片生成 3D 模型（`generate_3d_tripo`） |
| 项目管理 | project / thread / conversation / canvas link |

当前项目已有 Provider 抽象、异步图片任务、视频接口、素材入库和历史记录，所以 Lovart 可以接入。接入方式是**新增 `lovart` 协议分支**，而不是把 Lovart 当成普通 OpenAI Base URL。

---

## 1.5 已核对的真实接口契约基线（✅ 全部来自 agent_skill.py）

> 这是整份方案的地基。后端实现必须**直接照搬 `agent_skill.py` 的签名与请求逻辑**，不要凭文档二次推测。

### 1.5.1 鉴权与签名（✅ 已核对源码 `_sign` / `_request`）

- Base URL：`https://lgw.lovart.ai`，path 前缀：`/v1/openapi`（构造函数 `path_prefix` 默认值）。
- 签名串：`f"{METHOD}\n{PATH}\n{TS}"`，其中 `TS = str(int(time.time()))`（**Unix 秒**，非毫秒）。
- 签名算法：`hmac.new(secret_key, 串, sha256).hexdigest()`（**hex，小写**）。
- **签名用的 PATH 不含 query string**。query 参数另行拼到 URL 上（见 GET 接口），但签名只对 path。
- 必带请求头：

  ```text
  X-Access-Key:    <LOVART_ACCESS_KEY>
  X-Timestamp:     <秒级时间戳>
  X-Signature:     <hmac sha256 hex>
  X-Signed-Method: <METHOD>
  X-Signed-Path:   <PATH，不含 query>
  Content-Type:    application/json
  User-Agent:      <非空 UA，源码用 Mozilla/5.0 ... LovartAgentSkill/1.0>
  ```
- 通用 JSON POST 额外带 `Idempotency-Key: <uuid hex>`（幂等，重试不会重复计费）；`/file/upload` multipart 按官方 `upload_file()` 特殊路径照搬。
- 每次重试都**重新签名**（时间戳要新鲜）。
- `LOVART_INSECURE_SSL=1` 可关闭证书校验（企业代理场景），默认开启校验。

### 1.5.2 统一响应信封（✅ 已核对源码）

所有 JSON 响应是 `{ "code": int, "message": str, "data": {...}, "details"?: str }`：

- `code == 0` 表示成功，真正的业务数据在 `data` 里（源码 `return result.get("data", result)`）。
- `code != 0` 抛错，错误文案取 `message`（+ `details`）。
- 因此后端 `lovart_request()` 应统一：校验 `code`，成功返回 `data`，失败抛带 message 的异常。

### 1.5.3 端点清单（✅ 已核对源码，全部带 `/v1/openapi` 前缀）

| 方法 | Path | 请求体 / 参数 | 返回（data 内） |
| --- | --- | --- | --- |
| POST | `/chat` | 见 §1.5.4 | `thread_id` |
| GET | `/chat/status` | `?thread_id=` | `status` ∈ `running`/`done`/`abort` |
| GET | `/chat/result` | `?thread_id=` | `items[]`、`thread_id`、可选 `pending_confirmation` |
| POST | `/chat/confirm` | `{thread_id}` | 确认高成本任务后继续执行 |
| POST | `/file/upload` | **multipart/form-data**，字段名 `file` | `url`（CDN 地址） |
| POST | `/project/save` | `{project_id, canvas, project_cover_list:[], pic_count:0, project_type:3, project_name?}` | `project_id`（`project_id` 传空串即新建） |
| GET | `/project/validate` | `?project_id=` | `valid`、`project_name` |
| POST | `/mode/set` | `{unlimited: bool}` | 切换**计费模式**（账号级，见 §1.5.6） |
| POST | `/mode/query` | `{}` | `unlimited`、`unlimited_list`（免费模式模型清单）及账户/余额等可展示信息 |
| POST | `/artifact/upload` | `{project_id, artifact_type, artifact_content}` | 把外链产物登记进 project canvas |

重试策略（✅ 源码）：GET 重试 3 次、POST 1 次；对 `404/429/502/503` 退避重试（`2*(n+1)` 秒）。`404` 也重试，是为了容忍网关路由抖动。

### 1.5.4 chat 请求体（✅ 已核对源码 `send()`）

```jsonc
{
  "prompt": "……",            // 必填
  "project_id": "……",        // 必填（没有就得先建，见 §1.5.5）
  "attachments": ["<CDN URL>"], // 可选，参考图/视频先经 /file/upload 拿到 CDN URL
  "thread_id": "……",         // 可选，复用上下文；第一阶段建议每次新建（见下）
  "mode": "fast",             // 可选，"fast" | "thinking"（推理深度，见 §1.5.6）
  "tool_config": {            // 可选
    "prefer_tool_categories": { "IMAGE": ["..."] }, // 软偏好，Agent 可不理
    "include_tools": ["generate_image_midjourney"], // 硬约束，强制只用这些工具
    "exclude_tools": ["..."]                        // 硬约束，禁用
  }
}
```

> ⚠️ **上一版文档的 `"prefer_models": {"IMAGE":[...]}` 是错的**——真实接口里没有顶层 `prefer_models` 字段。模型偏好必须放进 `tool_config`。`prefer_tool_categories` 是软偏好，`include_tools` 才是硬约束。**本项目按决策 #1 用 `include_tools`**（见 §1.6）。

### 1.5.5 chat 响应与产物提取（✅ 已核对源码 `chat()` / `download_artifacts()`）

`/chat/result` 的 `data` 形如：

```jsonc
{
  "thread_id": "……",
  "items": [
    { "type": "...", "text": "可选的助手文字", "artifacts": [
        { "type": "image", "content": "<产物 URL>" },
        { "type": "video", "content": "<产物 URL>" }
    ]}
  ],
  "pending_confirmation": { /* 存在则表示需确认，见 §1.5.7 */ }
}
```

- **产物是嵌套两层的多对多**：`items[n].artifacts[m].content` 才是真正的 URL。一次生成可能产出**多个 item × 多个 artifact**（多图/变体/图+视频）。上一版 `return {"type":"url","value":artifact_url}`（单数）会丢产物，**必须遍历**。
- 产物 `type` 字段区分 `image`/`video` 等；下载时据此或据 URL 后缀决定扩展名。
- **下载产物 CDN 时必须带浏览器头**（✅ 源码）：`User-Agent: Mozilla/5.0` + `Referer: https://www.lovart.ai/`，否则 CDN 可能 403。上一版漏了这条。

### 1.5.6 两个「mode」是两件事（✅ 已核对源码）——上一版混为一谈

| 维度 | 怎么设 | 取值 | 作用 | 生效范围 |
| --- | --- | --- | --- | --- |
| **推理深度** | chat 请求体 `mode` 字段 | `fast`（默认，单遍） / `thinking`（深度规划） | 控制 Agent 思考强度 | **锁定到 thread 首条消息**，改它必须开新 thread（✅ 源码注释明确） |
| **计费模式** | `POST /mode/set {unlimited}` | `unlimited=false`→fast（扣 credits、不排队） / `unlimited=true`→unlimited（免 credits、排队） | 控制计费/排队 | **账号级、有状态**，影响该 AK/SK 之后**所有**生成；不能写进 chat 请求体 |

> ⚠️ 关键纠正：计费模式是**账号级开关**，必须单独调 `/mode/set`，**不能**像上一版那样塞进 chat 的 `"mode"` 里。chat 里的 `"mode"` 只控推理深度，且一旦 thread 建立就锁死。

### 1.5.7 高成本确认不是一个 status（✅ 已核对源码 `poll()`）

- `/chat/status` 的 `status` **只有** `running` / `done` / `abort` 三种。
- **需要确认时不会出现在 status 里**，而是 `/chat/result` 的 `pending_confirmation` 字段。源码轮询逻辑：
  1. status 第一次变 `done` 后，**先 `sleep(5s)` 再复查**——因为视频等子 Agent 可能还没起，thread 会短暂"假完成"。**naive 的"一见 done 就收工"会拿到空结果**。
  2. running 超过约 20s 后，定期去 `result` 里探 `pending_confirmation`（确认请求可能在 running 期间就冒出来）。
- `timeout` 是**客户端等待超时的本地结果**，不是服务端状态。

### 1.5.8 速率限制与错误码（✅ 来自 SKILL.md / 源码）

- 写操作（chat/confirm）：**60/分、600/时**；读操作（status/result/query）：300/分、3000/时；超限返回 `429`。
- 关键错误码（`message` 已是可直接展示的人话）：

  | HTTP | code | 含义 | 处理 |
  | --- | --- | --- | --- |
  | 402 | 2012 | 配额/计费/风控拒绝（余额不足、免费额度用尽、并发超限、需手机验证等） | 直接展示 `message` |
  | 409 | 2011 | 该 thread 上已有任务在跑 | 等它结束或**开新 thread**（佐证第一阶段每次新建 thread） |
  | 429 | 1429 | 触发限流 | 退避 ~60s 重试 |
  | 401 | — | AK/SK 错误 | 提示检查密钥 |
  | — | — | message 含 `Project ... does not exist` | 项目不存在，校验或新建 |

### 1.5.9 「done 但无产物」判定（✅ 已核对源码）

status=`done` 但 `items` 里没有任何 `artifacts`，通常是上游模型内容审核拒绝 / 超时 / Agent 只回了文字没调工具。源码处理可直接照搬：

- `generation_succeeded = any(item.artifacts)`；
- 无产物时置 `generation_succeeded=False`、写 `warning`、把 `items[].text` 汇成 `agent_message`。
- 后端必须把这种情况判成**失败**，不能生成空画布节点。

---

## 1.6 产品决策（已拍板，本文档据此设计）

| # | 决策点 | 结论 | 工程含义 |
| --- | --- | --- | --- |
| 1 | 模型选择语义 | **硬约束** | 用户在下拉框选的模型 → `tool_config.include_tools=[model]`。Agent 不得偷换；若 Lovart 返回工具不可用、无产物或错误，按错误明确提示（不静默替换）。不能仅因模型不在 `mode/query.unlimited_list` 就判定不可用。 |
| 2 | 计费模式 | **用户可切换，默认免费模式** | 免费模式=`unlimited=true`（排队、不扣 credits）；付费模式=`unlimited=false`（扣 credits、少排队）。用户在 Lovart 模型选择/生成设置处选择本次使用免费还是付费，后端在提交 Lovart chat 前调用 `/mode/set`。因计费模式是账号级全局状态，后端必须用 Lovart 提交锁包住「set_mode → send」以避免并发任务互相切模式。 |
| 3 | 付费模型确认 | **第一阶段支持付费模型和内嵌确认** | 用户可在第一阶段选择付费模型；若 Lovart 返回 `pending_confirmation`，前端展示预计 credits，用户确认后调用 `/api/lovart/confirm`，后端再 `/chat/confirm` 并继续 poll。不自动扣费，不静默确认。 |
| 4 | 视频是否进第一阶段 | **进，但仅 Lovart 视频走异步任务** | 新增 `/api/canvas-video-tasks` 只服务 Lovart；OpenAI/APIMart/火山/即梦等旧视频 provider 继续走现有同步 `/api/canvas-video`，避免扩大回归面。 |
| 5 | 尺寸/质量 | 真实 chat 体**无结构化尺寸字段** → 按兜底**拼进 prompt 提示**；若 Lovart 后续开放结构化字段再切 | 见 §7.3 |
| 6 | credits 可见性 | **必须展示；不设消费上限** | 模型下拉展示实测成本标签（如 10/14/50 credits 或"排队/待确认"）；真正扣费前以 `pending_confirmation.estimated_cost` 为准展示确认弹窗。设置页/侧栏显示账户余额（若 `mode/query` 返回）。 |

---

## 1.7 能力边界：Lovart 是 Agent-only，没有"裸模型 / 结构化参数"（✅ 已核对源码，务必先读）

这是接入前必须达成的共识，否则会按"传统模型 API"去设计，落地后发现做不到。

### 1.7.1 能不能"不走 Agent、直连模型"？——**不能**

Lovart OpenAPI **唯一的生成入口就是 `POST /v1/openapi/chat`**，它必然进 Lovart Agent。源码里没有任何 `/v1/images/generations`、`/v1/video/create` 之类的直连模型端点。也就是说：

- 没有"绕过 Agent"的路径。即使强制指定模型，请求仍由 Agent 接收 → 解析 prompt → 调工具 → 可能内容审核拒绝 / 加步骤 / 排队。
- Agent 是 Lovart 的**强制中间层**，不是可选项。

### 1.7.2 能不能"独立选择模型"？——**能（硬约束），但仍经 Agent**

通过 `tool_config.include_tools=["generate_image_midjourney"]`（即决策 #1）可以**强制 Agent 只用你选的那个模型**，这是 Lovart 允许的最强"指定模型"。效果上≈"用户选 Midjourney 就只出 Midjourney"，但：

- 仍是"告诉 Agent 必须用这个工具"，不是"直接调这个模型"。
- `mode/query.unlimited_list` 只标记免费模式模型，不能用来否定付费模型可用性。付费模型是否可执行，以 `send/include_tools` 后的 `pending_confirmation`、`done` 产物或明确错误为准；失败时必须明确报错（不静默替换）。

### 1.7.3 能不能"独立选择模型参数"（尺寸/步数/CFG/seed/质量等）？——**不能结构化选**

`/chat` 请求体的全部可控输入只有：`prompt`（自然语言）、`attachments`（参考文件）、`tool_config`（用哪些工具）、`mode`（推理深度）。**没有任何结构化参数字段**——没有 width/height、没有 steps、没有 cfg、没有 seed、没有 quality 枚举。所以：

- 参数只能**写进 prompt 当自然语言提示**（"约 1024×1024、high 质量、电影感"），由 Agent/上游模型尽力理解，**不保证精确生效**（决策 #5）。
- 想要"参数滑块 / seed 复现 / 精确分辨率"这类传统模型控制 —— **Lovart 给不了**。

### 1.7.4 由此引出的产品判断（建议产品负责人确认）

| 你的目标 | 适合的方案 |
| --- | --- |
| 要"Agent 出成品"：一句话出海报/logo/分镜，自动编排、自动选/换模型 | ✅ Lovart 正是为此而生 |
| 要"裸模型 + 参数滑块（尺寸/步数/seed/CFG）、可复现" | ❌ Lovart 做不到；**项目里现有的 OpenAI 兼容 / APIMart / 火山 / 即梦 / ModelScope / RunningHub 已经能做且更直接** |
| 想用某些"只有 Lovart 才有"的模型（特定 Midjourney/Veo 版本等） | ✅ 用 Lovart + `include_tools` 锁定该模型，但接受"经 Agent + 仅 prompt 级参数" |

> 一句话：**Lovart 的价值是 Agent 编排和它独家的模型阵容，不是"又一个可调参的模型网关"。** 如果用户真正想要的是后者，本项目已有更合适的 provider，接 Lovart 反而是降级。这点决定了 Lovart 在产品里的定位——是"智能成品生成"入口，而非"精细调参出图"入口。

---

## 2. 当前项目架构约束

| 层 | 文件 / 接口 | 现状 |
| --- | --- | --- |
| 后端应用 | `main.py` | FastAPI 单文件主应用（约 13900 行），Provider 逻辑集中在此 |
| Provider 配置 | `data/api_providers.json` + `/api/providers` | `id/name/base_url/protocol/image_models/video_models` |
| 图片任务 | `POST /api/canvas-image-tasks` + `GET /api/canvas-image-tasks/{task_id}` | **异步**：内存任务表 `CANVAS_TASKS` + `asyncio.create_task` + 前端轮询 |
| 视频任务 | `POST /api/canvas-video` | **同步**：单请求内 `await` 等上游返回 |
| 智能画布 | `static/js/smart-canvas.js` | 图片 `runApiGeneration()`、视频 `runApiVideoGeneration()` |
| API 设置页 | `static/api-settings.html` + `static/js/api-settings.js` | 选协议、填 Key、拉模型 |
| 资源输出 | `data/output` / `/output/...` | 上游结果下载到本地再返回可访问 URL |
| 密钥存储 | `API/.env` | `update_env_values()` 写文件并同步 `os.environ` |

当前已支持协议（✅ 已核对 `main.py:255`，注意上一版漏了 `codex_cli`）：

```python
SUPPORTED_PROVIDER_PROTOCOLS = {"openai", "apimart", "gemini", "volcengine", "runninghub", "jimeng", "codex_cli"}
```

新增：`"lovart"`。

> ⚠️ 关键风险：`CANVAS_TASKS` 是**内存字典**，服务重启即丢（404 文案已写"可能服务已重启"）。Lovart Agent 任务动辄数分钟，所以 `thread_id` / `project_id` 必须落盘以便恢复（见 §15.3）。

---

## 3. 接入原则

1. 不改现有 OpenAI / APIMart / Gemini / 火山 / RunningHub / 即梦 / Codex 路径的行为。
2. 不把 Lovart 塞进 OpenAI 兼容分支。
3. 前端绝不直接访问 Lovart；AK/SK、签名、上传下载全在后端。
4. 第一阶段复用现有异步图片任务接口；**视频也改异步任务**（决策 #4），不用同步 `/api/canvas-video`。
5. Lovart 返回的远程 URL 必须下载到本地输出目录（带 §1.5.5 的 CDN 头）再交给画布。
6. 用户选的模型走**硬约束 `include_tools`**（决策 #1）；模型不可用要明确报错，不静默替换。
7. 高成本确认、排队、失败、无产物、限流都要明确提示，不能静默失败。
8. Lovart model id 用官方 tool name（如 `generate_image_midjourney`），避免显示名与调用名混乱。
9. 后端**直接照搬 `agent_skill.py` 的签名/请求实现**，不要重写。

---

## 4. 总体架构设计

### 4.1 接入位置

```text
前端智能画布 / 普通画布
  -> 图片：/api/canvas-image-tasks（异步，已存在）
     视频：/api/canvas-video-tasks（异步，新增，决策 #4）
    -> main.py Provider 分发
      -> services/lovart_service.py（照搬 agent_skill.py 逻辑）
        -> Lovart OpenAPI (/v1/openapi/*)
          -> Lovart Agent
            -> GPT Image / Midjourney / Kling / Veo / Seedance / Tripo ...
```

### 4.2 不推荐方案

- 前端直连 Lovart → AK/SK 暴露在浏览器。
- Lovart 配成 OpenAI Base URL → 需要 HMAC 签名 + project/thread 语义，不是 `/v1/images/generations`。
- 长期 shell 调 `agent_skill.py` → 不利于错误处理/任务状态/路径/打包。**但可作为 M0 的契约验证探针**（见 §16）。

---

## 5. 模型映射（✅ 全部经 M0 探针实测，非文档推测）

> **关键结论：`mode/query` 的 `unlimited_list` ≠ "全部可用模型"**
>
> `unlimited_list` 只列出 unlimited 模式下**免费不扣积分**的模型。Seedance v2、Kling v3、Veo3 等视频模型**不在该列表里，但 API 完全支持调用**——只是会先触发 `pending_confirmation`（询问是否消耗 credits），确认后才正式执行。**`pending_confirmation` 本身不扣积分**，只有调用 `/chat/confirm` 才真正消费。
>
> 模型分为免费、免确认、付费确认、排队待验证四类，后端接入方式不同（见 §5.8）：

### 5.1 免费图片模型（✅ 实测：unlimited 模式直接出图，不扣积分）

这 9 个模型来自 `mode/query.unlimited_list`，实测均在 unlimited 模式下立即完成、无 `pending_confirmation`：

| 显示名 | tool name | 备注 |
| --- | --- | --- |
| GPT Image 1.5 | `generate_image_gpt_image_1_5` | |
| GPT Image 2 | `generate_image_gpt_image_2` | |
| GPT Image 2（低质量） | `generate_image_gpt_image_2_low` | 实测直接完成，不触发确认 |
| Midjourney | `generate_image_midjourney` | |
| Nano Banana | `generate_image_nano_banana` | |
| Nano Banana 2 | `generate_image_nano_banana_2` | 4K 输出 |
| Nano Banana Pro | `generate_image_nano_banana_pro` | 4K 输出 |
| Seedream 4 | `generate_image_seedream_v4` | |
| Seedream 4.5 | `generate_image_seedream_v4_5` | |

### 5.2 免确认图片模型（✅ 实测：直接完成；是否扣费以余额/账单为准）

这些模型在本账号实测中不触发 `pending_confirmation`，可以直接完成；但它们不在 `unlimited_list` 的结论里时，产品文案不要承诺"免费不扣积分"，只标注为"免确认"：

| 显示名 | tool name | 备注 |
| --- | --- | --- |
| Flux 2 Max | `generate_image_flux_2_max` | 实测直接完成 |
| Flux 2 Pro | `generate_image_flux_2_pro` | 实测直接完成 |
| Ideogram v4 | `generate_image_ideogram_v4` | 实测直接完成 |
| Seedream 5 | `generate_image_seedream_v5` | 实测直接完成 |

### 5.3 付费图片模型（第一阶段支持；确认后才扣积分）

| 显示名 | tool name | 预计积分 | 备注 |
| --- | --- | --- | --- |
| GPT Image 2（中质量） | `generate_image_gpt_image_2_medium` | **14 credits** | 实测触发 `pending_confirmation` |
| GPT Image 2（高质量） | `generate_image_gpt_image_2_high` | **50 credits** | 实测触发 `pending_confirmation`，当前最贵图片模型 |
| Luma Uni 1 | `generate_image_luma_uni_1` | 待确认 | unlimited 模式下排队；付费模式需以 `pending_confirmation.estimated_cost` 为准 |
| Luma Uni 1 Max | `generate_image_luma_uni_1_max` | 待确认 | unlimited 模式下排队；付费模式需以 `pending_confirmation.estimated_cost` 为准 |

### 5.4 免费视频模型（✅ 实测：来自 unlimited_list，unlimited 模式下排队免费）

| 显示名 | tool name | 备注 |
| --- | --- | --- |
| Kling 2.6 | `generate_video_kling_v2_6` | |
| Kling O1 | `generate_video_kling_omni_v1` | |
| Wan 2.6 | `generate_video_wan_v2_6` | |

### 5.5 付费视频模型（第一阶段支持；确认后才扣积分）

| 显示名 | tool name | 预计积分 | 备注 |
| --- | --- | --- | --- |
| Seedance v2 | `generate_video_seedance_v2_0` | **14 credits** | 实测触发 `pending_confirmation` |
| Seedance v2 Fast | `generate_video_seedance_v2_0_fast` | 待确认 | unlimited 模式下超时；付费模式需以 `pending_confirmation.estimated_cost` 为准 |
| Seedance Pro 1.5 | `generate_video_seedance_pro_v1_5` | **14 credits** | 实测触发 `pending_confirmation` |
| Kling v3 | `generate_video_kling_v3` | 待确认 | unlimited 模式下超时；付费模式需以 `pending_confirmation.estimated_cost` 为准 |
| Kling v3 Omni | `generate_video_kling_v3_omni` | 待确认 | unlimited 模式下超时；付费模式需以 `pending_confirmation.estimated_cost` 为准 |
| Veo3 | `generate_video_veo3` | **10 credits** | 最便宜付费视频 |
| Veo3.1 | `generate_video_veo3_1` | **14 credits** | |
| Veo3.1 Fast | `generate_video_veo3_1_fast` | **14 credits** | |
| Hailuo v2.3 | `generate_video_hailuo_v2_3` | **14 credits** | |
| Vidu Q2 | `generate_video_vidu_q2` | **14 credits** | |

### 5.6 3D 模型（付费，第二阶段）

| 显示名 | tool name | 预计积分 | 备注 |
| --- | --- | --- | --- |
| Tripo 3D | `generate_3d_tripo` | **14 credits** | 触发 `pending_confirmation` |

当前无一等 `3d_models` 字段与 3D 预览/下载，第二阶段新增 `three_d_models` 或独立面板，不混入 `image_models/video_models`。

### 5.7 音频（第二阶段）

README 提及音频/BGM/歌曲/音效，但源码未硬编码音频 tool name，`mode/query` 也未返回音频模型。第一阶段不硬编码；待 `mode/query` 返回音频工具后再加 `audio_models` 与音频输出卡片。

### 5.8 目标模式与后端接入差异（✅ 核心设计）

第一阶段支持免费模型、免确认模型和付费模型。用户在 Lovart 模型选择/生成设置阶段选择本次走：

- **免费模式**：`/mode/set {unlimited:true}`，默认值；优先用于 unlimited 免费模型，可能排队。
- **付费模式**：`/mode/set {unlimited:false}`；用于付费模型或用户想减少排队时，扣费前必须展示确认弹窗。

因为 `/mode/set` 是账号级全局状态，后端必须加 Lovart 提交锁：同一时刻只允许一个 Lovart 请求执行「set_mode → send」，拿到 `thread_id` 后释放锁，后续 poll 可并发。

#### A 类：免费 / 免确认模型（直接完成，无需确认）

```
send(include_tools=[model]) → poll() → done → extract_artifacts → download → 返回产物
```

- 图片任务异步走现有 `CANVAS_TASKS`，轮询即可。
- 来自 `unlimited_list` 的模型可标注"免费模式"；免确认但不在 `unlimited_list` 的模型只标注"免确认"，不承诺不扣费。

#### B 类：付费模型（需 `pending_confirmation` 确认后才执行）

```
send(include_tools=[model])
  → poll() 发现 pending_confirmation
    → 任务状态标记为 "pending_confirmation"
    → 返回给前端：{ status:"pending_confirmation", task_id:"...", thread_id:"...", estimated_cost:14 }
      ↓ 前端展示确认弹窗（第一阶段必须实现）
      ↓ 用户点"确认消耗 14 credits"
    → POST /api/lovart/confirm { task_id, thread_id }
      → 后端调 lovart_confirm(thread_id)
        → poll() 继续等待直到 done
          → extract_artifacts → download → 返回产物
```

关键：
- `pending_confirmation` 本身**不扣积分**，只是一次询问。
- 只有 `/chat/confirm` 才真正开始执行并扣费。
- 弹窗成本优先取 `pending_confirmation.estimated_cost`；若字段缺失，则展示 §5 表格里的实测成本或"待确认"。
- **第一阶段必须做确认闭环**：前端弹窗 → 用户确认 → 后端 confirm → 继续 poll → 返回产物。

#### C 类：排队中的模型（unlimited 模式下超时，fast 模式下走 B 类）

Seedance v2 Fast、Kling v3/v3 Omni、Luma 等在 unlimited 模式下会排很长的队。建议：
- unlimited 模式：超时后任务状态保持 `running`，凭落盘的 `thread_id` 稍后用 `/chat/result` 续查（§15.3）。
- fast 模式：这些模型会触发 `pending_confirmation`，走 B 类确认流程。

#### 后端判断逻辑（任务状态机）

```python
result = await lovart_poll(thread_id, timeout=300)

match result["final_status"]:
    case "done":
        if result.get("generation_succeeded"):
            # A类正常完成 → 下载产物
            artifacts = lovart_extract_artifacts(result)
            local_urls = [await lovart_download_artifact(a) for a in artifacts]
            return {"status": "succeeded", "urls": local_urls}
        else:
            # done 但无产物（内容审核拒绝 / Agent 只回文字）
            return {"status": "failed", "error": result.get("agent_message") or result.get("warning")}

    case "pending_confirmation":
        # B类付费模型等待确认
        pc = result.get("pending_confirmation", {})
        return {
            "status": "pending_confirmation",
            "thread_id": thread_id,
            "estimated_cost": pc.get("estimated_cost", 0),
            "message": f"本次生成需消耗约 {pc.get('estimated_cost', '?')} 积分，请确认后继续"
        }

    case "abort":
        return {"status": "failed", "error": "Lovart Agent 终止任务"}

    case "timeout":
        return {"status": "running", "thread_id": thread_id,
                "message": "任务仍在队列中，可稍后凭 thread_id 续查"}
```

### 5.9 `image_models` / `video_models` 的建议写法（写入 Provider 配置）

基于实测，第一阶段应包含免费、免确认和付费模型，前端下拉全部展示，并用标签标注 `免费` / `免确认` / `10 credits` / `14 credits` / `50 credits` / `待确认`。差异在**后端任务状态**（免费/免确认直接完成，付费走确认）。建议按类型分组展示（免费优先排在前）：

**`image_models`**（写入 `data/api_providers.json`）：
```json
[
  "generate_image_midjourney",
  "generate_image_gpt_image_1_5",
  "generate_image_gpt_image_2",
  "generate_image_gpt_image_2_low",
  "generate_image_nano_banana",
  "generate_image_nano_banana_2",
  "generate_image_nano_banana_pro",
  "generate_image_seedream_v4",
  "generate_image_seedream_v4_5",
  "generate_image_flux_2_max",
  "generate_image_flux_2_pro",
  "generate_image_ideogram_v4",
  "generate_image_seedream_v5",
  "generate_image_gpt_image_2_medium",
  "generate_image_gpt_image_2_high",
  "generate_image_luma_uni_1",
  "generate_image_luma_uni_1_max"
]
```

**`video_models`**（写入 `data/api_providers.json`）：
```json
[
  "generate_video_kling_v2_6",
  "generate_video_kling_omni_v1",
  "generate_video_wan_v2_6",
  "generate_video_veo3",
  "generate_video_veo3_1",
  "generate_video_veo3_1_fast",
  "generate_video_seedance_v2_0",
  "generate_video_seedance_v2_0_fast",
  "generate_video_seedance_pro_v1_5",
  "generate_video_kling_v3",
  "generate_video_kling_v3_omni",
  "generate_video_hailuo_v2_3",
  "generate_video_vidu_q2"
]
```

> 注：实际免费模型、成本和排队表现可能因账户套餐变化；`mode/query.unlimited_list` 只用于标记免费模式，付费成本以 `pending_confirmation.estimated_cost` 为准。上述清单基于本账户实测。

---

## 6. 后端设计

### 6.1 新增服务模块 `services/lovart_service.py`

> 实现方式：把 `agent_skill.py` 的 `AgentSkill` 类**整段移植**为项目内服务（去掉 CLI 部分），用 `httpx`/`requests` 替换 `urllib` 以契合现有异步风格即可。签名、信封、重试、产物提取、下载头、done-race、pending_confirmation 探测**逐行保留**。

| 函数 | 作用 | 对应源码 |
| --- | --- | --- |
| `lovart_access_key()` / `lovart_secret_key()` | 读 `LOVART_ACCESS_KEY/SECRET_KEY` | env |
| `lovart_sign(method, path)` | HMAC-SHA256（秒级 ts、hex、五个 X-头；通用 JSON POST 带 Idempotency-Key） | `_sign` |
| `lovart_request(method, path, body, params)` | 统一请求：签名→校验 `code`→返回 `data`；404/429/502/503 退避重试 | `_request` |
| `lovart_ensure_project()` | 复用/校验/新建 project，返回 `project_id`（见 §6.7） | `create_project`/`validate_project` |
| `lovart_upload_file(path)` | multipart 上传本地参考图，返回 CDN URL | `upload_file` |
| `lovart_send(prompt, project_id, attachments, include_tools, mode, thread_id=None)` | 提交 chat，返回 `thread_id` | `send` |
| `lovart_status(thread_id)` / `lovart_result(thread_id)` | 查状态 / 取结果 | `get_status`/`get_result` |
| `lovart_poll(thread_id, timeout)` | 轮询至 done/abort/pending_confirmation/timeout，含 5s done-race 复查与 pending 探测 | `poll` |
| `lovart_confirm(thread_id)` | 高成本确认（第二阶段接弹窗） | `confirm` |
| `lovart_extract_artifacts(result)` | 遍历 `items[].artifacts[].content`，返回多产物列表（含 type） | `download_artifacts` 取值部分 |
| `lovart_download_artifact(url, type)` | 带 `User-Agent`+`Referer` 头下载到本地输出目录 | `download_artifacts` |
| `lovart_set_mode(unlimited)` / `lovart_query_mode()` | 计费模式切换/查询（含免费模式清单与账户信息） | `set_mode`/`query_mode` |

### 6.2 环境变量

```bash
LOVART_ACCESS_KEY=ak_xxx
LOVART_SECRET_KEY=sk_xxx
LOVART_BASE_URL=https://lgw.lovart.ai
```

可选：

```bash
LOVART_INSECURE_SSL=0          # 1 关闭证书校验（企业代理）
LOVART_REASONING_MODE=fast     # 推理深度默认（fast|thinking），写入 chat 请求体
# 计费模式不是 env，而是账号级状态，通过 /mode/set 切换并由 /mode/query 读取（见 §1.5.6）
```

> ⚠️ 纠正：上一版 `LOVART_DEFAULT_MODE=fast` 语义不清。这里拆开：`LOVART_REASONING_MODE` 控推理深度（chat 体字段）；**计费模式不放 env**，它是账号级有状态开关。

AK/SK 不写入前端、不返回浏览器。

### 6.3 Provider 注册

`default_api_providers()` 增加：

```python
{
    "id": "lovart", "name": "Lovart",
    "base_url": "https://lgw.lovart.ai", "protocol": "lovart",
    "enabled": True, "primary": False,
    "image_models": LOVART_IMAGE_MODELS,
    "video_models": LOVART_VIDEO_MODELS,
    "chat_models": [], "ms_loras": [], "ms_defaults_version": 0,
}
```

`normalize_provider()` 增加 lovart 分支（固定协议 + 默认 base_url）；新增判定：

```python
def is_lovart_provider(provider):
    return provider_protocol(provider) == "lovart" or str((provider or {}).get("id") or "").lower() == "lovart"
```

### 6.4 Key 展示（仿火山 AK/SK，参 `main.py:1169`）

`public_provider()` 对 lovart 返回 `has_lovart_access_key` / `lovart_access_key_preview`（mask）/ `lovart_access_key_env` 及对应 secret 字段；**不返回原始 key**。

### 6.5 保存 Key（仿火山，参 `main.py:2425` / `9122`）

`ApiProviderPayload` 增加：

```python
lovart_access_key: Optional[str] = None
lovart_secret_key: Optional[str] = None
clear_lovart_access_key: bool = False
clear_lovart_secret_key: bool = False
```

保存时经 `update_env_values()`（`main.py:1246`）写 `API/.env` 并同步 `os.environ`，不写入 `data/api_providers.json`。

### 6.6 模型拉取/验证与计费模式

- `/api/providers/test-connection`：`protocol=="lovart"` 时走 `lovart_test_connection()`——调一次 `mode/query` 验证 AK/SK，并读取当前免费模式清单/余额等可展示信息。注意：`mode/query.unlimited_list` 不能用于否定付费模型可用性。
- `/api/providers/fetch-models`：第一阶段返回 §5.9 的内置模型快照，并叠加 `mode/query.unlimited_list` 标记哪些模型属于免费模式；不要因为付费模型不在 `unlimited_list` 就过滤掉。
- **新增（决策 #2，进第一阶段）**计费模式开关：
  - `GET /api/lovart/mode` → `lovart_query_mode()`（返回 fast/unlimited + 免费模式清单/余额等信息）
  - `POST /api/lovart/mode` `{unlimited: bool}` → `lovart_set_mode()`

### 6.7 project 处理（✅ 决策 #1 的前置，第一阶段必须）

真实 chat **必须带 `project_id`**。第一阶段策略：

1. 后端维护一个「画布默认 Lovart project」，id 持久化到 `data/`（如 `data/lovart_state.json`，类比 CLI 的 `~/.lovart/state.json`）。
2. 启动/首次生成时：若无 project_id → `save_project(project_id="")` 新建并落盘；若有 → `validate_project` 校验（新建项目可能需 ~2s 同步，失败重试一次）。
3. **reasoning mode 锁 thread**、且**同 thread 不能并发（409）**，所以第一阶段**每次生成新建 thread**（不传 `thread_id`），thread_id 随任务落盘用于 status/result/confirm/恢复。

### 6.8 设置页认证字段与连通性验证（✅ 本节回答"要填什么 + 怎么验"）

#### 6.8.1 用户在 API 设置页要填的内容

Lovart 没有 OAuth / token 交换，认证就是 **AK/SK + HMAC 签名**。设置页表单字段：

| 界面字段 | 写入 env | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| Access Key | `LOVART_ACCESS_KEY` | 是 | — | 在 **Lovart 平台（lovart.ai）**的开发者 / API 凭证页申请（控制台具体路径以平台为准） |
| Secret Key | `LOVART_SECRET_KEY` | 是 | — | 同上，**只在后端保存，绝不回前端**（只回 mask 预览） |
| Base URL | `LOVART_BASE_URL` | 否 | `https://lgw.lovart.ai` | 一般不用改，预填即可 |
| 关闭证书校验 | `LOVART_INSECURE_SSL` | 否 | 关（`0`） | 仅企业代理 / TLS 拦截场景勾选 |
| 计费模式 | 不入 env（账号级状态） | 否 | 免费模式（`unlimited=true`） | 免费/付费模式开关，调 `/api/lovart/mode`（决策 #2），旁显 credits（决策 #6） |

> 用户拿到 AK/SK 的前提：先在 Lovart 平台注册并开通 OpenAPI 权限。这一步在本产品之外，文档只负责"填进来 + 验证可用"。

#### 6.8.2 后端要留出的端点（即"把端口留出来"）

| 端点 | 状态 | 行为 |
| --- | --- | --- |
| `POST /api/providers/test-connection` | **复用、加 lovart 分支** | 见 6.8.3，连通性验证主入口 |
| `PUT /api/providers` | 已存在、加 lovart 字段（§6.5） | 保存 AK/SK 到 `API/.env` |
| `GET /api/providers` | 不改（§6.4） | 回 mask 预览 + `has_lovart_*_key` |
| `GET /api/lovart/mode` / `POST /api/lovart/mode` | 第一阶段新增（§6.6） | 计费模式查询 / 切换 |

#### 6.8.3 连通性验证：用只读的 `mode/query`

`test_provider_connection`（`main.py:9413`）顶部像 jimeng 一样加 lovart 分支（在通用 base_url/`/v1/models` 逻辑之前，因为 Lovart 没有 `/v1/models`）：

```python
if protocol == "lovart":
    return await lovart_test_connection(payload)
```

`lovart_test_connection` 调一次**只读、不计费、不生成**的 `POST /v1/openapi/mode/query {}`（已签名），一箭双雕：① 验证 AK/SK 是否有效；② 顺带取回当前计费模式、免费模式清单与余额等可展示信息。返回沿用现有结构：

```jsonc
{ "ok": true, "status": 200, "message": "Lovart AK/SK 验证通过（当前 fast 模式）",
  "model_count": 30, "image_models": ["..."], "video_models": ["..."],
  "chat_models": [], "all": ["..."], "raw": { "unlimited": false } }
```

结果判读：

| 结果 | 含义 / 提示 |
| --- | --- |
| 200 + `code==0` | 验证通过，回模型清单 + 当前模式 |
| 401 | AK/SK 错误 → "鉴权失败，请检查 Access Key / Secret Key" |
| 网络 / SSL 错误 | "连不上 Lovart，请检查网络；企业代理可尝试勾选关闭证书校验" |
| 429/1429 | "请求过于频繁，请稍后重试"（验证阶段极少触发） |

#### 6.8.4 验证用"刚输入的"还是"已保存的"key

现有 `TestConnectionPayload`（`main.py:9188`）只有单个 `api_key` 字段，对**双密钥**的火山是"先保存再验证"（`api_key_from_payload` 对火山只读 env）。Lovart 同为双密钥，两种做法：

- **本项目采用（更好 UX）**：给 `TestConnectionPayload` 加 `lovart_access_key` / `lovart_secret_key`，允许**输入即测、保存前先验**；后端验证时优先用 payload 里的、为空再回落 env。输入→验证通过→再保存，避免"先存一组错的再测"的回路。
- 备选（与火山一致、改动最小）：先保存写入 `.env`，再点验证读 env。

---

## 7. 图片生成接入

### 7.1 现有链路

```text
smart-canvas.js runApiGeneration()
  -> POST /api/canvas-image-tasks  (异步)
    -> run_canvas_image_task() -> build_online_image_result() -> generate_ai_image()
```

### 7.2 Lovart 分支（`generate_ai_image`，参 `main.py:7666`）

`generate_ai_image(prompt, size, quality, model, reference_images=None, provider_id="comfly")` 内部已 `provider = get_api_provider(provider_id)`。在火山分支之后加：

```python
if is_lovart_provider(provider):
    return await generate_lovart_provider_image(prompt, size, quality, model, reference_images, provider)
```

### 7.3 后端入参转换（✅ 已按真实契约修正）

现有图片请求 → Lovart chat：

```jsonc
{
  "prompt": "<原始 prompt>。<尺寸/质量作为附加约束拼进来，决策 #5>",
  "project_id": "<§6.7 取得>",
  "attachments": ["<reference_images 经 lovart_upload_file 上传后的 CDN URL>"],
  "mode": "fast",                                  // 推理深度，来自 LOVART_REASONING_MODE
  "tool_config": { "include_tools": ["<用户选的 model>"] }  // 决策 #1 硬约束
}
```

要点：

1. 参考图必须先 `lovart_upload_file()` 上传成 CDN URL 再放进 `attachments`。
2. `size/quality`：真实 chat 体无对应字段 → **拼进 prompt 提示**（决策 #5）。例：`"……。目标尺寸约 1024x1024，画质 high。"`
3. 用户选的 `model` 放 `include_tools`（硬约束）。**不要**用上一版的顶层 `prefer_models`。
4. 不大幅改写用户 prompt，Lovart Agent 自己会理解。
5. 现有 `n` 参数无干净映射（Agent 自行决定产物数）；第一阶段忽略 `n`，按实际返回的多产物处理。

### 7.4 返回转换（✅ 已按真实契约修正）

```python
# poll 到 done 后取 result，遍历多产物
artifacts = lovart_extract_artifacts(result)      # [{type, url}, ...]
if not result.get("generation_succeeded", bool(artifacts)):
    raise HTTPException(502, detail=result.get("agent_message") or result.get("warning") or "Lovart 未产出产物")
local_urls = [await lovart_download_artifact(a["url"], a["type"]) for a in artifacts]  # 带 CDN 头
# 复用现有：save_ai_image_to_output / save_to_history / manager.broadcast_new_image
return {"type": "url", "value": local_urls[0], "extra_values": local_urls[1:]}, result
```

> 若现有返回结构只接受单图，第一阶段可先取首张、其余作为附带产物入素材库；但**不要丢弃**多产物。

---

## 8. 视频生成接入（✅ 决策 #4：改为异步任务）

### 8.1 为什么不用同步 `/api/canvas-video`

现有 `canvas_video()`（`main.py:10342`）在**单个 HTTP 请求内 `await` 等到底**。Lovart 视频经 Agent（可能含 thinking、子 Agent、排队），耗时常达数分钟，加上 §1.5.7 的「done 后还要 5s 复查子 Agent」，同步路径极易超时 → 画布拿不到结果。

### 8.2 新增异步视频任务（镜像图片任务机制）

```text
POST /api/canvas-video-tasks         -> 建任务，asyncio.create_task 跑 run_canvas_video_task，返回 {task_id, status:"queued"}
GET  /api/canvas-video-tasks/{id}    -> 轮询任务状态/结果
```

`run_canvas_video_task` 复用 `CANVAS_TASKS` + `CANVAS_TASK_LOCK`（与图片任务同一套，`type:"online-video"`）。内部对 lovart：`ensure_project → upload 参考帧 → send(include_tools=[model]) → poll → 多产物下载`。

> 兼容：其它 provider 的视频仍走原同步 `/api/canvas-video`（不动）。第一阶段**只对 Lovart 视频**走 `/api/canvas-video-tasks`，避免把 APIMart/火山/即梦等旧视频链路一起重构。

### 8.3 后端入参转换

```jsonc
{
  "prompt": "<原始>。时长 5 秒，比例 16:9，分辨率 720p。",   // 结构化字段拼进 prompt（决策 #5）
  "project_id": "<§6.7>",
  "attachments": ["<首/尾帧经 upload 后的 CDN URL>"],
  "mode": "fast",
  "tool_config": { "include_tools": ["<用户选的视频 model>"] }
}
```

> 注意：Lovart `attachments` 是**扁平列表**，丢失现有视频接口的 `first_frame/last_frame/reference` 角色语义。第一阶段：把角色信息也拼进 prompt（"第一张为首帧、第二张为尾帧"）；若后续 Lovart 开放结构化首尾帧再切。

### 8.4 返回转换

```jsonc
{ "videos": ["/output/lovart_xxx.mp4"], "task_id": "<本地任务 id>", "thread_id": "<Lovart thread_id>", "raw": {} }
```

下载复用 `save_remote_video_to_output()`，但下载 Lovart CDN 时**必须带 §1.5.5 的 UA+Referer 头**。视频常**先出占位/分镜图再出成片**——按 §1.5.7 的 done-race 处理，别提前收工。

---

## 9. 音频和 3D 扩展规划（第二阶段）

### 9.1 音频

视频请求里已有的 `audios` 字段是"视频参考输入"，不是"生成音频输出"入口。新增统一接口：

```text
POST /api/lovart/generate  { "kind":"audio", "prompt":"...", "model":"", "attachments":[] }
->  { "audios":["/output/lovart_xxx.mp3"], "thread_id":"...", "raw":{} }
```

前端需新增：音频生成模式、音频输出卡片、素材库音频分类、播放/下载控件。

### 9.2 3D

不塞进图片/视频选择器。新增：

```text
POST /api/lovart/3d  { "prompt":"a low-poly sci-fi drone", "model":"generate_3d_tripo", "reference_images":[] }
->  { "models":["/output/lovart_xxx.glb"], "previews":["/output/lovart_xxx.png"], "thread_id":"...", "raw":{} }
```

前端需新增：3D 输出类型、`.glb/.obj/.fbx` 下载、可选 Three.js 预览、素材库 `3d` 分类。

---

## 10. 前端设计

### 10.1 API 设置页

修改 `static/api-settings.html` / `static/js/api-settings.js` / `static/js/i18n/api-settings.js`：

- 协议下拉新增 `<option value="lovart">Lovart</option>`；协议白名单与 `FIXED_PROTOCOL_PROVIDER_IDS` 加 `lovart`。
- 新增 Lovart Key 面板：Access Key / Secret Key / Base URL。
- **新增计费模式开关（决策 #2）**：免费 / 付费单选，调 `GET/POST /api/lovart/mode`；默认免费模式（`unlimited=true`）；旁注当前 credits（决策 #6）。

### 10.2 智能画布

- 图片：`runApiGeneration()` 继续用 `/api/canvas-image-tasks`；当任务返回 `pending_confirmation` 时显示确认弹窗，确认后调用 `/api/lovart/confirm` 并继续轮询。
- 视频：`runApiVideoGeneration()` 仅在 `videoProvider === "lovart"` 时提交 `/api/canvas-video-tasks` 并**轮询**；其它视频 provider 继续走 `/api/canvas-video`。
- **credits 可见（决策 #6，修正版）**：模型下拉展示成本标签；确认弹窗展示 `pending_confirmation.estimated_cost` 或 §5 实测成本；设置页/侧栏显示**账户余额**（若 `mode/query` 返回）。不做硬性封顶。
- 第一阶段不新增 Lovart 专属大 UI，避免破坏布局。

#### 10.2.1 Lovart 的 UI 形态结论（✅ 由 §1.7 能力边界推导）

因为 Lovart **没有结构化参数**（无尺寸/步数/CFG/seed/质量字段，§1.7.3），给它套用现有"参数面板"会出现一堆**点了不生效**的控件，误导用户。结论：

- **复用现有的 provider/模型下拉骨架**（前端按 `api_providers` 自动渲染即可，零改动），但当选中 provider 为 `lovart` 时：
  - **隐藏/置灰所有结构化参数控件**（尺寸滑块、steps、seed、CFG、quality 枚举等）——它们对 Lovart 无效。
  - 保留并强化三样真正有效的输入：**prompt（自然语言）+ 模型选择（硬约束）+ 参考图（attachments）**。
  - 把"尺寸/质量"降级为**可选文字提示**（写进 prompt，§7.3 / 决策 #5），并在旁标注"对 Lovart 仅为参考，不保证精确"。
- 不为 Lovart 单独做一套大改版 UI；用"**同一套骨架 + 按 provider 收敛控件**"的方式，既不破坏现有布局，又不给用户假控件。

### 10.3 普通画布

Provider 下拉显示 Lovart；图片节点提交 `/api/canvas-image-tasks`；视频节点仅在选择 Lovart provider 时提交 `/api/canvas-video-tasks`，其它 provider 继续提交 `/api/canvas-video`。节点保存结构不新增必填字段。若有硬编码 provider 列表，补 `lovart`，但不改既有默认值。

---

## 11. 内部接口清单

### 11.1 复用现有

| 接口 | 是否改路径 | Lovart 用法 |
| --- | --- | --- |
| `GET /api/providers` | 不改 | 返回 lovart provider 与 key 状态 |
| `PUT /api/providers` | 不改路径，增加 lovart 字段 | 保存 lovart provider 与 AK/SK |
| `POST /api/providers/test-connection` | 不改 | lovart → 走 `mode/query` 验证 |
| `POST /api/providers/fetch-models` | 不改 | lovart → 内置快照 + `mode/query.unlimited_list` 免费标记 |
| `POST /api/canvas-image-tasks` + `GET .../{id}` | 不改 | 图片异步任务 |

### 11.2 第一阶段新增

| 接口 | 用途 |
| --- | --- |
| `POST /api/canvas-video-tasks` + `GET /api/canvas-video-tasks/{id}` | **视频异步任务（决策 #4）** |
| `GET /api/lovart/mode` / `POST /api/lovart/mode` | **计费模式查询/切换（决策 #2）** |
| `POST /api/lovart/confirm` | **第一阶段付费确认**：接收 `{task_id, thread_id}`，调 `/chat/confirm` 后继续 poll |

### 11.3 第二阶段新增

| 接口 | 用途 |
| --- | --- |
| `POST /api/lovart/audio` / `POST /api/lovart/3d` | 音频 / 3D |
| `GET /api/lovart/projects` / `GET /api/lovart/threads` | project / thread 管理 |

---

## 12. 外部地址与端口（✅ 已核对）

本地服务端口不变：`http://127.0.0.1:3000/`。Lovart：Base `https://lgw.lovart.ai`，前缀 `/v1/openapi`。实际请求见 §1.5.3。**前端不写这些地址。**

---

## 13. 请求签名（✅ 已核对源码，照搬即可）

见 §1.5.1。要点重申，避免踩坑：

- 签名串 `"{METHOD}\n{PATH}\n{TS}"`，`TS` 是**秒**、签名 **hex**、`PATH` **不含 query**。
- 必带 `X-Access-Key/X-Timestamp/X-Signature/X-Signed-Method/X-Signed-Path` + `Content-Type` + 非空 `User-Agent`；通用 JSON POST 还要 `Idempotency-Key`。`/file/upload` 是 multipart 特殊路径，按官方 `upload_file()` 逻辑照搬。
- 每次重试重新签名（时间戳新鲜）。
- **直接移植 `agent_skill.py:_sign/_request`，不要自研**——任何一处（ts 单位、hex/base64、头大小写、是否含 query）漂移都会全挂。
- 业务层不拼签名头，统一走 `lovart_request()`。

---

## 14. 任务状态与错误处理（✅ 已按真实契约重写）

### 14.1 真实状态机

- `/chat/status` 仅 `running` / `done` / `abort`。
- **done-race**：首次 `done` 后 `sleep 5s` 复查；视频等子 Agent 可能还没起。
- **pending_confirmation 不是 status**，在 `/chat/result.pending_confirmation`；running 期间也可能出现（§1.5.7）。
- `timeout` 是客户端等待超时的本地结果。
- **done 无产物**：判失败，展示 `agent_message`/`warning`（§1.5.9）。

### 14.2 处理映射

| 情况 | 处理 |
| --- | --- |
| `done` 且有产物 | 遍历多产物，带 CDN 头下载到 `/output`，任务 succeeded |
| `done` 5s 复查后子 Agent 仍在跑 | 继续轮询，别收工 |
| `done` 无产物 | 任务 failed，显示 `agent_message`（内容审核/超时/没调工具） |
| `pending_confirmation`（result 字段） | **第一阶段**：任务标记为 `pending_confirmation`，保存 `task_id/thread_id/estimated_cost/balance/raw`，前端弹窗展示预计 credits；用户确认后 `POST /api/lovart/confirm`，后端 `/chat/confirm` 后继续 poll。用户取消则任务 failed/cancelled，不扣费 |
| `abort` | failed，显示原因 |
| `timeout`（客户端） | 任务保持 running 或可恢复提示；用持久化的 thread_id 稍后 `result` 续查（§15.3） |
| 402/2012 | 直接展示 message（余额/风控等，决策 #6 不封顶但要提示） |
| 409/2011 | thread 忙；第一阶段每次新建 thread 基本不会撞，撞了就提示稍候 |
| 429/1429 | 退避重试 ~60s；前端提示"操作过快"；注意写操作 60/分上限（§1.5.8） |
| 401 | 提示检查 AK/SK |

---

## 15. 数据保存

### 15.1 Provider 配置

`data/api_providers.json` 存非密钥配置（id/name/base_url/protocol/enabled/primary/image_models/video_models）。

### 15.2 密钥

`API/.env` 存 `LOVART_ACCESS_KEY` / `LOVART_SECRET_KEY`。

### 15.3 任务与恢复状态（✅ 新增，针对内存任务表会丢的问题）

- 图片历史继续写 `history.json`（`type:"online", provider_id:"lovart", model, images:[...]`）。
- **新增 `data/lovart_state.json`**：第一阶段必须存默认 `project_id`，以及"未完成任务 → thread_id / 本地 task_id / kind / model / mode / estimated_cost"映射，便于人工排查与后续恢复。**第一阶段不把服务重启自动续查作为硬验收**；完整重启恢复放入阶段 1.5/第二阶段。
- 视频节点至少要能保存最终 `/output/lovart_xxx.mp4`。

---

## 16. 目标模式开发计划（从开发到测试）

本计划按"先后端契约、再 Provider 配置、再图片、再 Lovart-only 视频、最后前端和回归"执行。第一阶段目标是可完整使用 Lovart 免费/付费图片与视频模型，付费模型必须有确认弹窗，默认免费模式。

### M0：契约探针与样例固化

1. 用官方 `agent_skill.py` 跑 `query-mode`，保存返回样例，确认 `unlimited_list`、余额字段、当前模式字段的真实 key。
2. 分别探测 1 个免费图片、1 个免确认图片、1 个付费图片、1 个免费视频、1 个付费视频，记录 `pending_confirmation` 的真实字段名和 `estimated_cost`。
3. 验证 `/file/upload` multipart、CDN 下载 UA/Referer、done-race、done 无产物、timeout 的真实表现。

验收：形成一份本地探针日志或测试记录；§5 成本表与真实 `pending_confirmation` 字段一致。

### M1：Lovart 服务模块与状态文件

1. 新增 `services/lovart_service.py`，移植 `agent_skill.py` 的签名、请求、上传、send/status/result/poll/confirm、产物提取和 CDN 下载逻辑。
2. 新增 Lovart 提交锁：包住 `set_mode → send`，避免账号级计费模式被并发任务互相切换。
3. 新增 `data/lovart_state.json`：存 `project_id`、未完成任务映射、`thread_id`、本地 `task_id`、`kind`、`model`、`billing_mode`、`estimated_cost`。
4. 第一阶段只保证状态落盘和人工可查；服务重启自动续查不作为硬验收。

验收：单元/脚本级调用可完成 `mode/query`、`ensure_project`、`send`、`poll`、`confirm`、artifact download。

### M2：Provider 与设置页后端

1. `SUPPORTED_PROVIDER_PROTOCOLS`、`default_api_providers()`、`normalize_provider()`、固定协议白名单加入 `lovart`。
2. `public_provider()` 返回 Lovart AK/SK mask 状态；`ApiProviderPayload` 支持 Lovart AK/SK 保存/清除。
3. `PUT /api/providers` 保存 Lovart 密钥到 `API/.env`，不写入 `data/api_providers.json`。
4. `POST /api/providers/test-connection` 对 Lovart 走 `mode/query`。
5. `POST /api/providers/fetch-models` 对 Lovart 返回 §5.9 模型快照 + 成本元数据 + `unlimited_list` 免费标记。
6. 新增 `GET/POST /api/lovart/mode`，默认初始化为免费模式 `unlimited=true`。

验收：API 设置页能保存 AK/SK、验证连接、拉到 Lovart 模型、显示免费/付费/待确认成本标签和当前模式。

### M3：图片生成与付费确认

1. `generate_ai_image()` 增加 Lovart 分支，参考图先 `/file/upload`，模型进 `include_tools`，尺寸/质量拼进 prompt。
2. `build_online_image_result()` 支持 Lovart 多产物：全部下载进 `/output`，全部写入 `history.json` 和前端结果，不只取第一张。
3. `/api/canvas-image-tasks/{id}` 支持 `pending_confirmation` 状态，返回 `task_id/thread_id/estimated_cost/message`。
4. `POST /api/lovart/confirm` 支持图片任务：确认后继续 poll，完成后更新原任务为 `succeeded`。

验收：免费图片直接出图；付费图片弹窗展示 14/50 credits 或接口返回成本，确认后出图，取消不扣费且任务结束。

### M4：Lovart-only 视频异步

1. 新增 `POST /api/canvas-video-tasks` 和 `GET /api/canvas-video-tasks/{id}`，仅 Lovart 视频使用。
2. 其它视频 provider 保持现有 `/api/canvas-video`，不改行为。
3. 首帧/尾帧/参考视频/音频等输入上传为 attachments；角色信息拼进 prompt。
4. 视频任务支持 `pending_confirmation`、timeout、abort、done 无产物、多产物下载和 CDN 头。
5. `POST /api/lovart/confirm` 支持视频任务：确认后继续 poll，完成后更新原任务为 `succeeded`。

验收：免费视频可排队并最终回填；付费视频弹窗展示 10/14 credits 或接口返回成本，确认后生成 `/output/lovart_*.mp4`；非 Lovart 视频 provider 不受影响。

### M5：前端设置页与模型选择体验

1. `static/api-settings.html/js/i18n` 增加 Lovart 协议、AK/SK 面板、免费/付费模式开关、余额/credits 展示。
2. 智能画布和普通画布模型下拉展示 Lovart 模型分组与成本标签：`免费`、`免确认`、`10 credits`、`14 credits`、`50 credits`、`待确认`。
3. Lovart provider 下隐藏/置灰无效结构化参数，保留 prompt、模型、参考图和免费/付费模式。
4. 模型选择阶段允许用户选择免费模式或付费模式；默认免费模式。

验收：用户不需要去设置页才能理解成本；生成前能看出模型是否免费/付费/待确认。

### M6：前端任务轮询与确认弹窗

1. 智能画布图片任务沿用现有轮询，识别 `pending_confirmation` 后弹窗确认。
2. 智能画布视频仅 Lovart 分支走 `/api/canvas-video-tasks` 轮询；其它 provider 保持同步接口。
3. 普通画布同样只在 Lovart 视频节点走 `/api/canvas-video-tasks`。
4. 确认弹窗展示模型名、模式、预计 credits、当前余额（有则显示）、取消/确认按钮。
5. 确认后调用 `/api/lovart/confirm`，继续等待原任务完成；完成结果进入节点和素材/历史。

验收：图片/视频付费任务都有完整确认闭环；刷新画布后结果仍在；错误不会留下空白节点。

### M7：回归与端到端测试

1. 后端静态检查：`python3 -m py_compile main.py services/lovart_service.py`。
2. 启动服务：`python3 main.py`，确认 `http://127.0.0.1:3000/` 可访问。
3. API 级测试：providers 保存/读取、test-connection、fetch-models、mode get/set、图片任务、视频任务、confirm。
4. 浏览器测试：API 设置页、智能画布、普通画布分别跑免费图片、付费图片、免费视频、付费视频。
5. 回归测试：OpenAI/APIMart/Gemini/RunningHub/火山/即梦/Codex/ModelScope 旧链路至少各做一次不破坏验证；非 Lovart 视频仍走 `/api/canvas-video`。
6. 失败测试：未配置 AK/SK、AK/SK 错误、用户取消付费确认、done 无产物、429、402、timeout、服务重启后本地任务 404 的提示。

验收：所有第一阶段场景通过；失败场景有明确提示；旧 provider 无行为回归。

### M8：文档与交付记录

1. 在本文档追加最终实现差异、已跑测试命令、测试结果、未完成项。
2. 若因 Lovart 平台返回字段与 §5 不一致，更新 §5 成本表和状态字段。
3. 第二阶段再做：音频、3D、project/thread 管理、服务重启自动续查、reasoning 模式 UI。

#### 2026-06-13 实施交付记录

**实现范围**

1. 新增 `services/lovart_service.py`：按 Lovart OpenAPI 官方签名方式封装 AK/SK HMAC 请求、project/thread 状态、`mode/query`、`mode/set`、`chat/send`、`chat/confirm`、轮询、附件上传与产物下载。
2. `main.py` 新增 Lovart provider、AK/SK 环境变量、模型元数据、`/api/lovart/mode`、`/api/lovart/confirm`、图片任务 Lovart 分支、Lovart-only `/api/canvas-video-tasks` 异步视频任务。
3. `static/api-settings.html`、`static/js/api-settings.js`、`static/css/api-settings.css` 新增 Lovart AK/SK、连通性验证、模型快照、免费/付费模式、模型成本标签。
4. `static/js/canvas.js`、`static/css/canvas.css` 新增普通画布图片/视频节点的 Lovart 免费/付费切换，默认免费；提交 Lovart 任务时携带 `unlimited`；轮询 `pending_confirmation` 时弹窗展示预计积分并调用 `/api/lovart/confirm`。
5. `static/js/smart-canvas.js`、`static/css/smart-canvas.css` 新增智能画布图片/视频入口的 Lovart 免费/付费切换，默认免费；Lovart 视频改走异步任务接口并支持二次确认。
6. `API/.env` 已写入 Lovart AK/SK、`LOVART_BASE_URL=https://lgw.lovart.ai`、`LOVART_REASONING_MODE=fast`。

**已跑验证**

```bash
python3 -m py_compile main.py services/lovart_service.py
node --check static/js/api-settings.js
node --check static/js/canvas.js
node --check static/js/smart-canvas.js
CANVAS_PORT=3001 CANVAS_HOST=127.0.0.1 .venv/bin/python main.py
```

接口验证结果：

1. `GET /api/providers`：Lovart 存在且启用，`protocol=lovart`，AK/SK 均已配置，图片模型 17 个、视频模型 13 个、模型元数据 30 条。
2. `POST /api/providers/test-connection`：返回 `ok=true`，Lovart AK/SK 验证通过，当前免费模式，模型总数 30。
3. `POST /api/providers/fetch-models`：返回 Lovart 图片/视频模型快照与 30 条模型元数据。
4. `GET /api/lovart/mode`、`POST /api/lovart/mode {"unlimited":true}`：均成功，读回 `unlimited=true`。
5. 静态资源访问：`/static/api-settings.html`、`/static/canvas.html`、`/static/smart-canvas.html`、三份 JS、两份 CSS 均返回 200。
6. 负路径：`POST /api/lovart/confirm {}` 返回 400 `缺少 task_id 或 thread_id`；Lovart 走旧 `/api/canvas-video` 返回 400 并提示使用 `/api/canvas-video-tasks`。

**未做的验证**

1. 未主动提交真实付费任务、未点击 Lovart 付费确认，以避免实际扣除积分。
2. 未主动跑真实图片/视频生成任务，以避免制造不可撤销的 Lovart 队列任务；当前验证覆盖到 AK/SK、mode、模型、任务接口分流、确认负路径和前端加载。
3. in-app Browser 打开本地 URL 两次返回 `Cannot navigate to invalid URL`，已用 Python HTTP 请求验证静态页面和资源 200。

---

## 17. 回归测试清单

### 17.1 不能破坏的旧功能

OpenAI 生图、APIMart 异步生图/视频、Gemini、RunningHub、火山、即梦、Codex、ModelScope 默认强制保留、老画布 JSON 打开、非 lovart provider 选择执行——逐项验证不受影响。

### 17.2 Lovart 新功能

| 场景 | 预期 |
| --- | --- |
| 未配 AK/SK | 提示缺少 Lovart AK/SK |
| AK/SK 错误 | 验证失败（401），提示鉴权错误 |
| 文生图 | `/output/lovart_*.png`（多图全部入库） |
| 图生图 | 参考图先上传 CDN 再返回 |
| 文生视频/图生视频 | 异步任务，`/output/lovart_*.mp4`；done-race 不丢成片 |
| 硬约束模型调用失败 | 明确报错，不静默替换（决策 #1） |
| 高成本任务 | 第一阶段显示预计 credits，用户确认后继续生成；用户取消不扣费 |
| done 无产物 | 失败 + 显示 agent_message，不生成空节点 |
| 限流 429 | 退避重试 / 友好提示 |
| 计费模式切换 | fast/unlimited 切换生效，`mode/query` 可读回（决策 #2） |
| 服务重启 | 第一阶段只要求 `data/lovart_state.json` 留下 thread_id 记录；自动续查不作为硬验收 |

---

## 18. 风险和取舍

1. **Lovart 是 Agent 不是纯模型 API**：即便 `include_tools` 硬约束，仍可能内容审核拒绝、需 credits 确认、或回文字不产物。后端必须校验 `generation_succeeded`/artifacts。
2. **尺寸/质量不一定严格生效**：无结构化字段，拼 prompt 只是建议（决策 #5）。画布是按确定比例拖拽的产品，这是真实 UX 落差，需告知用户"尺寸为参考"。
3. **视频耗时**：已用异步任务化解（决策 #4）；同步 `/api/canvas-video` 不再承载 lovart。
4. **计费模式是账号级全局状态**：即使单机单 AK/SK，也要用 Lovart 提交锁包住 `set_mode → send`，否则并发免费/付费任务会互相切模式；若将来多用户共用一把 AK/SK，需每用户独立密钥或更严格队列。
5. **reasoning mode 锁 thread + 同 thread 不并发（409）**：第一阶段每次新建 thread 规避；若做多轮编辑续 thread，需排队串行。
6. **写操作限流 60/分**：批量生成需前端限速 + 后端退避，否则 429。
7. **内存任务表丢失**：第一阶段只落盘 `data/lovart_state.json` 供排查和后续恢复，不承诺服务重启自动续查。
8. **音频/3D 需新 UI 与输出类型**，不应强塞进图片/视频节点（第二阶段）。

---

## 19. 推荐最终方案

第一阶段：

```text
Lovart 作为独立 provider（协议 lovart）
  -> 默认免费模式；用户可在模型选择阶段切付费模式
  -> 图片：复用现有异步图片任务，include_tools 硬约束
  -> 视频：仅 Lovart 新增异步视频任务；其它 provider 不动
  -> project 自动新建并落盘；每次生成新建 thread
  -> API 设置页：AK/SK + 免费/付费模式开关 + credits 可见
  -> 付费模型：pending_confirmation 弹窗确认 + /api/lovart/confirm
  -> 产物多份全部下载到 /output（带 CDN 头）
  -> 状态/错误：done-race、pending_confirmation(result字段)、done无产物、402/409/429 全覆盖
```

第二阶段：

```text
Lovart 专属能力面板
  -> reasoning fast/thinking（注意锁 thread）
  -> 音频 / 3D 输出（新 UI）
  -> project/thread 管理
  -> 服务重启自动续查未完成 thread
  -> reasoning 模式 UI
```

风险集中在新增 `lovart` 分支内，旧 provider 不受影响；所有对外契约均以移植自 `agent_skill.py` 的服务模块为单一事实来源。
