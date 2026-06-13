# taste-skill 使用指南：把成熟网站风格迁移到 daxiong-Canvas

这份文档面向第一次使用 Skills 的人。目标不是学会每个术语，而是能实际指挥 Codex：参考一个成熟网站的视觉语言，把当前项目的界面风格改得更统一、更高级，同时不破坏现有功能。

## 1. 先看结论：当前是全局还是项目级？

在本机当前状态里，`Leonxlnx/taste-skill` 分成两层：

| 范围 | 当前状态 | 说明 |
|---|---|---|
| 全局 Skills | 已安装一整套 taste-skill | 路径主要在 `/Users/ruoyu/.agents/skills/`。Codex 在任意项目里通常都能看到这些 skill。 |
| 当前项目 Skills | 只安装了 `brandkit` | 路径是 `./.agents/skills/brandkit/SKILL.md`，并记录在 `./skills-lock.json`。 |

也就是说：

- 你问的“这个 skills 是全局的，还是只是当前项目？”答案是：**完整 taste-skill 套件是全局的；当前项目只锁定安装了其中的 `brandkit`。**
- 如果你希望这个项目以后在别的机器、别的 agent、团队协作时也稳定复现，应把需要的 skill 安装到项目级。

## 2. 怎么查看安装状态？

在项目目录里执行：

```bash
cd /Users/ruoyu/Documents/GitHub/daxiong-Canvas
```

查看当前项目安装了哪些 skill：

```bash
npx skills list
```

你现在会看到类似：

```text
Project Skills
brandkit  ./.agents/skills/brandkit
```

查看全局安装了哪些 skill：

```bash
npx skills list -g
```

查看 `Leonxlnx/taste-skill` 仓库里一共有多少个 skill：

```bash
npx skills add Leonxlnx/taste-skill -l
```

这个命令只列出仓库里的 skill，不会安装。

## 3. 如果要把完整 taste-skill 装到当前项目

如果你希望这个项目完整使用 taste-skill，可以安装全部 skill 到项目级：

```bash
npx skills add Leonxlnx/taste-skill --all
```

如果只安装最常用的几个，建议：

```bash
npx skills add Leonxlnx/taste-skill --skill redesign-existing-projects design-taste-frontend image-to-code imagegen-frontend-web brandkit -y
```

推荐先装这 5 个：

| Skill | 这个项目里的用途 |
|---|---|
| `redesign-existing-projects` | 最适合改造当前项目。它会先读现有 HTML/CSS/JS，再做针对性升级，不建议推倒重写。 |
| `design-taste-frontend` | 用于建立整体风格规范，适合重新设计首页、工具页、设置页等。 |
| `imagegen-frontend-web` | 先生成视觉参考图，每个页面区域一张图，适合确定“长什么样”。 |
| `image-to-code` | 先看参考图，再把视觉落到代码里。 |
| `brandkit` | 生成品牌板、logo 风格、色彩和视觉世界观。当前项目已经项目级安装。 |

不建议一开始就用 `gpt-taste` 大规模改当前项目。它偏 Awwwards/GSAP 动效，很适合营销页，但当前项目是工具型 canvas 应用，过重的滚动动效可能影响可用性。

## 4. taste-skill 里有哪些功能？

`Leonxlnx/taste-skill` 一共包含 13 个 skill：

