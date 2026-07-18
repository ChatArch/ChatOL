# Overleaf 快速开始

这篇文档是从一台已经能访问 Overleaf 的机器开始，跑通 ChatOL `oleaf` 的最小路径。它不记录真实域名、账号、密码、cookie 或内部项目 ID。

## 1. 安装 ChatOL

从 PyPI 安装稳定版：

```bash
python -m pip install -U ChatOL
oleaf --version
```

从源码调试：

```bash
git clone https://github.com/ChatArch/ChatOL.git
cd ChatOL
python -m pip install -e ".[dev,docs]"
python -m pytest -q
```

## 2. 配置 Overleaf 连接

ChatOL 支持两类凭据：

1. 邮箱 + 密码：适合受控的服务端 smoke 或管理员维护脚本。
2. 已有 session cookie：适合复用浏览器/服务端已有会话，但要注意过期和权限范围。

### 方式 A：进程环境变量

```bash
export OVERLEAF_SITE_URL="https://overleaf.example.com"
export OVERLEAF_ADMIN_EMAIL="<email>"
export OVERLEAF_ADMIN_PASSWORD="<password>"
export OVERLEAF_HTTP_TIMEOUT=45
```

### 方式 B：ChatEnv active profile

ChatEnv target 是 `overleaf`，不是 `chatol`。

```bash
python -m chatenv.cli init -t overleaf -I
python -m chatenv.cli set OVERLEAF_SITE_URL=https://overleaf.example.com
python -m chatenv.cli paste OVERLEAF_ADMIN_EMAIL --stdin
python -m chatenv.cli paste OVERLEAF_ADMIN_PASSWORD --stdin
python -m chatenv.cli test -t overleaf -I
```

真实密码和 session 应通过 private profile、环境变量或 stdin 传入，不要写进 shell history、README、issue、PR 或报告。

## 3. 运行最小 smoke

```bash
oleaf doctor --json
oleaf projects list --json
```

`doctor` 会验证登录和项目列表访问，并返回可见项目数量。它不会修改 Overleaf 项目。

## 4. 编译一个项目

项目参数可以是项目名或项目 ID。项目名精确匹配；如果同名项目会造成歧义，优先使用项目 ID。

```bash
oleaf projects info "<project-name>" --json
oleaf compile run "<project-name>" --json
oleaf compile pdf "<project-name>" -o output.pdf --json
oleaf compile output "<project-name>" log -o output.log --json
```

## 5. Python 调用

CLI 背后是 `chatol.workflows` 和 `chatol.client.OverleafClient`。

```python
from pathlib import Path
from chatol.workflows import compile_project, download_pdf, list_projects

projects = list_projects()
project, result = compile_project(projects[0].name)
pdf_path = download_pdf(project.name, Path("output.pdf"))
```

## 当前边界

- 已实现：登录/session、项目列表、项目信息、编译、PDF 下载、compile output 下载。
- 未实现：文件树/上传/删除、双向 sync、comments、admin/user management。
- 变更性操作后续必须默认 dry-run 或要求显式 `--apply`。
