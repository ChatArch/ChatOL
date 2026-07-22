# Agent 使用 Overleaf 的任务闭环

这篇教程说明如何用 ChatOL 把 Overleaf 项目接入本地 Agent 工作流。核心思路是：从 Overleaf 拉取项目源码到本地任务目录，Agent 只修改本地文件，然后把明确选择的文件上传回 Overleaf，再触发远端编译并下载产物。

## 工作流

```text
本地任务目录
├── source/      # 从 Overleaf 拉取的源码
├── artifacts/   # PDF、log、bbl、aux 等编译产物
└── notes/       # 本地任务说明或诊断笔记，不上传到 Overleaf
```

推荐流程：

1. 用 `files pull` 获取远端项目源码；
2. Agent 在 `source/` 内修改 LaTeX、bib 或资源文件；
3. 用 `files upload` 上传明确选择的根目录文件；
4. 用 `compile run` 触发 Overleaf 编译；
5. 用 `compile pdf` 和 `compile output` 下载 PDF 与日志；
6. 根据日志继续修改，直到编译结果满足任务要求。

如果是新文章，可以先用模板命令生成本地入口文件，再上传到 Overleaf 项目。

## 初始化模板

```bash
oleaf templates list --json
oleaf templates init article-basic ./source --json
oleaf templates upload "<project-name>" ./source --json
```

模板命令只上传目录根层文件；图片、章节子目录等复杂结构建议先通过 `files pull` 看清远端结构，再分批处理。

## 拉取项目源码

```bash
oleaf files pull "<project-name>" ./source --json
```

默认情况下，`files pull` 不会覆盖本地已有文件。如果确认要刷新本地源码，显式使用 `--force`：

```bash
oleaf files pull "<project-name>" ./source --force --json
```

`files pull` 会检查 zip 内路径，拒绝解压会逃逸到目标目录外的文件。

## 上传单个文件

上传命令用于把本地文件写回 Overleaf 项目根目录，适合修改 `main.tex`、`sample.bib` 这类根目录文件：

```bash
oleaf files upload "<project-name>" ./source/main.tex --remote-path main.tex --json
```

注意：

- `--remote-path` 目前应是根目录文件名，不应包含 `/`。
- 上传命令不是完整同步器，不会自动比较目录差异。
- 如需处理嵌套目录，请先在 Overleaf 中准备好结构，或等同步能力完善后再做批量操作。

## 删除单个文件

删除是受保护操作，必须显式传入 `--apply`。只在明确知道远端路径时使用：

```bash
oleaf files delete "<project-name>" old-note.tex --apply --json
```

当前删除能力只处理 `doc`/`file` 实体，不删除文件夹。建议删除后运行：

```bash
oleaf files list "<project-name>" --json
```

用返回结果确认目标文件已经不存在。

## 编译并下载产物

```bash
oleaf compile run "<project-name>" --json
oleaf compile pdf "<project-name>" -o ./artifacts/output.pdf --json
oleaf compile output "<project-name>" log -o ./artifacts/output.log --json
oleaf compile bundle "<project-name>" -o ./artifacts --json
```

`compile pdf` 和 `compile output` 会在 workflow 层处理 Overleaf 编译冷却和可重试错误。默认 JSON 输出不会暴露内部编译 URL。

## Python 调用

同一套能力也可以直接从 Python 调用：

```python
from pathlib import Path
from chatol.workflows import download_compile_bundle, pull_project, upload_file

project_name = "<project-name>"

pull_project(project_name, Path("source"))
upload_file(project_name, Path("source/main.tex"), remote_path="main.tex")
download_compile_bundle(project_name, Path("artifacts"))
```

## 安全边界

- 密码、session cookie、真实服务 URL 和内部 build URL 不应写入仓库或公开文档。
- `files pull` 默认不覆盖本地文件；覆盖必须显式 `--force`。
- `files upload` 当前只支持根目录单文件上传。
- `files delete` 必须显式 `--apply`，且不删除文件夹。
- 当 Overleaf 项目页缺少 `rootFolder` 元数据时，ChatOL 会通过 Socket.IO 项目树解析根目录和文件 ID。
- ChatOL 不是完整同步器；不要把 `files upload` 当作批量同步命令使用。
