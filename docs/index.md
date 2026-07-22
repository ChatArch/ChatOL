# ChatOL 文档

ChatOL 是 ChatArch 的 Overleaf 工作流 CLI/API 包。它面向自托管 Overleaf，把项目发现、源码拉取、单文件上传、远端编译、PDF/日志下载封装成可 import 的 Python API，并提供薄 CLI `oleaf` 方便 Agent 和脚本调用。

## 从这里开始

| 你要做什么 | 入口 |
| --- | --- |
| 安装 ChatOL 并连接 Overleaf | [快速开始](overleaf-quickstart.md) |
| 了解 Overleaf 服务入口、Docker/Toolkit 和安全边界 | [部署与连接边界](overleaf-service-operations.md) |
| 让 Agent 拉取、修改、上传并编译 Overleaf 项目 | [Agent 任务闭环](agent-overleaf-flow.md) |
| 只需要编译项目并下载 PDF 或日志 | [编译与产物](compile-flow-quickstart.md) |
| 查 `oleaf` 命令、参数和示例 | [CLI 实战指南](cli-guide.md) |
| 从 Python 代码调用 ChatOL | [Python 接口树](interface-tree.md) |
| 查看已经开放的能力和安全限制 | [CLI 能力地图](chatol-cli-tree.md) |
| 查看后续计划中的能力边界 | [功能路线图](development-plan.md) |

## 最小命令

```bash
python -m pip install -U ChatOL
oleaf --help
oleaf doctor --json
```

常用命令树：

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

## 配置来源

ChatOL 的 ChatEnv target 是 `overleaf`。配置键复用 Overleaf 命名空间，不维护 `CHATOL_*` 平行入口。

```text
OVERLEAF_SITE_URL
OVERLEAF_ADMIN_EMAIL
OVERLEAF_ADMIN_PASSWORD
OVERLEAF_SESSION_COOKIE
OVERLEAF_SESSION_COOKIE_NAME
OVERLEAF_HTTP_TIMEOUT
```

配置优先级：显式 CLI/Python 参数 > 当前进程环境变量 > active ChatEnv `overleaf` profile。

## 本地预览文档

```bash
python -m pip install -e ".[docs]"
mkdocs serve
```

英文首页见 <https://arch.gh.wzhecnu.cn/ChatOL/en/>。缺少英文翻译的专题页会按 i18n 回退机制显示中文页面。
