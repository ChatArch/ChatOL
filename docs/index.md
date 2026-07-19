# ChatOL 文档

ChatOL 是 ChatArch 的 Overleaf 工作流 CLI/API 包。它面向自托管 Overleaf，把登录、项目发现、编译、PDF/日志等产物下载封装成可 import 的 Python API，并提供薄 CLI `oleaf` 方便 Agent 和脚本调用。

站点入口：<https://arch.gh.wzhecnu.cn/ChatOL/>

## 按场景选择文档

| 场景 | 文档 |
| --- | --- |
| 第一次安装、配置 Overleaf 连接并跑通 `oleaf doctor` | [安装与配置](overleaf-quickstart.md) |
| 了解自托管 Overleaf、Docker/Toolkit、内网入口和连接边界 | [部署与连接边界](overleaf-service-operations.md) |
| 让 Agent 拉取、修改、上传并编译 Overleaf 项目 | [Agent 任务闭环](agent-overleaf-flow.md) |
| 编译论文、下载 PDF 或读取日志 | [编译与产物](compile-flow-quickstart.md) |
| 查当前 CLI 命令、参数、安全约束和示例 | [CLI 实战指南](cli-guide.md) |
| 从 Python 代码直接调用 ChatOL | [Python 接口树](interface-tree.md) |
| 快速看已实现/未实现的 CLI 能力边界 | [CLI 能力地图](chatol-cli-tree.md) |
| 看后续文件操作、同步、管理员和用户管理路线 | [开发计划](development-plan.md) |

## 文档栏目组织

当前文档借鉴 ChatTea 的 MkDocs 设定层：分栏导航、场景入口、Flow 页面、中英文 suffix i18n 和语言切换；栏目本身按 ChatOL 的真实能力拆分，不照抄 ChatTea 的 Gitea/Runner/Actions 分类。

- **快速开始**：安装 ChatOL、配置 ChatEnv/环境变量，并验证 Overleaf 连接。
- **Overleaf 连接**：已探索。记录自托管 Overleaf 的部署形态、连接入口、凭据和安全边界；ChatOL 本身不是部署器。
- **论文编译 Flow**：说明项目拉取、单文件上传、编译、PDF/log 产物下载和日志反馈边界。
- **CLI / API**：记录当前 `oleaf` 命令树和 `chatol` Python API 映射。
- **路线图**：记录未实现能力的规划和保护要求。

## CLI

```bash
python -m pip install -U ChatOL
oleaf --help
oleaf doctor --json
```

当前命令树：

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

完整说明见 [CLI 实战指南](cli-guide.md)。所有实质命令都应调用 `chatol.workflows` 或 `chatol.client.OverleafClient` 中的可导入 API；CLI 只负责参数解析、stdin 凭据读取和 JSON/文本输出。

## ChatEnv 字段

ChatOL 的 ChatEnv target 是 `overleaf`。配置键复用 Overleaf 命名空间，不维护 `CHATOL_*` 平行兼容入口。

```text
OVERLEAF_SITE_URL
OVERLEAF_ADMIN_EMAIL
OVERLEAF_ADMIN_PASSWORD
OVERLEAF_SESSION_COOKIE
OVERLEAF_SESSION_COOKIE_NAME
OVERLEAF_HTTP_TIMEOUT
```

配置优先级是：显式 CLI/Python 参数 > 当前进程环境变量 > active ChatEnv `overleaf` profile。

## 本地预览

```bash
python -m pip install -e ".[docs]"
mkdocs serve
```

英文首页见站点语言入口：<https://arch.gh.wzhecnu.cn/ChatOL/en/>。缺少英文翻译的专题页会按 i18n 回退机制显示中文页面。
