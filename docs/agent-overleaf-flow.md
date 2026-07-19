# Agent Overleaf 任务闭环

这篇文档把 ChatOL 当前要推进的 Overleaf 形态定为一个任务闭环：本地任务目录承载 Agent 修改，Overleaf 承载远端编译与协作，ChatOL 负责同步、编译、产物拉取和反馈。

## 当前目标

```text
Agent task
├── pull: 从 Overleaf 拉取项目 zip 到本地任务目录
├── edit: Agent 在本地修改 LaTeX / bib / assets
├── push: 把明确选择的文件上传回 Overleaf
├── compile: 触发 Overleaf 编译
├── collect: 拉回 PDF 与 log/bbl/aux 等产物
└── feedback: 把编译状态、log 摘要、产物路径返回给 Agent
```

## 第一版已实现能力

| 环节 | CLI | Python API | 状态 |
| --- | --- | --- | --- |
| 项目发现 | `oleaf projects list/info` | `list_projects`, `get_project` | 已实现，已 live practice |
| 拉取 zip | `oleaf files zip <project> -o <zip>` | `download_project_zip` | 已实现，已 live practice |
| 拉取并解压 | `oleaf files pull <project> <dir>` | `pull_project` | 已实现，已 live practice |
| 单文件上传 | `oleaf files upload <project> <file>` | `upload_file` | 已实现，已 live practice；当前仅根目录 |
| 单文件删除 | `oleaf files delete <project> <path> --apply` | `delete_file` | 已实现，已 live practice；必须显式 apply |
| 编译 | `oleaf compile run <project>` | `compile_project` | 已实现，已 live practice |
| PDF | `oleaf compile pdf <project> -o <pdf>` | `download_pdf` | 已实现，已 live practice |
| 编译产物 | `oleaf compile output <project> log -o <log>` | `download_output` | 已实现，已 live practice |

## 推荐任务目录

```text
<task-dir>/
├── source/              # files pull 解压后的项目源码
├── artifacts/           # PDF/log/bbl/aux 等编译产物
├── reports/             # 任务总结、编译诊断、变更记录
└── TASK.md              # 任务目标和敏感信息边界
```

## 命令流程

```bash
# 1. 拉取远端项目源码
oleaf files pull "<project-name>" ./source --json

# 2. Agent 修改本地文件，例如 source/main.tex
#    当前第一版不做全量 sync；只上传明确选择的文件。

# 3. 上传单个文件到 Overleaf 项目根目录
oleaf files upload "<project-name>" ./source/main.tex --remote-path main.tex --json

# 可选：清理专门的 practice 文件；删除必须显式 --apply
oleaf files delete "<project-name>" chatol-agent-practice.tex --apply --json

# 4. 编译并收集产物
oleaf compile run "<project-name>" --json
oleaf compile pdf "<project-name>" -o ./artifacts/output.pdf --json
oleaf compile output "<project-name>" log -o ./artifacts/output.log --json
```

## 安全边界

- 第一版 `files upload` 只支持项目根目录文件；嵌套目录、自动建目录、全量 push/sync 暂不实现。
- 第一版 `files delete` 只按文件路径删除 `doc`/`file`，必须显式 `--apply`；不删除文件夹。
- `files pull` 默认不覆盖本地已有文件；需要覆盖时必须显式 `--force`。
- `files pull` 做 zip-slip 路径保护，拒绝解压逃逸到目标目录外的路径。
- 当项目 HTML 不暴露 `rootFolder` 时，ChatOL 会通过 Socket.IO project tree fallback 解析 root folder 和文件 id。
- 编译产物 URL 不出现在默认 JSON 输出里；报告不能保存内部 build URL。
- 密码、session cookie、真实 Overleaf 公网域名不写入 docs、reports、issue 或 PR 评论。

## 后续增量

1. 增加 `files download <project> <remote-path>`，用于拉单个文件。
2. 增加 `files tree <project>` 或增强 `files list`，兼容没有 `/entities` 的实例。
3. 增加嵌套目录上传：folder tree discovery、missing folder creation、重复文件覆盖规则。
4. 增加 `sync plan`：只做计划，不写远端。
5. 增加 `sync push --apply`：需要显式 apply，删除默认关闭。
6. 增加 compile log 诊断，把 LaTeX 错误摘要成 Agent 可执行反馈。
