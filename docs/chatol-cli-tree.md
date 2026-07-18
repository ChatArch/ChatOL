# CLI 能力地图

这篇文档给出 ChatOL 当前 CLI 能力、已实现 Python API 和后续规划边界。它是较短的能力地图；实战命令和例子见 [CLI 实战指南](cli-guide.md)。

状态约定：

- **已实现**：代码、单测和 CLI 路径已经存在。
- **已验证**：已在 self-hosted Overleaf 上做过脱敏 live practice。
- **未实现**：只记录设计方向和安全要求；等真实实现、测试和 live practice 完成后，再补操作文档。

## 当前已实现并已验证

```text
oleaf
├── doctor
├── projects
│   ├── list
│   └── info <project>
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
| `oleaf compile run` | `chatol.workflows.compile_project` | 已实现 |
| `oleaf compile pdf` | `chatol.workflows.download_pdf` | 已实现 |
| `oleaf compile output` | `chatol.workflows.download_output` | 已实现 |

## 未实现：计划中的文件操作

```text
oleaf files
├── tree <project>
├── download <project> <remote-path> -o <local-path>
├── upload <project> <local-path> [--remote-path <path>]
├── rename <project> <old-path> <new-name>
└── delete <project> <remote-path> --apply
```

要求：

- 每个命令背后必须有 importable Python 函数。
- 上传、删除、重命名返回结构化 before/after 结果。
- 删除必须显式 `--apply`。
- 报告里脱敏 project ID、entity ID 和内部 URL。

## 未实现：计划中的安全同步

```text
oleaf sync
├── plan <project> <dir>
├── pull <project> <dir>
├── push <project> <dir> --apply
└── sync <project> <dir> --no-delete by default
```

要求：

- `plan` 是默认安全入口。
- 删除默认不执行。
- 冲突报告必须可 JSON 序列化。
- ignore 规则覆盖 LaTeX 产物、临时文件和项目本地 ignore 文件。

## 未实现：计划中的 admin/user management

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

Admin 能力必须单独做 route/权限/版本探测，不能假定 Overleaf admin API 稳定可用，也不能默认直接写 Mongo。

## 不纳入第一版的能力

- 自动修改 LaTeX 源码并回写 Overleaf。
- comments/thread 管理。
- Overleaf 服务部署、升级、备份本身。
- 不受保护的破坏性操作。
