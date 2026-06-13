# daxiong-Canvas UI 风格优化开发文档

目标：在**不影响现有框架和功能**的前提下，把当前项目优化为“Figma 式画布工作台 + Linear 式冷静质感 + Runway/Krea 式 AI 创作面板”的专业工具型应用。

参考图路径：

```text
/Users/ruoyu/.codex/generated_images/019ebcf7-2069-7633-a886-d89318e4a293/ig_0dc111686c6c0c4b016a2c4bcc09e88191812ea3276cf08af2.png
```

## 1. 设计方向

当前项目不是官网，也不是展示页，而是一个 AI 创作型无限画布工具。审美优化的核心不是“更炫”，而是让用户长时间使用时更清晰、更专业、更少干扰。

推荐风格组合：

| 来源 | 借鉴内容 | 落地位置 |
|---|---|---|
| Figma / FigJam | 画布网格、悬浮工具栏、节点选择态、轻量面板 | 主画布、节点、工具栏、minimap |
| Linear | 克制深浅色、清晰层级、按钮状态、低噪音界面 | 全局主题、列表页、设置页、弹窗 |
| Runway / Krea | AI 创作面板、媒体预览、生成任务状态 | 生成节点、输出预览、资产库、工作流面板 |
| Raycast | 快捷命令、紧凑弹层、快速操作 | 创建菜单、节点菜单、未来命令面板 |
| Notion | 新手友好、空状态、轻量说明文案 | 画布选择页、空画布、素材库空状态 |

## 2. 不动的边界

本次优化不做框架迁移，不重写核心交互。

禁止事项：

- 不把项目迁移到 React、Vue、Next.js。
- 不重写 `static/js/canvas.js` 的核心拖拽、连线、缩放、保存逻辑。
- 不删除现有 DOM `id`，例如 `board`、`world`、`nodes`、`links`、`quickToolbar`。
- 不删除已有按钮和功能入口。
- 不大规模改变节点生成函数依赖的 class 结构。
- 不引入重型动画库或全局滚动动效。
- 不使用大面积玻璃拟态、紫蓝 AI 光效、营销页 hero 风格。

允许事项：

- 调整 CSS 变量、颜色、圆角、阴影、间距、字体层级。
- 给现有元素追加 class。
- 少量调整 HTML 分组结构，但必须保留原始 `id` 和事件入口。
- 增加纯视觉装饰层，例如轻量背景纹理、状态标记。
- 为按钮、面板、节点补充 hover、active、focus、disabled 状态。

## 3. 当前技术结构

主要文件：

| 文件 | 作用 | 改造策略 |
|---|---|---|
| `static/canvas.html` | 主画布页面结构 | 只做必要 class/分组微调，不删除 id 和 onclick |
| `static/css/canvas.css` | 主画布主要样式 | 第一阶段重点改造文件 |
| `static/css/theme.css` | 全局暗色主题和共用样式 | 第二重点，统一变量和深色质感 |
| `static/js/canvas.js` | 主画布交互逻辑 | 第一阶段尽量不动，只在必要时补状态 class |
| `static/index.html` | 入口页 | 后续统一风格 |
| `static/api-settings.html` | API 设置页 | 第二阶段处理 |
| `static/asset-manager.html` | 素材管理页 | 第二阶段处理 |
| `static/comfyui-settings.html` | ComfyUI 设置页 | 第二阶段处理 |

当前已有关键 UI 类：

| 模块 | 关键类 |
|---|---|
| 顶部区域 | `.topbar`、`.panel`、`.canvas-nav`、`.toolbar`、`.tool-btn` |
| 画布 | `.board`、`.world`、`.links`、`.link`、`.selection-box` |
| 节点 | `.node`、`.node-head`、`.node-title`、`.node-body`、`.node-run-status` |
| 菜单 | `.create-menu`、`.menu-btn`、`.selection-hub` |
| 资产面板 | `.canvas-asset-panel`、`.canvas-asset-head`、`.canvas-asset-grid` |
| 工作流面板 | `.workflow-transfer-panel`、`.workflow-transfer-card` |
| 预览弹窗 | `.output-lightbox`、`.output-preview`、`.output-prompt-panel` |
| 画布选择页 | `.canvas-gate`、`.gate-panel`、`.gate-list`、`.canvas-item` |
| 导航地图 | `.minimap`、`.minimap-content`、`.minimap-viewport` |