| Skill | 用一句话理解 |
|---|---|
| `brandkit` | 做品牌视觉板、logo 方向、品牌世界观。 |
| `design-taste-frontend` | 默认主力前端审美 skill，做 landing、portfolio、改版，避免模板味。 |
| `design-taste-frontend-v1` | 老版本兼容，一般不用。 |
| `redesign-existing-projects` | 改造现有项目，先审计再小步升级。 |
| `high-end-visual-design` | 高端 agency 质感规则，强调字体、间距、容器、动效。 |
| `gpt-taste` | 更激进的 GSAP/Awwwards 风格，适合展示型页面。 |
| `minimalist-ui` | 极简、编辑部、暖单色、扁平 bento 风格。 |
| `industrial-brutalist-ui` | 工业粗野、终端、蓝图、战术数据界面风格。 |
| `imagegen-frontend-web` | 为网站每个 section 生成独立设计参考图。 |
| `imagegen-frontend-mobile` | 为移动 App 生成多屏设计参考图，只出图。 |
| `image-to-code` | 先生成/分析视觉图，再实现成前端代码。 |
| `stitch-design-taste` | 为 Google Stitch 生成 `DESIGN.md` 设计规范。 |
| `full-output-enforcement` | 要求完整输出，禁止省略代码或只给骨架。 |

## 5. 小白怎么理解“迁移成熟网站风格”？

不要把它理解成“抄一个网站”。正确做法是提取风格 DNA，再换成我们自己的产品结构。

你要迁移的是这些东西：

- **布局节奏**：页面是紧凑工具型，还是大留白展示型？
- **颜色系统**：背景、主文字、弱文字、强调色、危险色、边框色怎么搭配？
- **字体气质**：偏工程、偏消费、偏编辑部、偏游戏、偏终端？
- **组件形状**：按钮是方的、圆角的、胶囊的，卡片是扁平还是有层次？
- **交互反馈**：hover、active、focus、loading、empty、error 状态怎么表现？
- **信息密度**：按钮、工具栏、面板、画布周围的信息是密还是松？

不要迁移这些东西：

- 不要复制别人的 logo、图片、商标、插画。
- 不要照抄文案。
- 不要把别人的页面结构一比一搬过来。
- 不要为了像某个网站而破坏当前项目的核心工作流。

## 6. 当前项目更适合参考什么类型的网站？

`daxiong-Canvas` 是一个工具型无限画布项目，不是普通品牌官网。优先参考成熟的“创作工具”和“专业工作台”，而不是普通 landing page。

可参考的成熟风格方向：

| 参考类型 | 适合迁移的部分 | 不适合照搬的部分 |
|---|---|---|
| Figma / FigJam | 工具栏、属性面板、画布边缘 UI、轻量图标、悬浮面板 | Figma 的复杂多人协作逻辑 |
| Linear | 克制配色、清晰层级、命令式交互、低噪音界面 | 过强的 issue 管理信息结构 |
| Notion | 柔和背景、块状内容、轻量编辑体验 | 文档编辑范式不适合完全套到画布 |
| Excalidraw | 画布工具栏、轻松创作感、低门槛图形操作 | 手绘风格不一定适合 AI 图像工作流 |
| Runway / Krea | AI 创作工具质感、媒体预览、生成任务状态 | 大量营销视觉和重图片背景 |
| Raycast | 命令面板、快捷操作、深色高效率界面 | 桌面启动器结构 |
| Vercel / shadcn/ui | 干净的组件层级、表单、设置页、文档质感 | 营销页 hero 不应直接套进工具页 |

推荐先选一个主参考，不要同时说“像 Figma、Linear、Notion、Runway”。混太多会导致风格不统一。

## 7. 推荐迁移流程

### 第一步：选一个成熟网站作为主参考

你可以这样告诉 Codex：

```text
使用 redesign-existing-projects skill。请先只读审计，不要改代码。
我想把当前项目的视觉方向调整为“Figma + Linear 风格”：
- Figma：参考画布工具栏、悬浮面板、属性面板
- Linear：参考深浅色、字体层级、按钮和状态反馈

请先扫描 static/canvas.html、static/css/canvas.css、static/css/theme.css、static/js/canvas.js，
输出：
1. 当前 UI 的主要问题
2. 哪些地方适合迁移参考风格
3. 哪些地方不能动，因为可能影响功能
4. 第一阶段最小改造方案
```

这一步只做审计，不改代码。适合避免一上来就改坏。

### 第二步：让 Codex 提取风格 DNA

