# ChatOL CLI 实战指南

这篇指南说明 `oleaf` 的主要命令、参数、安全边界，以及每个命令背后的 Python API。它面向自托管 Overleaf 的日常项目发现、文件拉取、单文件上传、编译和产物下载。

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
├── files                     # 文件和项目归档
│   ├── list <project>        # 列出文件实体，依赖实例支持 /entities
│   ├── zip <project>         # 下载项目 zip
│   ├── pull <project> <dir>  # 下载并安全解压项目 zip
│   ├── upload <project>      # 上传一个本地文件到项目根目录
│   └── delete <project>      # 删除一个远端文件，必须 --apply
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
from chatol.workflows import compile_project, download_output, download_pdf, list_projects, pull_project

projects = list_projects()
files = pull_project(projects[0].name, Path("source"))
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

## 文件和项目归档

```bash
oleaf files list "<project-name>" --json
oleaf files zip "<project-name>" -o project.zip --json
oleaf files pull "<project-name>" ./source --json
oleaf files pull "<project-name>" ./source --force --json
oleaf files upload "<project-name>" ./source/main.tex --remote-path main.tex --json
oleaf files delete "<project-name>" old-note.tex --apply --json
```

当前第一版文件能力服务 Agent 编译闭环：先拉取项目，再由 Agent 修改本地文件，最后上传明确选择的根目录文件。它不是完整同步器：

- `files pull` 默认拒绝覆盖已有文件，覆盖必须显式 `--force`。
- `files pull` 会拒绝 zip-slip 路径逃逸。
- `files upload` 当前只支持项目根目录文件；嵌套目录上传、自动建目录、重命名、完整同步仍是后续增量。
- `files delete` 当前只按路径删除 `doc`/`file`，不删除文件夹，并且必须显式 `--apply`。
- 项目页缺失 `rootFolder` metadata 时，ChatOL 会使用 Socket.IO 项目树回退解析来获取根目录和文件 ID。
- `files list` 依赖自托管 Overleaf 暴露 `/project/{project_id}/entities`；不支持时会明确返回“不支持”。

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
oleaf files list             -> chatol.workflows.list_files
oleaf files zip              -> chatol.workflows.download_project_zip
oleaf files pull             -> chatol.workflows.pull_project
oleaf files upload           -> chatol.workflows.upload_file
oleaf files delete           -> chatol.workflows.delete_file
oleaf compile run            -> chatol.workflows.compile_project
oleaf compile pdf            -> chatol.workflows.download_pdf
oleaf compile output         -> chatol.workflows.download_output

OverleafClient.from_password -> GET/POST /login，然后 GET /project
OverleafClient.list_projects -> GET /project，并解析嵌入的项目元数据
OverleafClient.files zip     -> GET /project/{project_id}/download/zip
OverleafClient.files upload  -> 读取 /project/{project_id} 或 Socket.IO 项目树，然后 POST /project/{project_id}/upload
OverleafClient.files delete  -> 读取 /project/{project_id}/entities 和项目树，然后 DELETE /project/{project_id}/{type}/{id}
OverleafClient.compile       -> POST /project/{project_id}/compile
```

## 安全注意

- 密码和 session cookie 不作为普通命令参数传递。
- JSON 默认不输出内部编译 URL、项目所有者/更新者元数据。
- 产物下载拒绝跨源 URL。
- 不要把真实 URL、邮箱、cookie、token、build URL、项目 ID 或用户 ID 写进公开输出、文档、issue 或 PR 评论。
- 当前只实现根目录单文件上传和受保护单文件删除；重命名、完整同步、管理员和用户管理尚未实现，未来必须默认 dry-run 或显式 `--apply`。
