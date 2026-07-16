<div align="center">
    <a href="https://pypi.python.org/pypi/ChatOL">
        <img src="https://img.shields.io/pypi/v/ChatOL.svg" alt="PyPI version" />
    </a>
    <a href="https://github.com/ChatArch/ChatOL/actions/workflows/ci.yml">
        <img src="https://github.com/ChatArch/ChatOL/actions/workflows/ci.yml/badge.svg" alt="Tests" />
    </a>
    <a href="https://arch.gh.wzhecnu.cn/ChatOL/">
        <img src="https://img.shields.io/badge/docs-mkdocs-blue.svg" alt="Documentation" />
    </a>
</div>

<div align="center">

[English](README.en.md) | [简体中文](README.md)
</div>

# ChatOL

ChatOL: Python client and CLI for Overleaf workflows

## 快速开始

```bash
pip install -e ".[dev]"
chatol --help
chatol --version
python -m pytest -q
python -m build
```

## Overleaf CLI 示例

CLI 只做薄封装；对应能力也可以从 `chatol.workflows` 和 `chatol.client.OverleafClient` 直接 import 调用。

```bash
export CHATOL_BASE_URL="https://overleaf.example.com"
export CHATOL_EMAIL="<email>"
export CHATOL_PASSWORD="<password>"

chatol doctor --json
chatol projects list --json
chatol projects info "<project-name>" --json
chatol compile run "<project-name>" --json
chatol compile pdf "<project-name>" -o output.pdf --json
chatol compile output "<project-name>" log -o output.log --json
```

密码和 session cookie 也可以通过 `--password-stdin` / `--session-stdin` 传入，避免出现在 shell history 或进程参数里。

## CLI 规范

这个模板默认依赖 `chatstyle>=0.1.0,<0.2.0` 和 `chatenv>=0.2.0,<0.3.0`，新的命令应优先使用：

- `CommandSchema` / `CommandField` 描述输入。
- `add_interactive_option()` 提供统一 `-i/-I`。
- `resolve_command_inputs()` 统一缺参补问、默认值、TTY 与校验。
- 默认生成 `config.py` 和 `chatenv.configs` entry point，使包可被 ChatEnv 发现；只有明确不需要 ChatEnv 接入时才使用 `--without-chatenv-provider`。

## 目录结构

- `src/`：包源码
- `tests/code-tests/`：代码测试和历史测试迁移
- `tests/cli-tests/`：真实 CLI 测试，doc-first
- `tests/mock-cli-tests/`：mock/fake CLI 测试，doc-first
- `docs/`：长期维护文档，由 mkdocs 构建

## 开发说明

扩展脚手架前，先阅读 `DEVELOP.md` 和 `AGENTS.md`。