如果你有参考网站截图或 URL，可以这样说：

```text
使用 design-taste-frontend skill。请把这个参考网站的风格拆成设计 DNA，
不要复制品牌资产，只提取可迁移的 UI 规则：
- 配色
- 字体
- 圆角
- 边框和阴影
- 工具栏
- 面板
- 按钮状态
- 空状态/错误状态/loading 状态

然后把它转换成 daxiong-Canvas 可以使用的设计规则。
```

如果是具体网站，最好提供截图。只给网站名字也可以，但截图更稳。

### 第三步：先生成一个“目标风格说明”

建议先让 Codex 写一个项目内设计规范，例如：

```text
请新建 docs/ui-style-guide.md，
把“Figma + Linear 风格迁移到 daxiong-Canvas”的规则写清楚。
必须包含：
1. 设计目标
2. 色彩变量
3. 字体层级
4. 按钮规则
5. 工具栏规则
6. 面板规则
7. canvas 页面改造优先级
8. 禁止事项
```

有了这个文档，后面改代码就不容易跑偏。

### 第四步：只改一个页面，不要全项目一起改

当前项目的前端主要在 `static/` 下：

| 文件 | 作用 |
|---|---|
| `static/canvas.html` | 主画布页面结构 |
| `static/css/canvas.css` | 主画布页面样式 |
| `static/css/theme.css` | 全局主题变量和共用样式 |
| `static/js/canvas.js` | 主画布交互逻辑 |
| `static/index.html` | 入口页 |
| `static/api-settings.html` / `static/css/api-settings.css` | API 设置页 |
| `static/asset-manager.html` / `static/css/asset-manager.css` | 素材管理页 |
| `static/comfyui-settings.html` / `static/css/comfyui-settings.css` | ComfyUI 设置页 |

第一阶段建议只改：

```text
static/canvas.html
static/css/canvas.css
static/css/theme.css
```

不要先动 `static/js/canvas.js`，除非只是补充 class 或无风险的状态标记。画布交互逻辑通常风险更高。

### 第五步：让 Codex 小步实现

可直接复制这个提示词：

```text
使用 redesign-existing-projects skill。
请按 docs/ui-style-guide.md 改造主画布页面，第一阶段只做视觉升级：
- 保留现有功能和 DOM id，不删除已有按钮和交互入口
- 优先修改 static/css/theme.css 和 static/css/canvas.css
- 只有必要时才微调 static/canvas.html 的 class/结构
- 暂时不要重写 static/js/canvas.js

目标风格：Figma 的画布工具感 + Linear 的克制深色/浅色质感。
请改完后启动本地服务，并用浏览器检查主页面。
```

## 8. 三种适合本项目的风格方案

### 方案 A：Figma + Linear，高效专业工具风

适合大多数用户。推荐优先做这个。

特征：

- 背景是低噪音浅灰或深灰，不抢画布内容。
- 工具栏轻、窄、悬浮，按钮有明确 hover/active。
- 属性面板分组清楚，标题小，控件紧凑。
- 强调色少，只用于当前工具、运行状态、危险操作。

建议使用：

```text
redesign-existing-projects + design-taste-frontend
```

### 方案 B：Runway + Krea，AI 创作媒体工具风

适合强调 AI 生图、生视频、媒体资产管理。

特征：

- 更强的媒体预览区域。
- 面板更像创作控制台。
- 任务状态、模型选择、生成参数更有层级。
- 可以有轻微玻璃感，但不能影响性能。

建议使用：

```text
design-taste-frontend + imagegen-frontend-web + image-to-code
```

### 方案 C：Industrial Brutalist，专业控制台/实验室风

适合想做出“硬核、机械、工程、数据密度高”的差异化。

特征：

- 深色终端感或工业印刷感。
- 明确网格线、坐标、编号、状态灯。
- 数据面板非常清晰。
- 适合高级用户，但新手可能觉得冷。

建议使用：

