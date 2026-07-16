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

## Quick Start

```bash
pip install -e ".[dev]"
oleaf --help
oleaf --version
python -m pytest -q
python -m build
```

## Overleaf CLI Example

The CLI is a thin wrapper; the same behavior can be imported from `chatol.workflows` and `chatol.client.OverleafClient`.

Configuration can come from process environment variables or the active ChatEnv `overleaf` profile. Configuration keys reuse official Overleaf names where they exist, such as `OVERLEAF_SITE_URL` and `OVERLEAF_ADMIN_EMAIL`; password, session, and HTTP timeout extras also stay in the `OVERLEAF_*` namespace instead of adding a parallel `CHATOL_*` set. The examples use placeholders; pass real passwords through `chatenv paste --stdin`, a private profile, environment variables, or `--password-stdin` instead of shell history.

```bash
export OVERLEAF_SITE_URL="https://overleaf.example.com"
export OVERLEAF_ADMIN_EMAIL="<email>"
export OVERLEAF_ADMIN_PASSWORD="<password>"

oleaf doctor --json
oleaf projects list --json
oleaf projects info "<project-name>" --json
oleaf compile run "<project-name>" --json
oleaf compile pdf "<project-name>" -o output.pdf --json
oleaf compile output "<project-name>" log -o output.log --json
```

Passwords and session cookies can also be passed with `--password-stdin` / `--session-stdin` so they do not appear in shell history or process arguments.

## CLI Contract

This template depends on `chatstyle>=0.1.0,<0.2.0` and `chatenv>=0.2.2,<0.3.0`. New commands should prefer:

- `CommandSchema` / `CommandField` for inputs.
- `add_interactive_option()` for the shared `-i/-I` switch.
- `resolve_command_inputs()` for missing args, defaults, TTY behavior, and validation.
- Generate `config.py` and a `chatenv.configs` entry point by default so the package is ChatEnv-discoverable; use `--without-chatenv-provider` only when ChatEnv integration is intentionally not needed.

## Layout

- `src/`: package source code
- `tests/code-tests/`: code tests and migrated historical tests
- `tests/cli-tests/`: real CLI tests, doc-first
- `tests/mock-cli-tests/`: mock/fake CLI tests, doc-first
- `docs/`: long-lived project docs built by mkdocs

## Development Notes

See `DEVELOP.md` and `AGENTS.md` before expanding the scaffold.
