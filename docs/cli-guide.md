# ChatOL CLI 实战指南

这篇指南是当前 ChatOL Overleaf 能力面的实用 CLI 地图。它覆盖已实现命令树、每个命令背后的 Python API，以及来自 self-hosted Overleaf smoke 的脱敏实践边界。

## 当前 CLI 树

```text
oleaf
├── --base-url                # 默认读取 OVERLEAF_SITE_URL
├── --email                   # 默认读取 OVERLEAF_ADMIN_EMAIL
├── --password-stdin          # 从 stdin 读取密码
├── --session-stdin           # 从 stdin 读取 session cookie
├── --cookie-name             # 默认 overleaf_session2
├── --timeout                 # HTTP timeout 秒数
├── doctor                    # 验证登录和项目列表访问
├── projects                  # 项目发现
│   ├── list                  # 列出当前会话可见项目
│   └── info <project>        # 按项目名或 ID 解析项目
└── compile                   # 编译和产物下载
    ├── run <project>         # 触发编译并输出 metadata
    ├── pdf <project>         # 编译并下载 PDF
    └── output <project>      # 编译并下载一个 output artifact
```

## 实现合约

ChatOL 命令应是薄 Click 包装层。每个实质命令都调用一个可导入 Python 函数或 `OverleafClient` method。

示例：

```python
from pathlib import Path
from chatol.client import OverleafClient
from chatol.workflows import compile_project, download_output, download_pdf, list_projects

projects = list_projects()
project, compile_result = compile_project(projects[0].name)
pdf = download_pdf(project.name, Path("output.pdf"))
log = download_output(project.name, "log", Path("output.log"))
```

CLI 只负责：

- 解析 Click 参数；
- 从 stdin 读取 password/session；
- 调用 `chatol.workflows`；
- 输出文本或 JSON；
- 把异常转换成稳定错误输出。

## 连接和凭据

进程环境变量方式：

```bash
export OVERLEAF_SITE_URL="https://overleaf.example.com"
export OVERLEAF_ADMIN_EMAIL="<email>"
export OVERLEAF_ADMIN_PASSWORD="<password>"
oleaf doctor --json
```

stdin 方式：

```bash
printf '%s\n' "<password>" | oleaf --password-stdin doctor --json
printf '%s\n' "<session-cookie>" | oleaf --session-stdin doctor --json
```

ChatEnv 方式：

```bash
python -m chatenv.cli init -t overleaf -I
python -m chatenv.cli test -t overleaf -I
oleaf doctor --json
```

配置优先级：显式 CLI/Python 参数 > 进程环境变量 > active ChatEnv `overleaf` profile。

## 项目发现

```bash
oleaf projects list --json
oleaf projects info "<project-name>" --json
oleaf projects info "<project-id>" --json
```

`projects list` 默认过滤 archived 和 trashed 项目。`projects info` 支持项目名或项目 ID；自动化中如果能拿到 ID，优先用 ID。

## 编译和产物

```bash
oleaf compile run "<project-name>" --json
oleaf compile pdf "<project-name>" -o output.pdf --json
oleaf compile output "<project-name>" log -o output.log --json
```

`compile pdf` 和 `compile output` 会触发编译，然后下载对应产物。Overleaf compile cooldown 的重试逻辑在 workflow 层，不在 CLI 层。

## 路由和辅助函数映射

```text
oleaf doctor                 -> chatol.workflows.client_from_env + OverleafClient.list_projects
oleaf projects list          -> chatol.workflows.list_projects
oleaf projects info          -> chatol.workflows.get_project
oleaf compile run            -> chatol.workflows.compile_project
oleaf compile pdf            -> chatol.workflows.download_pdf
oleaf compile output         -> chatol.workflows.download_output

OverleafClient.from_password -> GET/POST /login, then GET /project
OverleafClient.list_projects -> GET /project and parse embedded project metadata
OverleafClient.compile       -> POST /project/{project_id}/compile
```

## 安全注意

- 密码和 session cookie 不作为普通命令参数传递。
- JSON 默认不输出内部 compile URL、owner/updater metadata。
- artifact 下载拒绝 cross-origin URL。
- 报告、issue、PR 评论和截图里必须脱敏真实 URL、邮箱、cookie、token、build URL、项目/user ID。
- 文件 mutation、sync、admin/user management 尚未实现；未来必须默认 dry-run 或显式 `--apply`。