## 4. 视觉系统规范

### 4.1 色彩

采用“深色优先 + 浅色兼容”的专业工具色系。

深色建议：

```css
:root {
  --ui-bg: #0b0d12;
  --ui-bg-grid: rgba(112, 123, 146, 0.14);
  --ui-panel: rgba(17, 20, 27, 0.94);
  --ui-panel-solid: #11141b;
  --ui-panel-raised: #151a23;
  --ui-border: rgba(138, 149, 171, 0.18);
  --ui-border-strong: rgba(157, 170, 196, 0.32);
  --ui-text: #eef2f8;
  --ui-text-muted: #9aa6b8;
  --ui-text-faint: #647086;
  --ui-accent: #4cc9f0;
  --ui-accent-strong: #38bdf8;
  --ui-danger: #ff6b6b;
  --ui-success: #4ade80;
  --ui-warning: #fbbf24;
  --ui-shadow: rgba(0, 0, 0, 0.34);
}
```

浅色建议：

```css
:root {
  --ui-bg-light: #f5f7fb;
  --ui-bg-grid-light: rgba(100, 116, 139, 0.18);
  --ui-panel-light: rgba(255, 255, 255, 0.94);
  --ui-panel-solid-light: #ffffff;
  --ui-border-light: #e1e7ef;
  --ui-text-light: #111827;
  --ui-text-muted-light: #64748b;
}
```

原则：

- 只保留一个主强调色：蓝青色。
- 紫色、橙色、绿色只用于状态，不作为大面积品牌色。
- 背景不使用大渐变和发光球。
- 画布网格必须低对比，不能抢节点内容。

### 4.2 字体

当前 CSS 使用了 `Inter`。如果本地 `fonts.css` 已有更合适字体，可优先使用项目内字体。建议栈：

```css
font-family: "Geist", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

规则：

- 节点标题：11px-12px，字重 750-850，轻微字距。
- 面板标题：13px-15px，字重 800-900。
- 正文/说明：12px-13px，行高 1.45。
- 数字、尺寸、进度：使用 tabular numbers。

```css
.node,
.panel,
.tool-btn {
  font-variant-numeric: tabular-nums;
}
```

### 4.3 圆角

统一圆角层级，避免所有东西都是大圆角或胶囊。

| 元素 | 圆角 |
|---|---|
| 小按钮 | 9px-10px |
| 工具栏按钮 | 10px-12px，不建议全部胶囊 |
| 浮动面板 | 16px |
| 节点卡片 | 18px |
| 大弹窗 | 20px-24px |
| 状态徽标 | 999px 可保留 |

### 4.4 阴影

阴影用于区分层级，不做装饰。

建议：

```css
--shadow-panel: 0 18px 54px rgba(0, 0, 0, 0.28);
--shadow-node: 0 14px 36px rgba(0, 0, 0, 0.22);
--shadow-popover: 0 24px 70px rgba(0, 0, 0, 0.36);
```

禁用：

- 纯黑重阴影。
- 每个卡片都很重的阴影。
- 浅色模式里过强的浮层阴影。

## 5. 模块改造方案

### 5.1 主画布背景

目标：像专业设计工具，不像普通网页背景。

现状：

- `.board` 已经使用点阵网格。
- 深色下网格和背景可继续优化。

改造：

- 深色背景改为 `#0b0d12`。
- 网格降低透明度。
- 增加非常轻的中心暗角或径向层次，但不要出现明显渐变球。

建议改动文件：

```text
static/css/canvas.css
```

重点类：

```css
.board
.world
```

验收标准：

- 节点在画布上更突出。
- 长时间看不刺眼。
- 网格可见但不抢内容。

### 5.2 顶部工具栏

目标：参考 Figma 的悬浮工具条，但保留当前所有功能。

现状：

- `.topbar` 左侧是画布标题，右侧是快捷工具栏。
- `.toolbar-items` 功能很多，容易拥挤。
- `.tool-btn` 全部胶囊，视觉节奏不够专业。

