# olcli 对照参考

`olcli` 是当前 ChatOL 设计的重要参考，但 ChatOL 不直接照抄完整命令树。ChatOL 的原则是 Python API first、CLI thin wrapper，并且优先服务 Agent 任务闭环。

## olcli 命令树

本地参考版本：`@aloth/olcli` `0.7.0`。

```text
olcli
├── auth
│   ├── --cookie <session>
│   ├── --email <email>
│   ├── --password <password>
│   ├── --no-save-password
│   └── --save-local
├── whoami
├── logout
├── list | ls
│   ├── --json
│   └── -n, --limit <n>
├── info [project]
│   └── --json
├── comments
│   ├── list [project]
│   ├── add <file> <message> [project]
│   ├── reply <threadId> <body> [project]
│   ├── resolve <threadId> [project]
│   ├── reopen <threadId> [project]
│   └── delete <threadId> [project]
├── download <file> [project]
├── zip [project]
├── pdf [project]
├── output [type]
│   ├── --list
│   └── --project <name>
├── upload <file> [project]
├── delete | rm <file> [project]
├── rename | mv <oldname> <newname> [project]
├── compile [project]
├── pull [project] [dir]
│   └── --force
├── push [dir]
│   ├── --project <name>
│   ├── --all
│   ├── --dry-run
│   ├── --probe-folder
│   └── ignore controls
├── sync [dir]
│   ├── --project <name>
│   ├── --no-delete
│   ├── --dry-run
│   └── ignore controls
├── config
│   ├── set-url/get-url
│   ├── set-cookie-name/get-cookie-name
│   └── set-timeout/get-timeout
├── ignored [dir]
└── check
```

## olcli 已验证实践

| 组 | olcli 能力 | 在 self-hosted 实例上的实践结果 | ChatOL 处理 |
| --- | --- | --- | --- |
| Auth / Config | cookie、email/password、base URL、cookie name、timeout | 可用；`check` 输出需脱敏 | ChatOL 走 `OVERLEAF_*` / ChatEnv `overleaf`，不保存明文密码到 repo |
| Project | list/info | 可用 | 已实现 |
| Project archive | pull/zip | 可用 | 第一版补 `files zip` / `files pull` |
| Compile | compile/pdf/output | 可用；过快重复编译可能 too-recently-compiled | 已实现 retry/cooldown |
| File CRUD | upload/download/rename/delete | 单文件实践可用 | 第一版只补 root 单文件 upload；download/rename/delete 后续 |
| Sync | push/sync dry-run/ignore | dry-run 可用；真实 sync 删除风险高 | 先做 `sync plan`，后续再 `--apply` |
| Comments | comments list/add/reply/resolve | 当前 self-hosted 实例不兼容，内部 route 失败 | 暂缓，不写成已可用 |
| MCP / git helper | olcli-mcp、git-remote-overleaf | 可作为远期参考 | 不进入 ChatOL 第一阶段 |

## ChatOL 当前命令树

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

## 设计取舍

- `olcli` 是宽 CLI：auth、sync、comments、MCP、git helper 都在同一个 npm 包里。
- ChatOL 先做窄核心：项目发现、文件拉取、明确文件上传、受保护清理、远端编译、产物收集。
- ChatOL 不在第一版做破坏性 sync；所有删除/覆盖类能力都需要显式 `--apply` 或 `--force`。
- ChatOL 的每个 CLI 命令必须对应可 import 的 Python API，方便 Agent/skill 直接调用。
- 本次 live practice 发现当前 self-hosted 实例的项目 HTML 不暴露 `rootFolder`，因此 ChatOL 也吸收了 `olcli` 的 project tree fallback 思路：通过 Socket.IO `joinProjectResponse` 解析 root folder 和 doc/file id。
