# CLI 能力地图

这篇文档给出 ChatOL 当前 CLI 能力、对应 Python API 和后续规划边界。完整命令示例见 [CLI 实战指南](cli-guide.md)。

## 当前可用命令

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
├── templates
│   ├── list
│   ├── init <template> <dir>
│   └── upload <project> <dir>
├── compile
│   ├── run <project>
│   ├── pdf <project> -o <path>
│   ├── output <project> <output-type> -o <path>
│   └── bundle <project> -o <dir>
└── admin
    └── doctor
```

| CLI | Python API | 说明 |
| --- | --- | --- |
| `oleaf doctor` | `client_from_env`, `OverleafClient.list_projects` | 验证配置和项目列表访问 |
| `oleaf projects list` | `chatol.workflows.list_projects` | 列出当前会话可见项目 |
| `oleaf projects info` | `chatol.workflows.get_project` | 按项目名或 ID 解析项目 |
| `oleaf files list` | `chatol.workflows.list_files` | 列出远端文件实体 |
| `oleaf files zip` | `chatol.workflows.download_project_zip` | 下载项目 zip |
| `oleaf files pull` | `chatol.workflows.pull_project` | 下载并安全解压项目 zip |
| `oleaf files upload` | `chatol.workflows.upload_file` | 上传根目录单文件 |
| `oleaf files delete` | `chatol.workflows.delete_file` | 受保护删除远端单文件，必须 `--apply` |
| `oleaf templates list` | `chatol.workflows.list_templates` | 列出内置本地模板 |
| `oleaf templates init` | `chatol.workflows.write_template` | 把模板写到本地目录 |
| `oleaf templates upload` | `chatol.workflows.upload_template` | 上传模板目录根层文件 |
| `oleaf compile run` | `chatol.workflows.compile_project` | 触发远端编译 |
| `oleaf compile pdf` | `chatol.workflows.download_pdf` | 编译并下载 PDF |
| `oleaf compile output` | `chatol.workflows.download_output` | 编译并下载指定产物 |
| `oleaf compile bundle` | `chatol.workflows.download_compile_bundle` | 编译一次并下载多个常用产物 |
| `oleaf admin doctor` | `chatol.workflows.admin_status` | 只读探测管理员入口 |

## 文件命令边界

- `files pull` 默认不覆盖本地文件；覆盖必须显式 `--force`。
- `files pull` 拒绝 zip-slip 路径逃逸。
- `files upload` 当前只支持项目根目录文件；嵌套目录和自动建目录属于后续能力。
- `files delete` 当前只删除 `doc`/`file`，不删除文件夹，并且必须显式 `--apply`。
- 项目页缺失 `rootFolder` metadata 时，client 使用 Socket.IO 项目树回退解析来获取根目录和文件 ID。
- 默认 JSON 输出不包含内部编译 URL、项目所有者/更新者元数据。
- `templates upload` 只上传模板目录根层文件，不做嵌套目录同步。
- `admin doctor` 只读探测，不创建、禁用或删除用户。

## 规划中的文件操作

```text
oleaf files
├── tree <project>
├── download <project> <remote-path> -o <local-path>
└── rename <project> <old-path> <new-name>
```

要求：

- `tree` 应在 `/entities` 不可用时复用项目树回退解析。
- `download` 应按远端路径精确定位文件。
- `rename` 应返回结构化 before/after 结果。

## 规划中的安全同步

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
- 冲突信息必须可 JSON 序列化。
- ignore 规则覆盖 LaTeX 产物、临时文件和项目本地 ignore 文件。

## 规划中的管理员和用户管理

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

## 不纳入当前版本的能力

- 自动修改 LaTeX 源码并回写 Overleaf。
- 评论和协作线程管理。
- Overleaf 服务部署、升级、备份本身。
- 不受保护的破坏性操作。