改造：

- 工具栏容器更紧凑，背景更接近深色浮层。
- 按钮统一为 34px-36px 高度。
- 图标按钮和文字按钮区分：常用工具可图标+短文本，固定入口可更明显。
- 增加 active/hover/pressed/focus 状态。
- 折叠按钮保持现有逻辑，只改样式。

重点类：

```css
.topbar
.panel
.toolbar
.toolbar-items
.toolbar-fixed
.tool-btn
.toolbar-toggle
```

不要做：

- 不删除任何 `onclick`。
- 不拆掉 `quickToolbar`。
- 不把按钮换成新组件。

验收标准：

- 按钮对齐整齐。
- 工具栏不再像一排普通网页按钮。
- 功能入口没有丢失。

### 5.3 节点卡片

目标：节点像专业创作工具里的工作单元，状态更清楚。

现状：

- `.node` 使用较大圆角和阴影。
- `.node-head`、`.node-title` 已有基础层级。
- 运行状态 `.node-run-status` 已存在。

改造：

- 节点背景改为更稳的浮层色。
- 节点边框降低噪音，选中态更明确。
- 节点标题区更像工具面板 header。
- 输入、输出、运行状态分区更清楚。
- 不同节点类型允许轻微左侧色条或顶部小状态点，但不使用大面积彩色。

重点类：

```css
.node
.node.selected
.node-head
.node-title
.node-body
.node-run-status
.resize-handle
.port
.link
```

节点类型优先级：

1. 图片节点
2. 提示词节点
3. API 生成节点
4. 视频生成节点
5. 输出节点
6. LLM 节点
7. ComfyUI / RH / LTX 节点

验收标准：

- 选中节点一眼可见。
- 运行中、失败、排队状态一眼可见。
- 节点内部控件不挤、不乱。
- 节点拖拽和缩放不受影响。

### 5.4 连线与端口

目标：连线更精致，端口更像可交互连接点。

改造：

- 普通连线降低亮度。
- hover 或选中连线增强。
- 临时连线使用强调色虚线。
- 端口 hover 时有明确反馈。

重点类：

```css
.link
.link.temp
.link-hit
.port
.link-delete
```

风险：

- 连线坐标由 JS 控制，第一阶段只改 stroke、颜色、宽度，不改 SVG 结构。

### 5.5 右侧资产库面板

目标：参考 Runway/Krea 的创作资产面板，像专业媒体库。

现状：

- `.canvas-asset-panel` 已是右侧浮层。
- 有 asset library、category、drop zone、grid。

改造：

- 面板标题区更清晰。
- 下拉框、分类、上传区域风格统一。
- asset grid 增加更好的缩略图边框、hover、选中态。
- 空状态更友好，减少“空白”的廉价感。

重点类：

```css
.canvas-asset-panel
.canvas-asset-head
.canvas-asset-select
.canvas-asset-drop
.canvas-asset-grid
.canvas-asset-hover-preview
```

验收标准：

- 面板打开后像正式素材库。
- 缩略图更像媒体资产，不像普通图片列表。
- 拖拽上传区域明确。

### 5.6 工作流导入导出面板

目标：把它做成专业工具的任务面板，不像临时弹窗。

现状：

- `.workflow-transfer-panel` 结构已经完整。
- 有导出、导入、状态文本。

改造：

- 卡片层级降低，减少“卡片套卡片”。
- 导入区域更明确。
- 成功、忙碌、失败状态更统一。
- 主要按钮和次要按钮层级更清晰。

重点类：

```css
.workflow-transfer-panel
.workflow-transfer-head
.workflow-transfer-card
.workflow-transfer-btn
.workflow-import-drop
.workflow-transfer-meta
```

### 5.7 画布选择页

目标：参考 Notion/Linear 的项目选择页，清爽但不营销化。

现状：

- `.gate-panel` 是大面板。
- `.gate-list` 是网格卡片。
- 已有新建、排序、回收站。

改造：

- 面板尺寸、标题层级、卡片密度优化。
- 画布卡片减少重边框，增强 hover 和 active。
- 空状态更有指导性。
- 智能画布按钮不要再使用彩虹渐变，改成克制强调色。

重点类：

