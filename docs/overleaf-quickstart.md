# Overleaf 快速开始

这篇教程带你从零开始配置 ChatOL，并用 `oleaf` 连接一个自托管 Overleaf 实例。完成后，你可以列出项目、编译项目、下载 PDF 和日志。

## 前置条件

- 一台能访问 Overleaf Web 服务的机器。
- 一个可登录 Overleaf 的账号，或一个有效的 Overleaf session cookie。
- Python 3.10+。

ChatOL 不部署 Overleaf；如果还没有 Overleaf 服务，请先看 [部署与连接边界](overleaf-service-operations.md)。

## 1. 安装

从 PyPI 安装：

```bash
python -m pip install -U ChatOL
oleaf --version
```

从源码安装：

```bash
git clone https://github.com/ChatArch/ChatOL.git
cd ChatOL
python -m pip install -e ".[dev,docs]"
```

## 2. 配置连接

最直接的方式是使用环境变量：

```bash
export OVERLEAF_SITE_URL="https://overleaf.example.com"
export OVERLEAF_ADMIN_EMAIL="<email>"
export OVERLEAF_ADMIN_PASSWORD="<password>"
export OVERLEAF_HTTP_TIMEOUT=45
```

如果你已经有浏览器或服务端会话，也可以使用 session cookie：

```bash
export OVERLEAF_SITE_URL="https://overleaf.example.com"
export OVERLEAF_SESSION_COOKIE="<session-cookie>"
export OVERLEAF_SESSION_COOKIE_NAME="overleaf_session2"
```

也可以通过 ChatEnv 保存当前环境的 `overleaf` profile：

```bash
python -m chatenv.cli init -t overleaf -I
python -m chatenv.cli set OVERLEAF_SITE_URL=https://overleaf.example.com
python -m chatenv.cli paste OVERLEAF_ADMIN_EMAIL --stdin
python -m chatenv.cli paste OVERLEAF_ADMIN_PASSWORD --stdin
python -m chatenv.cli test -t overleaf -I
```

不要把真实密码、cookie、token 或内部项目 ID 写进 shell history、README、issue 或 PR。

## 3. 检查连接

```bash
oleaf doctor --json
```

`doctor` 会检查当前配置能否访问项目列表。它不会修改 Overleaf 项目。

如果成功，可以继续列出项目：

```bash
oleaf projects list --json
```

## 4. 编译项目

项目参数可以是项目名或项目 ID。自动化脚本中建议优先使用项目 ID，避免同名项目造成歧义。

```bash
oleaf projects info "<project-name>" --json
oleaf compile run "<project-name>" --json
oleaf compile pdf "<project-name>" -o output.pdf --json
oleaf compile output "<project-name>" log -o output.log --json
```

如果想一次拿到 PDF 和日志，可以用 bundle 命令：

```bash
oleaf compile bundle "<project-name>" -o ./artifacts --json
```

需要同时保存项目源码 zip 时加上：

```bash
oleaf compile bundle "<project-name>" -o ./artifacts --include-source-zip --json
```

## 5. 使用模板

查看内置模板：

```bash
oleaf templates list --json
```

把模板写到本地目录：

```bash
oleaf templates init article-basic ./template --json
```

把模板根目录文件上传到 Overleaf 项目：

```bash
oleaf templates upload "<project-name>" ./template --json
```

模板上传只处理模板目录根层文件，不做嵌套目录同步。

## 6. 拉取和上传文件

把 Overleaf 项目拉到本地目录：

```bash
oleaf files pull "<project-name>" ./source --json
```

修改本地文件后，上传一个根目录文件：

```bash
oleaf files upload "<project-name>" ./source/main.tex --remote-path main.tex --json
```

删除远端文件需要显式确认：

```bash
oleaf files delete "<project-name>" old-note.tex --apply --json
```

更多说明见 [Agent 任务闭环](agent-overleaf-flow.md)。

## 7. Python 调用

```python
from pathlib import Path
from chatol.workflows import download_compile_bundle, list_projects, write_template

projects = list_projects()
write_template("article-basic", Path("template"))
bundle = download_compile_bundle(projects[0].id, Path("artifacts"))
```

## 常见问题

| 问题 | 处理方式 |
| --- | --- |
| `doctor` 无法登录 | 检查 `OVERLEAF_SITE_URL`、账号密码、cookie 名称和 cookie 是否过期 |
| 项目名找不到 | 先用 `oleaf projects list --json` 确认名称；脚本中优先使用项目 ID |
| 拉取目录已有文件 | 默认不会覆盖；确认安全后加 `--force` |
| 上传嵌套路径失败 | 当前只支持根目录单文件上传 |
| 模板上传后覆盖了远端文件 | 上传前先用 `oleaf files list` 检查远端文件名 |
| 删除文件失败 | 确认路径是文件而不是文件夹，并且命令包含 `--apply` |
