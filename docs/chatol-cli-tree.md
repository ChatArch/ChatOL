# CLI 能力地图

这篇文档给出 ChatOL 当前 CLI 能力、已实现 Python API 和后续规划边界。它是较短的能力地图；实战命令和例子见 [CLI 实战指南](cli-guide.md)。

状态约定：

- **已实现**：代码、单测和 CLI 路径已经存在。
- **已验证**：已在自托管 Overleaf 上做过脱敏真实实践。
- **未实现**：只记录设计方向和安全要求；等真实实现、测试和真实实践完成后，再补操作文档。

## 当前已实现并已验证

```text
oleaf
├── doctor
├── projects
│   ├── list
│   └── info <project>
├── files
│   ├── list <project>
│   ├── zip <project> -o <zip>
│   ├── pull <project> <dir> [--force]
│   ├── upload <project> <local-path> [--remote-path <name>]
│   └── delete <project> <remote-path> --apply
└── compile
    ├── run <project>
    ├── pdf <project> -o <path>
    └── output <project> <output-type> -o <path>
```

| CLI | Python API | 状态 |
| --- | --- | --- |
| `oleaf doctor` | `client_from_env`, `OverleafClient.list_projects` | 已实现 |
| `oleaf projects list` | `chatol.workflows.list_projects` | 已实现 |
| `oleaf projects info` | `chatol.workflows.get_project` | 已实现 |
| `oleaf files list` | `chatol.workflows.list_files` | 已实现，已真实验证 |
| `oleaf files zip` | `chatol.workflows.download_project_zip` | 已实现，已真实验证 |
| `oleaf files pull` | `chatol.workflows.pull_project` | 已实现，已真实验证 |
| `oleaf files upload` | `chatol.workflows.upload_file` | 已实现，已真实验证；当前仅根目录 |
| `oleaf files delete` | `chatol.workflows.delete_file` | 已实现，已真实验证；必须显式 `--apply` |
| `oleaf compile run` | `chatol.workflows.compile_project` | 已实现 |
| `oleaf compile pdf` | `chatol.workflows.download_pdf` | 已实现 |
| `oleaf compile output` | `chatol.workflows.download_output` | 已实现 |

## 已实现第一版：文件/任务闭环支撑

```text
oleaf files
├── list <project>
├── zip <project> -o <zip>
├── pull <project> <dir> [--force]
├── upload <project> <local-path> [--remote-path <name>]
└── delete <project> <remote-path> --apply
```

要求：

- 每个命令背后必须有可 import 的 Python 函数。
- `pull` 默认不覆盖本地文件；覆盖必须显式 `--force`。
- `pull` 必须拒绝 zip-slip 路径逃逸。
- `upload` 当前只支持项目根目录文件；嵌套目录和自动建目录进入后续增量。
- `delete` 当前只删除 `doc`/`file`，不删除文件夹，并且必须显式 `--apply`。
- 项目页缺失 `rootFolder` metadata 时，client 使用 Socket.IO 项目树回退解析来获取根目录和文件 ID。
- 报告里脱敏项目 ID、entity ID 和内部 URL。

## 未实现：后续文件操作

```text
oleaf files
├── tree <project>
├── download <project> <remote-path> -o <local-path>
└── rename <project> <old-path> <new-name>
```

重命名必须返回结构化 before/after 结果。

## 未实现：计划中的安全同步

```text
oleaf sync
├── plan <project> <dir>
├── pull <project> <dir>
├── push <project> <dir> --apply
└── sync <project> <dir> --no-delete 默认开启
```

要求：

- `plan` 是默认安全入口。
- 删除默认不执行。
- 冲突报告必须可 JSON 序列化。
- ignore 规则覆盖 LaTeX 产物、临时文件和项目本地 ignore 文件。

## 未实现：计划中的管理员和用户管理

```text
oleaf admin
├── doctor
├── users list/get
├── users create/invite
├── users set-password --password-stdin
├── users disable/enable
├── users delete --apply --transfer-projects-to <user>
├── projects list-all
└── projects transfer <project> --to <user> --apply
```

管理员能力必须单独做路由、权限和版本探测，不能假定 Overleaf 管理员 API 稳定可用，也不能默认直接写 Mongo。

## 不纳入第一版的能力

- 自动修改 LaTeX 源码并回写 Overleaf。
- 评论和协作线程管理。
- Overleaf 服务部署、升级、备份本身。
- 不受保护的破坏性操作。