```text
industrial-brutalist-ui + redesign-existing-projects
```

## 9. 推荐你实际怎么下命令

### 如果只想在当前对话里使用全局 skill

直接点名即可：

```text
使用 redesign-existing-projects skill，帮我审计当前项目 UI，不要改代码。
```

全局 skill 已经存在，Codex 会优先读取它。

### 如果想让这个项目长期固定使用这些 skill

安装到项目级：

```bash
npx skills add Leonxlnx/taste-skill --skill redesign-existing-projects design-taste-frontend image-to-code imagegen-frontend-web brandkit -y
```

安装后检查：

```bash
npx skills list
```

你应该能看到这些 skill 的路径在：

```text
/Users/ruoyu/Documents/GitHub/daxiong-Canvas/.agents/skills/...
```

这才是项目级安装。

## 10. 给 Codex 的标准提示词模板

### 模板 1：只审计，不改代码

```text
使用 redesign-existing-projects skill。
请审计 daxiong-Canvas 当前前端，不要改代码。

目标：把界面风格迁移到“Figma + Linear 的专业创作工具风”。

请检查：
- static/canvas.html
- static/css/canvas.css
- static/css/theme.css
- static/index.html
- 相关设置页 CSS

输出：
1. 当前视觉问题
2. 成熟网站风格可迁移的规则
3. 不能动或高风险区域
4. 第一阶段改造清单
5. 需要我确认的产品决策
```

### 模板 2：生成风格规范

```text
使用 design-taste-frontend skill。
请为 daxiong-Canvas 写一份 docs/ui-style-guide.md。

参考风格：
- Figma：画布工具栏、属性面板、轻量图标按钮
- Linear：克制配色、字体层级、hover/active/focus 状态

要求：
- 不复制任何品牌资产
- 只提取设计规则
- 适配当前 static HTML/CSS/JS 项目
- 给出 CSS 变量建议
- 给出每个页面的改造优先级
```

### 模板 3：开始第一阶段改造

```text
使用 redesign-existing-projects skill。
请按 docs/ui-style-guide.md 执行第一阶段视觉改造。

范围：
- 主要改 static/css/theme.css
- 主要改 static/css/canvas.css
- 必要时小改 static/canvas.html

约束：
- 不删除现有 DOM id
- 不破坏 canvas 操作
- 不重写 static/js/canvas.js
- 每次改完运行本地页面验证
- 最后说明改了什么、怎么验证、还有哪些风险
```

### 模板 4：用截图或网站做参考

```text
使用 design-taste-frontend + redesign-existing-projects skill。
我会给你一个成熟网站截图。请不要照抄，只提取风格 DNA，
并迁移到 daxiong-Canvas 的主画布页面。

请先输出设计拆解：
- 颜色
- 字体
- 间距
- 圆角
- 面板层级
- 工具栏
- 按钮状态
- 哪些规则适合 daxiong-Canvas
- 哪些规则不适合

等我确认后再改代码。
```

## 11. 改造时的安全原则

这个项目不是纯展示网页，不能只追求好看。

必须遵守：

- 先审计，再改代码。
- 先改一个页面，再推广到其他页面。
- 优先改 CSS，少动 JS。
- 保留所有已有 `id`、事件入口、按钮功能。
- 不要一次性引入大型前端框架。
- 不要把静态 HTML 项目强行改成 React/Next。
- 不要为了动画牺牲画布性能。
- 每次改完都要本地打开页面检查。

## 12. 一句话记忆

如果你想“换风格但不改坏功能”，最稳的组合是：

```text
redesign-existing-projects 负责安全改造
design-taste-frontend 负责审美方向
brandkit 负责品牌视觉
imagegen-frontend-web / image-to-code 负责先出图再落地
```

对这个项目，第一阶段建议这样说：

```text
使用 redesign-existing-projects skill。先审计主画布页面，不要改代码。
目标是迁移 Figma + Linear 的成熟工具型产品风格。
```
