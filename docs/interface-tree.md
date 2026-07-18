# 接口树

ChatOL 的实现顺序是 Python API first、CLI thin wrapper。这个页面列出当前可直接 import 的接口，以及它们和 CLI 的关系。

## 包入口

```python
from chatol import CompileOutput, CompileResult, OverleafClient, Project, __version__
```

## `chatol.client.OverleafClient`

```text
OverleafClient
├── from_password(base_url, email, password, timeout=30.0)
├── from_session_cookie(base_url, session_cookie, cookie_name="overleaf_session2", timeout=30.0)
├── session_cookie(cookie_name="overleaf_session2")
├── list_projects()
├── get_project(project)
├── compile_project(project_id)
├── compile_project_by_name(project)
├── download_pdf(project_id)
├── download_output(project_id, output_type)
└── download_compile_output(output, result=None)
```

使用示例：

```python
from chatol.client import OverleafClient

client = OverleafClient.from_password(
    "https://overleaf.example.com",
    "<email>",
    "<password>",
)
projects = client.list_projects()
project = client.get_project(projects[0].name)
result = client.compile_project(project.id)
```

## `chatol.workflows`

Workflow 函数负责把配置解析、重试、文件写入和 CLI 复用逻辑集中起来。

```text
client_from_env(
  base_url=None,
  email=None,
  password=None,
  session=None,
  cookie_name=None,
  timeout=None,
  chatarch_home=None,
)
list_projects(client=None, **client_kwargs)
get_project(project, client=None, **client_kwargs)
compile_project(project, client=None, retry_delays=(0, 20, 45), sleep=time.sleep, **client_kwargs)
download_pdf(project, output_path, client=None, retry_delays=(0, 20, 45), sleep=time.sleep, **client_kwargs)
download_output(project, output_type, output_path, client=None, retry_delays=(0, 20, 45), sleep=time.sleep, **client_kwargs)
```

使用示例：

```python
from pathlib import Path
from chatol.workflows import download_output, download_pdf, list_projects

projects = list_projects()
pdf = download_pdf(projects[0].name, Path("output.pdf"))
log = download_output(projects[0].name, "log", Path("output.log"))
```

## `chatol.config.OverleafConfig`

ChatEnv provider：

```text
target: overleaf
storage dir: Overleaf
entry point: chatenv.configs / overleaf = chatol.config
```

字段：

```text
OVERLEAF_SITE_URL
OVERLEAF_ADMIN_EMAIL
OVERLEAF_ADMIN_PASSWORD
OVERLEAF_SESSION_COOKIE
OVERLEAF_SESSION_COOKIE_NAME
OVERLEAF_HTTP_TIMEOUT
```

## 数据模型

```text
Project
├── id
├── name
├── archived
├── trashed
└── to_dict(include_private=False)

CompileResult
├── status
├── output_files
├── compile_group
├── clsi_server_id
├── pdf_output()
├── find_output(output_type)
└── to_dict(include_urls=False)

CompileOutput
├── type
├── path
├── url
└── to_dict(include_url=False)
```

默认 `to_dict()` 不输出 private owner/updater metadata，也不输出 compile output URL。调用方只有在明确需要内部调试信息时才应打开 include 参数，并且不能把结果原样写进公开文档或日志。

## CLI 映射

```text
oleaf doctor          -> client_from_env + OverleafClient.list_projects
oleaf projects list   -> list_projects
oleaf projects info   -> get_project
oleaf compile run     -> compile_project
oleaf compile pdf     -> download_pdf
oleaf compile output  -> download_output
```