```css
.canvas-gate
.gate-panel
.gate-head
.gate-title
.gate-subtitle
.gate-list
.canvas-item
.primary-btn
.smart-create-btn
```

### 5.8 输出预览弹窗

目标：参考 Runway 的媒体预览，让生成结果成为焦点。

改造：

- 预览背景更暗，减少界面干扰。
- 图片/视频区域最大化。
- prompt 面板改成侧边信息区。
- 下载、复制、再次运行按钮更像工具操作。

重点类：

```css
.output-lightbox
.output-lightbox-shell
.output-preview
.output-prompt-panel
.preview-icon-btn
.preview-text-btn
```

## 6. 开发阶段规划

### Phase 0：建立安全基线

目标：确认当前功能可运行，避免改完不知道哪里坏了。

任务：

- 记录当前分支和未提交文件。
- 启动本地服务。
- 打开主画布页面。
- 截图保存当前状态。
- 确认以下功能可用：
  - 新建画布
  - 添加图片节点
  - 添加提示词节点
  - 添加生成节点
  - 节点拖拽
  - 节点连线
  - 打开资产库
  - 打开工作流导入导出
  - 打开输出预览

建议命令：

```bash
git status -sb
python3 main.py
```

如果启动方式以项目脚本为准，则使用已有启动脚本。

交付：

- 当前页面截图。
- 功能基线记录。

### Phase 1：主题变量和画布基础质感

目标：先统一气质，不碰复杂结构。

改动范围：

```text
static/css/canvas.css
static/css/theme.css
```

任务：

- 增加新的语义变量，不直接全局替换所有旧变量。
- 将旧变量映射到新变量，例如 `--page`、`--panel`、`--card`、`--line`。
- 优化 `.board` 背景和网格。
- 优化 `.panel`、`.tool-btn`、`.node` 的基础色、边框、阴影。

风险等级：低。

验收：

- 页面整体气质接近参考图。
- 所有功能入口仍可点击。
- 暗色和浅色都不明显崩坏。

### Phase 2：工具栏和画布导航

目标：让顶部操作区像专业画布工具。

改动范围：

```text
static/css/canvas.css
static/canvas.html
```

任务：

- 调整 `.topbar` 对齐和间距。
- 调整 `.canvas-nav` 标题区。
- 调整 `.toolbar`、`.toolbar-items`、`.toolbar-fixed`。
- 将按钮分为：
  - 节点创建类
  - 工作流/资产/日志类
  - 折叠控制类
- 只在必要时为按钮增加 class，不改变 onclick。

风险等级：低到中。

验收：

- 工具栏视觉更紧凑。
- 小屏不严重溢出。
- 折叠功能正常。

### Phase 3：节点系统视觉升级

目标：提升主工作区最重要的视觉对象。

改动范围：

```text
static/css/canvas.css
```

必要时少量调整：

```text
static/canvas.html
static/js/canvas.js
```

任务：

- 优化 `.node`、`.node-head`、`.node-body`。
- 优化 `.node.selected`、`.resize-handle`。
- 优化 `.node-run-status`。
- 优化图片、提示词、生成、输出等节点内部控件。
- 如果需要区分节点类型，优先使用已有节点类型 class，不改生成逻辑。

风险等级：中。

验收：

- 节点拖拽、缩放、输入、运行不受影响。
- 节点内容可读性提升。
- 选中态、运行态、失败态清晰。

### Phase 4：右侧面板和弹层

目标：让资产库、工作流、预览弹窗具备 AI 创作工具质感。

改动范围：

```text
static/css/canvas.css
```

任务：

- 优化 `.canvas-asset-panel`。
- 优化 `.workflow-transfer-panel`。
- 优化 `.output-lightbox`。
- 优化 `.create-menu` 和 `.selection-hub`。

风险等级：中。

验收：

- 面板打开/关闭动画正常。
- 文件拖入、工作流导入导出入口正常。
- 输出预览不影响图片和视频展示。

### Phase 5：画布选择页和设置页统一

目标：把主画布风格扩展到其他页面。

改动范围：

```text
static/css/canvas.css
static/css/theme.css
static/css/api-settings.css
static/css/asset-manager.css
static/css/comfyui-settings.css
static/css/smart-canvas.css
```

