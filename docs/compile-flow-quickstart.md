# 编译与产物

这篇文档说明如何用 ChatOL 触发 Overleaf 编译，并下载 PDF 或日志产物。典型链路是：加载 Overleaf 配置，解析目标项目，触发编译，下载产物，再把日志反馈给调用方进行下一轮修改。

## 命令概览

```text
oleaf doctor                 # 验证登录和项目列表访问
oleaf projects list          # 列出当前会话可见项目
oleaf projects info          # 解析项目名或项目 ID
oleaf compile run            # 触发编译并返回编译状态
oleaf compile pdf            # 编译并下载 PDF
oleaf compile output         # 编译并下载指定产物，例如 log
oleaf compile bundle         # 编译一次并下载多种常用产物
```

所有命令支持 `--json` / `--json-output`，方便 Agent 读取结构化结果。

## 最小流程

```bash
oleaf doctor --json
oleaf projects list --json
oleaf projects info "<project-name>" --json
oleaf compile run "<project-name>" --json
oleaf compile pdf "<project-name>" -o build/output.pdf --json
oleaf compile output "<project-name>" log -o build/output.log --json
oleaf compile bundle "<project-name>" -o build/artifacts --json
```

推荐把 Agent 产物写进任务工作目录，例如 `build/` 或 project-local `playground/`，不要写到仓库根目录的长期文档区。

## Python 调用

```python
from pathlib import Path
from chatol.workflows import compile_project, download_output, download_pdf, get_project

project = get_project("<project-name>")
resolved, result = compile_project(project.id)
pdf_path = download_pdf(project.id, Path("build/output.pdf"))
log_path = download_output(project.id, "log", Path("build/output.log"))
```

如果调用方需要一次拿到 PDF 和日志，可以使用 bundle workflow：

```python
from pathlib import Path
from chatol.workflows import download_compile_bundle

bundle = download_compile_bundle("<project-name>", Path("build/artifacts"))
```

如果是长期服务进程，也可以自己创建 `OverleafClient` 并复用 session：

```python
from chatol.client import OverleafClient

client = OverleafClient.from_session_cookie(
    "https://overleaf.example.com",
    "<session-cookie>",
)
projects = client.list_projects()
```

## 重试和 cooldown

`chatol.workflows.compile_project` / `download_pdf` / `download_output` 默认在 workflow 层处理可重试的 Overleaf compile cooldown，而不是把等待逻辑散落在 CLI 调用者里。默认 retry delays 是：

```text
0s, 20s, 45s
```

如果调用方有自己的调度器，可以传入自定义 `retry_delays` 和 `sleep`。

## 输出和脱敏

Agent 可以使用这些稳定字段：

| 命令 | 稳定信息 |
| --- | --- |
| `doctor --json` | `ok`, `project_count` |
| `projects list --json` | 项目 `id`, `name`, `archived`, `trashed` 等非 owner metadata |
| `compile run --json` | compile `status` 和 output 类型摘要 |
| `compile pdf --json` | `ok`, 本地 `output`, 文件大小字段 |
| `compile output --json` | `ok`, `output_type`, 本地 `output`, 文件大小字段 |
| `compile bundle --json` | `ok`, `project`, `compile`, `artifacts` |

默认 JSON 不输出内部编译 URL、项目所有者/更新者元数据。不要把真实服务 URL、邮箱、cookie、build URL、项目 ID 或用户 ID 写进公开输出。

## 当前边界

- 单文件拉取、上传和删除见 [Agent 任务闭环](agent-overleaf-flow.md)。
- 本地目录和 Overleaf 项目的双向同步不在编译命令中处理。
- 编译日志的自动诊断和源码修改闭环。
- 评论和协作线程。
- 管理员和用户管理。

涉及远端写入的能力需要 dry-run 或 `--apply` 保护。
