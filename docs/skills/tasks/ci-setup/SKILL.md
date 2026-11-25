---
name: ci-setup
description: 给一个软件项目从零搭建持续集成（CI）：把「可自动跑的测试 + 依赖声明 + 一份 workflow 编排文件」串成 PR 门禁，覆盖触发条件、依赖锁版本、缓存、分层执行、权限最小化与自托管 runner 安全。当用户要「搭 CI」「让测试自动跑」「配 GitHub Actions」「给 PR 加门禁」时使用。
---

# CI 搭建（持续集成）

## 什么时候用

- 新仓库想做到「每次提交/PR 自动跑测试，失败不让合并」。
- 已有测试但没人自动跑，合入后才被发现挂了。
- 要把 lint、单测、GPU/集成测试按成本分层触发。

## 核心认知：最小闭环三件套

CI 不神秘，本质只有三样，缺一不可：

1. **可自动跑的测试** —— 无交互、单命令能跑（`pytest tests/`），环境可复现。
2. **依赖声明** —— `pyproject.toml` + 锁文件（或 `requirements.txt`），让 CI 的干净机器能装出和本地一致的环境。
3. **一份 workflow 编排文件** —— 描述「拉代码 → 装环境 → 跑测试 → 上报结果」的 `ci.yml`。

其余所有东西（触发、分层、缓存、覆盖率）都属于 `ci.yml` 里的可选增强，解决资源/安全/可复现问题，不是起步必需。

## 落地顺序（先跑绿，再增强）

1. 最小 `ci.yml`：checkout → 装依赖 → 跑测试，先让最小闭环跑绿。
2. 加 lint job，用 `needs` 串成「lint 过了再跑慢测试」。
3. 锁工具/依赖版本，配缓存。
4. 细化触发条件、声明最小权限。
5. 按需加路径过滤、覆盖率上报、GPU/发布 job。

## 最小模板（Python + pytest）

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --group dev --frozen
      - run: pytest tests/
```

## 关键设计点

- **触发**：PR（`opened/synchronize/reopened`）做门禁；`push` 到主分支跑完整回归；`workflow_dispatch` 留手动入口。
- **分层省钱**：快测试（lint、单测）先跑；慢/贵测试用 `needs` + `dorny/paths-filter` 按改动路径决定是否触发。
- **可复现**：锁版本（工具、依赖、锁文件），避免上游升级导致 CI 突然挂。
- **权限最小化**：`permissions: { contents: read }`，别用默认的宽权限。
- **安全**：自托管 runner 必须校验 PR 来源（`head.repo.full_name == github.repository`），防 fork 恶意代码跑在你机器上；配 `timeout-minutes` 防占死。
- **报告**：`actions/upload-artifact` 用 `if: always()`，失败也上传 junit/coverage 产物便于定位。

## 参考

完整案例（分层 + GPU 自托管 + 镜像回退 + 覆盖率门禁的真实 CI）：见 `references/uranus-ci.md`。