任务：

- 统一按钮、面板、输入框、列表、卡片。
- 减少每个页面单独发明一套颜色。
- 保持页面功能和布局习惯。

风险等级：中。

验收：

- 主页面、设置页、素材页视觉一致。
- 没有页面出现明显亮暗错乱。

## 7. 具体实施原则

### 7.1 CSS 优先

优先级：

1. CSS 变量
2. CSS 类样式
3. HTML 追加 class
4. JS 追加状态 class
5. 最后才考虑改 DOM 结构

### 7.2 保留原有选择器

不要删除旧类名。即使新增新类，也应保留原类：

```html
<button class="tool-btn tool-btn-node" ...>
```

不要改成：

```html
<button class="new-button" ...>
```

### 7.3 不破坏 JS 查询

在改 HTML 前，先搜索 JS 是否依赖相关 id/class：

```bash
rg "quickToolbar|tool-btn|canvasAssetPanel|workflowTransferModal|node-run-status" static/js/canvas.js
```

如果 JS 依赖某个 class，不要删除它。

### 7.4 状态必须完整

每个可交互元素至少要有：

- default
- hover
- active/pressed
- focus-visible
- disabled

节点运行相关至少要有：

- queued
- running
- failed
- done

## 8. 验收清单

每个阶段完成后检查：

- 页面能正常打开。
- 控制台没有新增 JS error。
- 新建画布正常。
- 添加节点正常。
- 节点拖拽正常。
- 节点缩放正常。
- 连线正常。
- 资产库打开正常。
- 工作流面板打开正常。
- 输出预览正常。
- 暗色模式正常。
- 小屏宽度下不严重遮挡。

视觉验收：

- 主画布接近参考图的专业工具质感。
- 颜色统一，没有随机紫色/橙色/蓝色到处出现。
- 工具栏、节点、右侧面板属于同一套设计系统。
- 画布内容仍然是视觉焦点。
- 没有过度动画。

## 9. UI 动画与交互增强建议

Pinterest 同类 UI 灵感里常见的趋势是：深色浮层、卡片微动效、悬浮状态、弹层过渡、进度可视化、局部强调色。这些可以借鉴，但当前项目是生产力工具，动画必须服务操作反馈，不能变成展示页特效。

### 9.1 动效原则

适合做：

- hover、active、focus 的即时反馈。
- 面板打开/关闭的轻量位移和透明度过渡。
- 节点创建、运行、成功、失败的状态反馈。
- 连线创建时的临时高亮。
- 拖拽、选择、吸附、缩放时的轻量视觉提示。
- 生成任务的进度脉冲、骨架加载、状态徽标。

不适合做：

- 大面积滚动动画。
- 全屏转场。
- 背景持续运动。
- 节点拖拽时复杂弹性动画。
- 影响 canvas 性能的 blur、filter、box-shadow 动画。
- 每个节点都持续闪烁或呼吸。

动画技术约束：

- 优先只动画 `transform` 和 `opacity`。
- 避免动画 `top`、`left`、`width`、`height`。
- 避免在大量节点上使用 `filter: blur()`。
- 动画时长控制在 120ms-260ms。
- 所有动画必须兼容 `prefers-reduced-motion`。

建议加入：

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 9.2 工具栏交互

目标：像 Figma/Raycast 一样，工具按钮有明确反馈，但不夸张。

落地点：

```css
.tool-btn
.toolbar
.toolbar.collapsed
.toolbar-toggle
```

建议：

- hover：背景略亮，图标颜色变强。
- active：按钮下压 `translateY(1px)` 或 `scale(.98)`。
- focus-visible：显示清晰描边。
- 当前工具：用蓝青色细边或小点，不用大面积填充。

示例方向：

```css
.tool-btn {
  transition:
    background-color 160ms var(--ease),
    border-color 160ms var(--ease),
    color 160ms var(--ease),
    transform 120ms var(--ease);
}

.tool-btn:active {
  transform: translateY(1px) scale(0.99);
}

.tool-btn:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--ui-accent) 72%, transparent);
  outline-offset: 2px;
}
```

### 9.3 节点创建动画

