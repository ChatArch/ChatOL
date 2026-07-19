# 真实实践：服务端 Overleaf Smoke

这页记录 ChatOL 原生 Python client 和 `oleaf` CLI 的服务端真实实践。内容已脱敏：不保存真实公网服务 URL、账号邮箱、密码、cookie、内部 build URL、项目 ID 或 entity ID。

## 环境形态

```text
ChatOL checkout
  -> 同一服务器上的 Overleaf loopback 地址
  -> 运行时加载私有环境变量文件
  -> 自托管 Overleaf smoke 项目
```

密钥和凭据保存在仓库外部，运行时通过 Overleaf 命名空间的环境变量或 ChatEnv 的 active `overleaf` profile 传入 `chatol.workflows.client_from_env`。

```bash
set -a
source <private-overleaf-env>
set +a
export OVERLEAF_SITE_URL=http://127.0.0.1:<overleaf-port>
export OVERLEAF_HTTP_TIMEOUT=45
```

## 已实践命令

```bash
oleaf doctor --json
oleaf projects list --json
oleaf projects info "<smoke-project-name>" --json
oleaf compile run "<smoke-project-name>" --json
oleaf compile pdf "<smoke-project-name>" -o smoke.pdf --json
oleaf compile output "<smoke-project-name>" log -o smoke.log --json
oleaf files zip "<smoke-project-name>" -o project.zip --json
oleaf files pull "<smoke-project-name>" ./source --json
oleaf files list "<smoke-project-name>" --json
oleaf files upload "<smoke-project-name>" ./chatol-agent-practice.tex --remote-path chatol-agent-practice.tex --json
oleaf files delete "<smoke-project-name>" chatol-agent-practice.tex --apply --json
```

## 结果

| 工作流 | 结果 |
| --- | --- |
| `doctor` | 成功 |
| `projects list` | 成功；实践实例中可见 1 个项目 |
| `projects info` | 成功 |
| `compile run` | 成功 |
| `compile pdf` | 成功；PDF 已写入本地 |
| `compile output log` | 成功；日志已写入本地 |
| `files zip` | 成功；项目 zip 已写入本地 |
| `files pull` | 成功；本地解压 3 个文件 |
| `files list` | 成功；可逆变更前后项目文件数均为 3 |
| `files upload` | 成功；仅上传根目录实践文件 `chatol-agent-practice.tex` |
| `files delete --apply` | 成功；实践文件已删除，并确认远端不存在残留 |

本次观察到的产物大小：

```text
pdf_bytes: 247915
log_bytes: 17466
project_zip_bytes: 99242
pulled_count: 3
practice_pdf_bytes: 248106
practice_log_bytes: 17466
```

## Review 记录

- CLI 命令保持薄封装，实际逻辑由可 import 的 workflow 函数承载。
- 同一套能力可以从 Python 里通过 `chatol.workflows` 调用。
- JSON 默认不输出内部编译 URL。
- 密码和 cookie 没有作为普通进程参数传入。
- `files upload` 的远端变更范围限定为单个根目录可逆文件：`chatol-agent-practice.tex`。
- `files delete --apply` 只用于删除这个精确文件名；删除后用 `files list` 验证无残留。
- 当前实例的项目 HTML 不暴露根目录 metadata；ChatOL 通过 Socket.IO 项目树回退解析来获取删除所需的文件 ID。
- 本次 smoke 尚未覆盖嵌套目录上传、完整同步、重命名、评论和管理员能力。

## 后续实践

下一批真实实践建议覆盖：

1. 嵌套目录上传，包括目录发现和缺失目录创建；
2. 安全同步计划，在任何破坏性同步前只生成 plan；
3. 管理员 route 探测，再考虑 user-management 实现；
4. 编译日志诊断，把 LaTeX 错误整理成 Agent 可执行反馈；
5. 可选的单文件下载和重命名命令。
