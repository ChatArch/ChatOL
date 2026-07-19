# ChatOL 开发计划

## 评审合约

ChatOL 开发遵循这些评审规则：

- 每个 CLI 命令都必须是可 import Python 函数或类方法的薄封装。
- 核心行为放在 `chatol.client` 和 `chatol.workflows`，不要塞进 Click 命令体。
- CLI 命令必须支持面向 Agent 的机器可读 JSON 输出。
- 密钥不能作为位置参数传递；优先使用 stdin、环境变量或私有 profile 存储。
- 破坏性操作必须默认只做 dry-run，或要求显式 `--apply`。
- 公开文档、日志和 issue/PR 评论必须脱敏邮箱、密码、session cookie、build URL、内部项目 ID 和用户 ID。
- 测试要同时覆盖可 import 函数和 CLI 包装层。

## 阶段 1：原生读取与编译核心

第一阶段已经实现并验证的范围：

```text
oleaf
├── Python API
│   ├── OverleafClient.from_password
│   ├── OverleafClient.from_session_cookie
│   ├── OverleafClient.list_projects
│   ├── OverleafClient.get_project
│   ├── OverleafClient.compile_project
│   ├── OverleafClient.download_pdf
│   └── OverleafClient.download_output
├── workflow 函数
│   ├── client_from_env
│   ├── list_projects
│   ├── get_project
│   ├── compile_project
│   ├── download_pdf
│   └── download_output
└── CLI 薄封装
    ├── oleaf doctor
    ├── oleaf projects list
    ├── oleaf projects info <project>
    ├── oleaf compile run <project>
    ├── oleaf compile pdf <project> -o <path>
    └── oleaf compile output <project> <type> -o <path>
```

设计取舍：

- 优先使用 Python 标准库 HTTP 能力，保持依赖面小。
- 复用 Overleaf 官方配置命名：`OVERLEAF_SITE_URL` 和 `OVERLEAF_ADMIN_EMAIL` 来自 Overleaf 部署语义；ChatOL 补充字段如 `OVERLEAF_ADMIN_PASSWORD`、`OVERLEAF_SESSION_COOKIE`、`OVERLEAF_HTTP_TIMEOUT` 也放在同一命名空间，不增加 `CHATOL_*` 平行别名。
- 从 Overleaf HTML meta 标签解析项目元数据。
- CLI 默认不输出内部编译 URL。
- 编译冷却和重试放在 workflow 函数里，不放在 CLI 调用者里。

## 阶段 2：文件操作

当前已提供第一批 Agent 任务闭环所需的文件能力：

```text
oleaf files
├── list <project>
├── zip <project> -o <zip>
├── pull <project> <dir> [--force]
├── upload <project> <local-path> [--remote-path <path>]
└── delete <project> <remote-path> --apply
```

已实现约束：

- 所有命令都调用可 import 函数。
- `pull` 默认不覆盖本地文件，覆盖必须显式 `--force`。
- `pull` 拒绝 zip-slip 路径逃逸。
- `upload` 当前只支持项目根目录文件。
- `delete` 只删除 `doc`/`file`，不删除文件夹，并且必须显式 `--apply`。
- 项目 HTML 缺少 `rootFolder` 时，client 会使用 Socket.IO 项目树回退解析。
- 报告脱敏项目 ID 和内部实体 ID。

后续文件能力：

```text
oleaf files
├── tree <project>
├── download <project> <remote-path> -o <local-path>
└── rename <project> <old-path> <new-name>
```

后续要求：

- 上传、删除、重命名要返回结构化 before/after 结果。
- 单文件下载要优先通过实体 ID 读取；必要时再从 zip 中提取。
- 嵌套目录上传要先实现目录树发现和缺失目录创建。

## 阶段 3：安全同步计划

```text
oleaf sync
├── plan <project> <dir>
├── push <project> <dir> --apply
├── pull <project> <dir>
└── sync <project> <dir> --no-delete 默认开启
```

要求：

- `plan` 是默认安全入口。
- 删除永远不能默认执行，必须由用户显式请求。
- ignore 规则要覆盖 LaTeX 编译产物和项目本地 ignore 文件。
- 冲突报告必须能序列化成 JSON。

## 阶段 4：管理员和用户管理

管理员能力与普通项目 workflow 分离。

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

管理员能力前置条件：

- 检测当前 session 是否真的具备管理员权限。
- 变更操作前探测管理员路由和 Overleaf 版本兼容性。
- 使用 `--password-stdin`，不要使用密码命令参数。
- 所有变更操作使用 dry-run 和幂等设计。
- 输出审计事件时脱敏目标标识符。

## 实现流程

每个阶段按这个顺序推进：

1. 增加或调整可 import Python API。
2. 增加 CLI 薄封装。
3. 增加 parser、client、workflow 的单元测试。
4. 在受控 Overleaf 环境中验证新命令。
5. 把验证记录保存到本地任务报告，不写入公开 MkDocs。
6. 把验证发现回写到下一轮实现切片。