目标：新节点出现时让用户知道“创建成功”，但不影响后续拖拽。

落地点：

```css
.node
```

需要 JS 配合：

- 创建节点时给新节点临时加 class：`node-entering`。
- 180ms 后移除。

建议动画：

- 初始 `opacity: 0; transform: scale(.96) translateY(6px);`
- 结束 `opacity: 1; transform: scale(1) translateY(0);`

风险：

- 如果节点本身已有 transform 由 JS 控制，不能直接覆盖 transform。
- 更稳妥的方式是在节点内部增加视觉 wrapper 后再动画 wrapper。
- 第一阶段可先不做，等节点结构稳定后再加。

### 9.4 节点选择与拖拽反馈

目标：选中态比现在更精确，拖拽时更有控制感。

落地点：

```css
.node.selected
.selection-box
.selection-hub
.resize-handle
```

建议：

- 选中节点使用蓝青色细描边 + 轻微外发光。
- resize handle 只在 hover/selected 出现。
- 框选区域使用低透明蓝青背景。
- 多选工具条 `.selection-hub` 出现时用 120ms fade/slide。

不要做：

- 拖拽节点时加弹簧回弹。
- 拖拽过程中改变节点尺寸。

### 9.5 连线交互

目标：连线更容易理解，创建连接时更有反馈。

落地点：

```css
.link
.link.temp
.link-hit
.link-delete
```

建议：

- 普通连线低对比。
- 临时连线使用蓝青色虚线。
- hover 到连线删除点时，删除按钮轻微放大。
- 连接成功瞬间可短暂高亮新连线。

需要 JS 配合：

- 新建连线后短暂加 class：`link-created`。

### 9.6 生成任务状态动画

目标：让 AI 生成节点的“排队/运行/失败/完成”更清楚。

落地点：

```css
.node-run-status
.gen-cascade-btn
.node-retry-bar
.workflow-transfer-meta
```

建议：

- `queued`：灰色小点。
- `running`：小点 pulse，按钮显示轻量 loading stripe。
- `failed`：红色状态条，不使用弹窗轰炸。
- `done`：短暂显示成功状态，随后收起或变为普通状态。

适合新增：

```css
@keyframes statusPulse {
  0%, 100% { opacity: .45; transform: scale(.92); }
  50% { opacity: 1; transform: scale(1); }
}
```

注意：

- 只让状态点动，不让整张节点卡片动。
- 不要让多个节点同时大面积闪烁。

### 9.7 右侧面板打开/关闭动画

目标：资产库、工作流面板、预览弹窗打开时有空间层级。

落地点：

```css
.canvas-asset-panel
.workflow-transfer-panel
.output-lightbox
.create-menu
.prompt-template-modal
.log-modal
```

建议：

- 右侧面板：`opacity + translateX(8px)`。
- 顶部弹层：`opacity + translateY(-6px)`。
- 菜单：`opacity + scale(.98)`。
- 输出预览：背景 fade，内容 scale(.985) 到 1。

现状已有部分 `opacity` 和 `transform`，可以统一 easing 和时长。

### 9.8 资产库媒体交互

目标：让图片/视频资产像专业媒体库。

落地点：

```css
.canvas-asset-grid
.canvas-asset-hover-preview
.canvas-asset-drop
```

建议：

- 缩略图 hover：边框变亮，略微上浮 1px。
- 拖入区域 drag-over：边框变强调色，背景轻微变亮。
- hover preview：快速 fade，不要大动画。
- 选中资产：显示小角标或描边。

### 9.9 命令面板交互：建议新增但放到后期

这是我认为最值得新增的交互之一。它比很多装饰动画更有价值。

功能：

- 快速添加节点。
- 搜索节点类型。
- 搜索画布命令。
- 快速打开资产库、日志、工作流。

参考方向：

- Raycast 的命令面板。
- Figma 的 quick actions。

建议快捷键：

```text
Cmd/Ctrl + K
```

落地方式：

- 新增 `#commandPalette` 弹层。
- 不改变现有工具栏，只增加一个快捷入口。
- 命令项调用现有函数，例如 `addImageNode()`、`addPromptNode()`、`openCanvasLog()`。

