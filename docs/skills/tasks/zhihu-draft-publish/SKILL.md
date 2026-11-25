---
name: zhihu-draft-publish
description: 把 Hugo 博客文章同步到知乎草稿箱：盘点已发布文章、机械转换 Markdown、导入草稿、补插配图并验收。当用户要求「同步到知乎」「把没发的文章发到知乎」「管理知乎账号」「把博客搬到知乎」时使用。只写草稿，发布与删除必须由用户确认。
---

# 博客文章同步到知乎草稿箱

把本机 Hugo 文章搬到知乎，难点不在正文，而在三处：知乎读不到本地图片、Hugo 语法知乎不认、导入会新建草稿。整套流程按下面的顺序做，每步都能独立验证。

**硬规则**

- 只创建/编辑草稿，**不点「发布」**；发布由用户逐篇确认。
- 删除草稿、覆盖已有草稿属于破坏性操作，动手前必须问用户。
- 登录由用户手动完成，不接触账号密码。

## 第 0 步：确认范围

先问清三件事，避免漏发或重复发：

1. 同步哪些文章（全部 / 指定几篇 / 是否含 `draft: true` 的草稿）
2. 存草稿还是直接发布（默认存草稿）
3. 「已发过」怎么判定（默认对比知乎已发文章标题）

## 第 1 步：盘点两侧

**博客侧**：`content/post/**/index.md` 的 front matter。`draft: true` 的不算已发布。

```bash
grep -rn "^draft: true" content/post
```

**知乎侧**：打开 `https://www.zhihu.com/creator/manage/creation/article`，页面会显示「共 N 条内容」，逐条读标题。草稿在 `https://www.zhihu.com/creator/manage/creation/draft`。

标题两边经常不一致（博客叫「从 HunyuanWorld-Mirror 初探 3D 重建」，知乎叫「初探 3D 重建：HunyuanWorld-Mirror」），按主题比对，不要只做字符串相等。知乎独有的文章（直接写在知乎的）不算缺口。

## 第 2 步：转换成知乎能吃的 Markdown

```bash
python3 docs/skills/zhihu-draft-publish/scripts/hugo_to_zhihu.py \
  content/post/technical_musings/xxx/index.md -o /tmp/zhihu-work/md/xxx.md
```

脚本只做机械转换，不动正文文字：

| Hugo 写法 | 转换结果 |
| --- | --- |
| YAML front matter | 删除（标题单独填到知乎标题框） |
| 脚注 `[^key]` + 定义 | 正文改 `[n]`，文末追加编号「参考」列表 |
| `<table>` HTML 表格 | Markdown 表格（知乎会渲染成真表格） |
| `<figure><img>` | `![alt](IMG:x.png)` 占位 + 斜体图注 |
| `{{< details "标题" >}}` | `**标题**` 开头，内容展开 |
| 着色 `<span style>` | 引用块 `>`（知乎不支持文字颜色） |
| `<a id="锚点">` | 删除 |

转换后自查残留：

```bash
grep -nE '<[a-zA-Z/]|\{\{|\^' /tmp/zhihu-work/md/*.md
```

## 第 3 步：SVG 转 PNG

知乎图床不收 SVG，本地 SVG 必须先渲染成 PNG。本机用 Chrome 无头模式，`--window-size` 按 SVG 的 `viewBox` 宽高 ×2 取：

```bash
CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CH" --headless=new --disable-gpu --hide-scrollbars --no-first-run \
  --user-data-dir=/tmp/zhihu-work/chrome --force-device-scale-factor=2 \
  --window-size=900,748 --screenshot=/tmp/zhihu-work/img/chip-arch.png \
  "file:///abs/path/chip-arch.svg"
```

Chrome 要写配置目录，命令需要在本地沙箱外执行。渲染完用 Read 看一眼 PNG，确认文字没被裁掉。

## 第 4 步：导入为新草稿

1. 打开 `https://zhuanlan.zhihu.com/write`——**每打开一次就新建一篇草稿**，导入失败重试会留下重复草稿，收尾时要检查。
2. 工具栏「导入」→「导入文档（MD/Doc）」，弹层提示上限 30 MB。
3. 弹层里的 `input[type=file]` 是隐藏的，`browser_upload_file` 直接点会失败。可行做法二选一：把该 input 临时改成可见再上传；或向它注入 `File` 并派发 `input`/`change` 事件。
4. 注意页面里还有一个 `accept` 含 `.md` 的输入框属于「直答知识库」，注入会弹「选择文件/存入知识库」，**认准导入弹层里的那个**。
5. 导入成功后 URL 变成 `/p/<id>/edit`，字数从 0 变为正文长度，状态显示「草稿保存中」→「刚刚 · 草稿」。
6. 单独填标题，等自动保存。以服务端为准：

```bash
# 在页面里 fetch，或用浏览器直接打开
GET https://zhuanlan.zhihu.com/api/articles/<id>/draft
# 返回 title / content，可用于核对字数与图片数量
```

## 第 5 步：补插图片

导入时 `IMG:` 占位会被知乎当成真实图片去拉取，必然「上传失败」，刷新后整块消失、服务端只留空段落。所以图片必须在导入后单独插。

1. 用图注文本定位：图注段仍在，占位块已丢/变空段落。
2. 若点击正文无法落光标（后台标签页常见），直接改 Draft.js 状态：从 React fiber 取 `editorState`/`onChange`，用 `EditorState.forceSelection` 把选区设到图注 block 的 offset 0。
3. 点工具栏「图片」→ 上传 → 注入 PNG 的 `File` → 「插入图片」。
4. 验证：`img` 数量符合预期、`src` 为 `pic-private.zhihu.com`（或 `pic*.zhimg.com`）、`naturalWidth` 与本地图比例一致、图片 block 紧邻图注 block 之前。

一次只插一张并核对，插错用编辑器「撤销」回退，别靠肉眼对齐。

## 第 6 步：验收

- 每篇再打开一次编辑页，读 title、字数、`img` 数量。
- 全文搜「上传失败」，必须为 0。
- 表格要确认是 `<table>` 结构，不是一堆竖线文本。
- 检查草稿箱有没有重复条目（同标题多篇），只保留内容完整的那篇。
- 最后把草稿链接列给用户，由用户预览后自行发布。

## 已知坑

| 现象 | 原因与处理 |
| --- | --- |
| 导入后字数一直 0、「草稿保存中」不结束 | 旧标签页状态脏了，关掉重开 `/write` 重新导入 |
| 点正文光标总是跳到文首 | Draft.js 选区被复位，用 `forceSelection` 显式定位 |
| 编辑器点不动 | 「草稿备份」全屏弹层盖在上面，先关掉它 |
| 截图不可用 / 无法聚焦 | 标签页在后台，`document.hasFocus()` 为 false；改用 DOM 与网络请求取证 |
| 本地文件传不进去 | 系统文件选择器（`showOpenFilePicker`）接管了点击；改用注入 `File` |
| 需要让页面 fetch 到本地图片 | 起一个允许 CORS 的临时本地静态服务（如 8899 端口），用完关掉 |
| 导入重复生成草稿 | 每次打开 `/write` 都是新草稿；失败重试后去草稿箱清理 |

## 备选方案

不想走文件导入时，知乎编辑器支持粘贴富文本（`stripPastedStyles=false`，会保留 `text/html` 的标题、列表、表格），可以本地渲染页面后整段复制粘贴；「更多」菜单里还有「Markdown 语法输入」开关。图片仍需单独上传。
