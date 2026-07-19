# olcli 对照参考

`olcli` 是当前 ChatOL 设计的重要参考，但 ChatOL 不直接照抄完整命令树。ChatOL 的原则是 Python 接口优先、命令行薄封装，并且优先服务 Agent 任务闭环。

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

| 组 | olcli 能力 | 在自托管实例上的实践结果 | ChatOL 处理 |
| --- | --- | --- | --- |
| 认证 / 配置 | cookie、email/password、base URL、cookie name、timeout | 可用；`check` 输出需脱敏 | ChatOL 走 `OVERLEAF_*` / ChatEnv `overleaf`，不保存明文密码到仓库 |
| 项目 | list/info | 可用 | 已实现 |
| 项目归档 | pull/zip | 可用 | 第一版补 `files zip` / `files pull` |
| 编译 | compile/pdf/output | 可用；过快重复编译可能 too-recently-compiled | 已实现重试和冷却处理 |
| 文件操作 | upload/download/rename/delete | 单文件实践可用 | 第一版补根目录单文件上传和受保护删除；download/rename 后续 |
| 同步 | push/sync dry-run/ignore | dry-run 可用；真实同步的删除风险高 | 先做 `sync plan`，后续再 `--apply` |
| 评论 | comments list/add/reply/resolve | 当前自托管实例不兼容，内部路由失败 | 暂缓，不写成已可用 |
| MCP / git 辅助 | olcli-mcp、git-remote-overleaf | 可作为远期参考 | 不进入 ChatOL 第一阶段 |

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

- `olcli` 是宽 CLI：认证、同步、评论、MCP、git 辅助都在同一个 npm 包里。
- ChatOL 先做窄核心：项目发现、文件拉取、明确文件上传、受保护清理、远端编译、产物收集。
- ChatOL 不在第一版做破坏性 sync；所有删除/覆盖类能力都需要显式 `--apply` 或 `--force`。
- ChatOL 的每个 CLI 命令必须对应可 import 的 Python API，方便 Agent/skill 直接调用。
- 本次真实实践发现当前自托管实例的项目 HTML 不暴露 `rootFolder`，因此 ChatOL 也吸收了 `olcli` 的项目树回退解析思路：通过 Socket.IO `joinProjectResponse` 解析根目录和 doc/file ID。