风险等级：中。建议 Phase 6 后再做。

### 9.10 节点吸附与对齐辅助：建议新增但分阶段

这是第二个高价值交互。

功能：

- 拖动节点时显示对齐参考线。
- 靠近其他节点边缘或中心时轻微吸附。
- 多选节点时显示对齐分布操作。

参考方向：

- Figma 的红线/蓝线对齐提示。
- Miro / FigJam 的对象吸附体验。

风险：

- 会碰到节点拖拽逻辑，必须单独做，不和视觉 Phase 1-4 混在一起。

建议：

- Phase 1-5 只做视觉。
- Phase 6 单独做“对齐辅助线”，先不做自动吸附。
- Phase 7 再做轻量吸附。

## 10. 参考页面可借鉴结论

本次使用 OpenCLI Browser 实际打开了 Pinterest 搜索页：

```text
https://www.pinterest.com/search/pins/?q=ui%20%E7%95%8C%E9%9D%A2&rs=ac&len=2&source_id=ac_46zSicGK&eq=ui&etslf=5707
```

本地参考截图：

```text
/tmp/daxiong-ui-inspo/pinterest-ui-search.png
/tmp/daxiong-ui-inspo/pinterest-ui-search-2.png
```

从 Pinterest 同类 UI、Dribbble dashboard、dashboard best practices 中可借鉴的点：

- 深色界面适合长时间创作，但必须控制对比度。
- 信息应该分组，不要把所有按钮平铺成一排。
- 重要操作放在优先视觉区，次要操作收进面板或菜单。
- 色彩只用于状态和当前选中，不做装饰性彩虹。
- 卡片/面板的微交互比大动画更适合工具应用。
- 用户应该能定制工作区，而不是被固定布局限制。

### 10.1 Pinterest 页面实测：适合采用

#### A. 黑白高密度 dashboard 风格

页面中多张 B 端/dashboard 作品使用黑白灰、高密度网格、紧凑数据卡片。这是最适合当前项目的方向。

可迁移到：

- `.node`：节点内部信息更清晰，减少装饰。
- `.canvas-asset-panel`：资产库做成紧凑媒体管理面板。
- `.workflow-transfer-panel`：任务状态和操作分组更像专业工作台。
- `.gate-panel`：画布选择页更像项目管理入口。

具体做法：

- 用细边框和微弱阴影区分层级。
- 用小标题、状态点、进度条表达状态。
- 主要信息放左上，次要操作放右上或折叠菜单。
- 保留充足负空间，不把所有工具都做成彩色块。

#### B. Liquid Glass / 轻玻璃组件

页面中有多张 “Liquid Glass Kit” 和玻璃拟态组件。它们有高级感，但要克制使用。

适合迁移到：

- 顶部 `.toolbar`
- `.canvas-nav`
- `.selection-hub`
- `.create-menu`
- 输出预览里的工具按钮

不适合用于：

- 大量节点卡片
- 大面积右侧面板
- 滚动画布背景

具体做法：

- 只在浮动控制层使用 `backdrop-filter`。
- 背景透明度保持高一些，避免文字不可读。
- 玻璃边缘用 1px 内高光，不做强烈彩虹折射。

#### C. Soft 3D / 轻拟物按钮

页面中一些浅色组件有轻微的凸起、柔和阴影、圆润按钮。这适合用在新手入口和空状态，不适合主画布高频操作。

可迁移到：

- 空画布引导
- `.gate-list-empty`
- 画布新建入口
- 素材库空状态

不建议迁移到：

- 节点卡片
- 生成参数表单
- 大量工具栏按钮

#### D. 游戏 HUD / 科技面板

页面右侧出现多张游戏 UI/HUD，视觉冲击强，但直接套用会让项目偏游戏化。

可少量借鉴：

- 运行状态徽标
- 连接线高亮
- 节点执行中的 pulse 状态点
- 失败/警告提示的边缘色

不要借鉴：

- 大面积荧光
- 复杂圆形雷达
- 装饰性仪表盘
- 背景角色/场景图

#### E. 移动端卡片系统

多张移动端 app UI 使用大卡片、底部导航、柔和渐变。当前项目是桌面画布工具，不适合照搬移动端布局，但可以借鉴信息层级。

