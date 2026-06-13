# 安全与 Bug 审查报告 — daxiong-Canvas

审查日期：2026-06-13
审查范围：后端 `main.py`（约 14,000 行 FastAPI 服务）、前端 `static/js/*`、启动脚本、更新机制。
原则：**只报告，不改码**。所有结论附文件路径与行号，按严重程度分级。

> 说明：这是一个本地优先的 AI 画布工具，默认在用户自己机器上运行。下面很多"漏洞"在**纯本机 + 受信任内网**场景下风险较低，但只要这台机器接入了不可信网络（公共 Wi-Fi、办公室局域网、被打洞/端口转发），就会从"理论问题"变成"可被远程接管"。请结合你的实际部署环境判断优先级。

---

## 总览

| 级别 | 数量 | 概述 |
|---|---|---|
| 致命 (Critical) | 1 | 服务监听 `0.0.0.0` 且零鉴权 + 可远程改写 `main.py` 的更新接口 → 局域网内可远程代码执行 |
| 高 (High) | 4 | CORS 全开、SSRF、任意本地文件读取面、前端存储型 DOM XSS |
| 中 (Medium) | 5 | 更新源信任、zip 解析、子进程超时/僵尸、异常吞没、上传类型校验 |
| 低 (Low) | 4 | 日志泄露、错误信息回显、魔法数字、186 处宽泛 except |

---

## 致命

### C-1　零鉴权服务暴露在所有网卡上，叠加可写 `main.py` 的更新接口
- 监听地址：`main.py:14089` → `uvicorn.run(app, host="0.0.0.0", port=3000)`
- 全程无任何鉴权层：搜索 `Depends`/`Authorization` 校验，所有 `/api/*` 业务接口都没有调用方身份校验。
- 更新机制允许写入 `main.py`：`main.py:1762` `update_allowed_file()` 显式放行 `main.py`、`VERSION` 和 `static/`；`download_*_update_files()`（`main.py:1819` 起）会把远端内容落地并覆盖本地文件。

**风险链条**：`0.0.0.0` 意味着同一局域网内**任何人**都能访问 `http://<你的IP>:3000`。由于没有鉴权，攻击者可直接调用触发"一键更新"的接口，让你的进程从远端拉取并覆盖 `main.py`，下次重启即执行攻击者代码——等价于局域网内的远程代码执行（RCE）。即便不走更新，攻击者也能直接调用生图/子进程/文件接口消耗你的 API 额度、读取本地文件。

**建议**：默认绑定 `127.0.0.1`；确需局域网访问时，加一层本地 token（启动时随机生成、写在终端里）并对所有 `/api` 接口做校验；更新接口必须二次确认 + 来源签名校验（见 M-1）。

---

## 高

### H-1　CORS 允许任意来源
- `main.py:71-75`：`allow_origins=["*"]` + `allow_methods=["*"]` + `allow_headers=["*"]`。
- 与 C-1 叠加：任何网页（你浏览任意网站时）都能用你的浏览器向 `http://127.0.0.1:3000` 发跨域请求，操作你的画布、触发生成、读取已配置的服务端能力。这是典型的"DNS rebinding / 本地服务被任意站点驱动"攻击面。
- **建议**：白名单具体来源（`http://127.0.0.1:3000`），或对写操作要求自定义头 + 校验 `Host`。注意：部分本地导入接口已用 `ensure_same_origin_request`（`main.py:4620`），但绝大多数业务接口没有。

### H-2　SSRF：`fetch_remote_media_bytes` 无内网/回环地址防护
- `main.py:4595-4612`：只校验 scheme 是 http/https，对目标 IP 不做限制。被 `/api/download-output`（`main.py:8078`）等接口以用户提供的 `url` 调用。
- 攻击者（结合 C-1/H-1）可让服务去请求 `http://169.254.169.254/...`（云元数据）、`http://127.0.0.1:<其他端口>`、内网管理后台，并把响应回传——把你的机器当跳板探测内网。
- **建议**：解析目标 IP，拒绝回环、私有网段（10/172.16/192.168）、链路本地 `169.254`、以及解析后重定向到内网的情况。

### H-3　本地任意文件读取面：`normalize_local_image_path`
- `main.py:4631` 起：接受 `file://` 或裸路径并最终读取本机文件。虽然入口处用 `ensure_same_origin_request` 限制了来源（`main.py:8429` 等），但 H-1 的 CORS 全开 + 同源判断依赖可伪造的 `Host`/`Origin` 头，在非浏览器攻击者面前形同虚设。
- 一旦绕过，可读取任意路径图片（乃至探测文件是否存在）。
- **建议**：限制可读根目录（白名单目录），对解析后的绝对路径做 `commonpath` 围栏（参考 `shared_child_abs` 的正确写法，`main.py:5212`）。

### H-4　前端存储型 DOM XSS：节点标题未转义直插 innerHTML
- `static/js/canvas.js:6053`：
  ```
  el.innerHTML = `<div class="node-head"><span class="node-title">${displayTitle}</span>...`;
  ```
  `displayTitle` 来源于 `node.title`（源文本/便签/AI 文本等用户可编辑字段）或文件名，**未经过 `escapeHtml`**。同文件其它位置都规范地用了 `escapeHtml/escapeAttr`，此处是遗漏。
