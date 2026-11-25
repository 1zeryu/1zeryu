# Uranus-smd 的 CI 案例解析

真实仓库：`github/Uranus-smd/.github/workflows/ci.yml` + `tests/run_tests.sh`。

这套 CI 是「PR 门禁：lint + L0/L1 CPU 单测 + L2 分布式 + 条件性 L3 GPU 烟测」的完整范例，适合作为复杂项目的模板。

## 一、ci.yml 结构

### 触发（on）
- `pull_request` types `[opened, synchronize, reopened, labeled]`：PR 建立 / 更新 / 重开 / 打标签都触发。`labeled` 让维护者打 `ci:gpu` 标签强制跑 GPU。
- `push` branches `[main, dev]`：只推主分支才跑，feature 分支等 PR。
- `workflow_dispatch`：手动入口。

### 权限（permissions）
`contents: read` + `pull-requests: read`，最小只读。

### 并发（concurrency）
`group: ci-${{ github.ref }}` + `cancel-in-progress: true`：同一 ref 只保留最新一次运行，自动取消旧的，省资源。

### 四条 job 依赖图
```
lint     ──┬──> fast（needs: lint）
              └──> gpu-smoke（needs: [lint, changes]）
changes  ────^
```

### job 详解

1. **lint**：固定版本 uv（`astral-sh/setup-uv@v5`，version `0.11.6`），`uvx --from ruff==0.16.0 ruff check .` + `ruff format --check .`。版本与 `pyproject.toml` 保持一致。

2. **changes**：`dorny/paths-filter@v3` 判断改动是否触及 GPU 相关路径（`uranus/models`、`pipelines`、各 `*parallel*.py`、`tests/gpu`、`tests/distributed`、`pyproject.toml`、`uv.lock`）。输出 `gpu` 布尔值供下游用。

3. **fast（L0/L1 CPU）+ L2**：
   - 装系统库：Pillow 的 `libjpeg/zlib/tiff/freetype/lcms/webp`，torchcodec 的 `ffmpeg + libnpp*`。
   - 探测内部 PyPI 镜像（`mirrors.ivolces.com`）；可达走内网，不可达回退官方 PyPI（`if:` 条件步骤 + `GITHUB_OUTPUT` 分流）。
   - `uv sync --group dev --frozen` 用锁文件精确还原。
   - `bash tests/run_tests.sh fast` 跑 L0/L1 单测 + 覆盖率；`bash tests/run_tests.sh dist` 跑 L2 gloo 2-rank 分布式。
   - `if: always()` 上传 junit/coverage 产物。

4. **gpu-smoke（L3）**：
   - `runs-on: uranus-vci-gpu`（自托管 GPU runner）。
   - 复杂 `if:` 条件：手动触发 / push 且触及 GPU 路径 / PR 来自同仓库且（触及 GPU 或打了 `ci:gpu` 标签）。校验 `head.repo` 防止 fork 恶意代码。
   - `timeout-minutes: 30` + 单卡 `URANUS_GPU_DEVICES: "0"`。
   - 代理 + `git config http.version HTTP/1.1` + 重试 3 次 `uv sync`（应对 VCI 出网不稳定）。

## 二、run_tests.sh 测试分层

| tier | pytest 范围 | 覆盖 | 对应 CI job |
|------|------------|------|-------------|
| fast (L0+L1) | `tests/unit tests/property ... -m "not (gpu or tos or dist or model or slow)"` | 纯 CPU 单测 | fast |
| dist (L2) | `tests/distributed -m dist` | CPU 分布式 gloo 2-rank | fast |
| gpu (L3) | `tests/gpu -m "gpu or model"` | GPU 烟测 | gpu-smoke |
| e2e | `tests/e2e`（真实权重/TOS） | 手动/nightly | - |
| lint | ruff | lint | lint job |

环境变量：脚本头部统一 `CUDA_VISIBLE_DEVICES=""`（非 GPU 层禁用 CUDA）、`HF_HUB_OFFLINE=1` 禁联网、`WANDB_MODE=disabled`。脚本非 GPU 层禁用 CUDA。

## 三、可直接复用的设计模式

- **内网镜像 + PyPI 回退**：探测 `GITHUB_OUTPUT`，条件步骤分流，兼顾速度与可用性。
- **路径过滤省资源**：`paths-filter` 决定昂贵 job 是否跑。
- **自托管 runner 安全**：fork 白名单 + 超时保护。
- **分层测试脚本**：`run_tests.sh` 一个入口、`tier` 参数切换，CI 只调这个脚本；本地 `tests/run_tests.sh ci` 即可复现（lint + fast + dist）。