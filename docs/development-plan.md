# 功能路线图

这页说明 ChatOL 的能力边界：哪些命令可以直接使用，哪些方向还需要更明确的安全保护后再开放。

## 已开放能力

### 连接和项目发现

```text
oleaf doctor
oleaf projects list
oleaf projects info <project>
```

用途：

- 检查 Overleaf 配置是否可用；
- 列出当前会话可见的项目；
- 用项目名或项目 ID 解析目标项目。

### 编译和产物下载

```text
oleaf compile run <project>
oleaf compile pdf <project> -o <path>
oleaf compile output <project> <type> -o <path>
oleaf compile bundle <project> -o <dir>
```

用途：

- 触发 Overleaf 远端编译；
- 下载 PDF；
- 下载日志、bbl、aux 等编译产物。
- 一次编译后下载多个常用产物。

### 模板

```text
oleaf templates list
oleaf templates init <template> <dir>
oleaf templates upload <project> <dir>
```

用途：

- 查看内置模板；
- 把模板写到本地目录；
- 上传模板目录根层文件到 Overleaf 项目。

### 文件和项目归档

```text
oleaf files list <project>
oleaf files zip <project> -o <zip>
oleaf files pull <project> <dir> [--force]
oleaf files upload <project> <local-path> [--remote-path <name>]
oleaf files delete <project> <remote-path> --apply
```

用途：

- 查看远端文件实体；
- 下载项目 zip；
- 将项目源码安全解压到本地目录；
- 上传根目录单文件；
- 删除远端单文件，且必须显式 `--apply`。

限制：

- `files upload` 只支持根目录文件名；
- `templates upload` 只上传目录根层文件；
- `files delete` 不删除文件夹；
- `files pull` 默认不覆盖本地已有文件；
- ChatOL 不是完整双向同步器。

### 管理员入口探测

```text
oleaf admin doctor
```

用途：

- 只读检查 `/admin` 入口是否可达；
- 判断当前 session 是否具备管理员入口访问能力；
- 为后续用户管理能力确认路由和权限边界。

## 计划开放能力

### 单文件下载和重命名

```text
oleaf files download <project> <remote-path> -o <local-path>
oleaf files rename <project> <old-path> <new-name>
```

开放前需要满足：

- 远端路径解析稳定；
- 重命名返回结构化 before/after 结果；
- 错误输出能区分“文件不存在”“路径是文件夹”“权限不足”。

### 安全同步

```text
oleaf sync plan <project> <dir>
oleaf sync push <project> <dir> --apply
oleaf sync pull <project> <dir>
```

开放前需要满足：

- `plan` 是默认入口，只输出同步计划；
- 真实写入必须显式 `--apply`；
- 删除默认关闭；
- ignore 规则覆盖 LaTeX 编译产物、临时文件和项目本地 ignore 文件；
- 冲突信息能序列化为 JSON，方便 Agent 和 CI 消费。

### 管理员和用户管理

```text
oleaf admin users list
oleaf admin users create
oleaf admin users disable
oleaf admin users delete --apply --transfer-projects-to <user>
oleaf admin projects transfer <project> --to <user> --apply
```

开放前需要满足：

- 复用 `oleaf admin doctor` 的权限和路由探测结果；
- 密码只通过 `--password-stdin` 或私有配置传入；
- 变更操作默认 dry-run 或要求显式 `--apply`；
- 输出中脱敏用户 ID、项目 ID、邮箱和内部 URL。

## 不提供的行为

- 不在 CLI 参数中直接接收明文密码；
- 不默认执行删除、转移、覆盖等破坏性操作；
- 不把 ChatOL 当作 Overleaf 部署器；
- 不直接写 MongoDB 作为常规项目操作方式。