可迁移：

- 卡片内部的标题/副标题/状态/行动按钮顺序。
- 空状态的友好引导。
- 输出预览中媒体卡片的排版。

不要迁移：

- 底部手机导航。
- 过大的圆角和过大的卡片间距。
- 手机屏幕式纵向布局。

### 10.2 Pinterest 页面实测：不建议采用

以下趋势在 Pinterest 上常见，但不适合当前项目：

- 大面积粉紫渐变背景：会覆盖画布内容，显得像营销页。
- 超强玻璃/透明面板：复杂画布内容下可读性会变差。
- 3D 球体和装饰物：与创作工具目标无关。
- 游戏化全屏 HUD：容易把专业 AI 工具做成游戏面板。
- 高饱和彩虹按钮：会破坏状态颜色体系。
- 手机 App 风格底部导航：不适合桌面无限画布。

### 10.3 从 Pinterest 补充到当前项目的设计决策

结合实际页面观察，当前项目可以新增这些设计决策：

| 决策 | 说明 | 目标模块 |
|---|---|---|
| 浮层轻玻璃 | 只用于 toolbar、菜单、selection hub | `.toolbar`、`.create-menu`、`.selection-hub` |
| 节点专业卡片化 | 使用深色面板、细边框、清晰状态 | `.node`、`.node-head`、`.node-body` |
| 媒体预览更强 | 输出、资产库缩略图更像 AI 创作工具 | `.output-lightbox`、`.canvas-asset-grid` |
| 状态点动效 | 只让状态点和进度条动 | `.node-run-status` |
| 命令面板 | 比装饰动画更提升效率 | 新增 `#commandPalette` |
| 少量 HUD 语言 | 只用于连接线、运行态和警告态 | `.link.temp`、`.node.failed` |

对当前项目最有价值的新增交互排序：

1. `Cmd/Ctrl + K` 命令面板。
2. 节点创建轻动效。
3. 生成任务状态动画。
4. 连线创建/hover 反馈。
5. 资产库 hover preview 和 drag-over 反馈。
6. 节点对齐辅助线。
7. 多选后的浮动操作条强化。

## 11. 建议的第一批代码改动

第一批只做低风险改动：

1. 在 `static/css/canvas.css` 顶部重构变量。
2. 优化 `.board`。
3. 优化 `.panel`。
4. 优化 `.tool-btn`。
5. 优化 `.node`、`.node-head`、`.node.selected`。
6. 优化 `.canvas-asset-panel` 和 `.workflow-transfer-panel` 的基础面板质感。
7. 优化 `.minimap`。

暂不改：

- `static/js/canvas.js`
- 节点生成逻辑
- 保存/加载逻辑
- API 调用逻辑
- 工作流导入导出逻辑

## 12. 给 Codex 的执行提示词

第一阶段可以直接这样下达：

```text
使用 redesign-existing-projects skill。
请按 docs/ui-redesign-development-plan.md 执行 Phase 1。

要求：
- 不迁移框架
- 不重写 JS
- 不删除任何 DOM id
- 优先改 static/css/canvas.css 和 static/css/theme.css
- 保留现有功能入口
- 目标风格参考图路径：
  /Users/ruoyu/.codex/generated_images/019ebcf7-2069-7633-a886-d89318e4a293/ig_0dc111686c6c0c4b016a2c4bcc09e88191812ea3276cf08af2.png

完成后启动本地服务，用浏览器检查主画布页面，并汇报：
1. 改了哪些文件
2. 哪些功能验证通过
3. 是否有残余风险
```

第二阶段：

```text
继续使用 redesign-existing-projects skill。
请按 docs/ui-redesign-development-plan.md 执行 Phase 2，只优化顶部工具栏和画布导航。
不要改节点生成逻辑，不要改 API 调用逻辑。
```

## 13. 最终效果目标

完成后，用户打开主画布应当有以下感受：

- 这是一个专业 AI 创作工作台，不是普通网页拼装工具。
- 操作入口清楚，画布内容优先。
- 节点、连线、面板属于同一套设计语言。
- 深色模式适合长时间创作。
- 新手能理解，老用户不会觉得功能被藏起来。