- 画布数据以 JSON 文件保存且可被分享/导入（`data/canvases/*.json`）。一个标题为 `<img src=x onerror=fetch('/api/...')>` 的节点，在任何人打开该画布时即执行脚本——可调用上述无鉴权接口，危害被放大。
- 全项目 `innerHTML` 赋值：`canvas.js` 88 处、`smart-canvas.js` 49 处、`api-settings.js` 37 处，建议整体排查同类遗漏。
- **建议**：`displayTitle` 包一层 `escapeHtml`；对所有把 `node.title`/文件名/远端返回文本拼进 `innerHTML` 的位置统一转义，或改用 `textContent`。

---

## 中

### M-1　更新源仅靠 HTTPS，无内容签名校验
- `main.py:1819` `download_github_update_files` / `download_modelscope_update_files`：从固定 GitHub/ModelScope 仓库拉取并覆盖 `main.py`。路径围栏写得对（`commonpath` 检查），但**内容本身没有签名/哈希校验**。若上游仓库被攻陷、或 DNS/中间人被劫持（配合代理设置 `getproxies()`），即可推送恶意 `main.py`。
- **建议**：对更新包做发布者签名校验或固定 commit/哈希校验；更新前向用户展示 diff 并要求确认。

### M-2　zip 读取未做 zip-bomb / 路径校验
- `main.py:5619`、`11663`：`zipfile.ZipFile(...)` 读取上传/远端 zip。当前是读取条目而非 `extractall`，路径穿越风险低，但未限制解压后总大小/条目数，存在 zip bomb 资源耗尽风险。
- **建议**：限制条目数与累计解压字节；对任何写盘场景校验成员名不含 `..`/绝对路径。

### M-3　子进程超时与僵尸进程处理
- `main.py:11242` 起：`subprocess.Popen(...)` + `proc.wait(timeout=...)`。超时抛 `TimeoutExpired` 后，代码是否 `kill()` 并回收子进程需确认；多处子进程调用（`main.py:1931/3680/4526/5781/8999`）混用同步/异步，超时分支若不 `terminate` 会留下孤儿进程。命令本身用 list 形式传参（非 `shell=True`），**命令注入风险低**，这点是好的。
- **建议**：统一封装：超时 → `proc.kill()` + `proc.wait()`；记录退出码。

### M-4　大范围 `except Exception` 吞掉错误
- 全文 186 处 `except`（`grep -c` 结果），大量为 `except Exception: pass`/`continue`（如 `main.py:8064` 的后端轮询、`8101` 上传循环）。会掩盖真实故障、使排错困难，也可能让本应失败的流程"静默成功"。
- **建议**：缩小捕获范围，至少 `logging.exception` 记录；区分"可忽略"与"应中止"。

### M-5　上传类型校验依赖扩展名/Content-Type
- `main.py:8142` 起 `upload_ai_reference`：按扩展名/`content_type` 推断类型并落盘，文件名用 uuid 重写（**这点很好，避免了文件名穿越**），但内容未做真实类型校验（magic bytes）。`doc_exts` 放行 `.zip/.docx` 等，配合 M-2 有一定面。
- **建议**：对图片用 PIL 真正解码校验；对文档类限制大小并隔离存放。

---

## 低

### L-1　日志可能记录敏感 URL/参数
- 自定义日志过滤器（`main.py:50` 起 `QuietAccessLogFilter`）只是降噪，访问日志仍可能含带 token 的查询串。建议确保 API key 不出现在 URL（应放 Header，代码多数已用 `Authorization`，保持一致即可）。

### L-2　错误详情直接回显给客户端
- 如 `main.py:8088` `detail=f"远程文件下载失败：{exc}"` 等多处把异常字符串透传。可能泄露内部路径/依赖信息。建议生产环境返回通用文案，详情仅入日志。

### L-3　API key 在服务端 `.env` 明文存储
- `main.py:221` `API/.env`，明文。返回给前端时已做掩码（`main.py:669 mask_secret`、`1175 key_preview`），这点正确。明文落盘对本地工具可接受，但若机器多人共用需注意文件权限（`chmod 600`）。

### L-4　魔法数字与硬编码端口/限额
- 端口 `3000`、各处 `timeout`/`max_bytes`（如 `200*1024*1024`）散落硬编码，建议集中为配置常量，便于审计与调参。

---

## 做得好的地方（避免误伤）
- 路径围栏 `shared_child_abs`（`main.py:5212`）与 `output_file_from_url`（`main.py:4470`）用 `commonpath` 正确防穿越。
- 子进程统一用 list 传参，无 `shell=True`，无 `eval/exec/pickle`，命令注入面小。
- 上传文件名用 uuid 重写，前端大量位置已用 `escapeHtml/escapeAttr`。
- 返回前端的密钥已掩码。

---

## 建议处理顺序
1. **C-1**：绑定 `127.0.0.1` 或加本地 token 鉴权（一行改动即可消除最大风险）。
2. **H-1 / H-2 / H-3**：收紧 CORS、加 SSRF 围栏、限制本地读路径。
3. **H-4**：给 `displayTitle` 加转义，排查同类 innerHTML 遗漏。
4. **M-1**：更新接口加确认 + 内容校验。
5. 其余按上表逐条收口。

> 复核说明：以上行号基于本次审查时的 `main.py`（14,089 行）与 `static/js/canvas.js`（15,081 行）。C-1 的监听地址、H-1 的 CORS 配置、H-4 的未转义注入均已逐行核对确认；SSRF/本地读取的"可达性"取决于你的网络暴露面，已在文中标注前提条件。
