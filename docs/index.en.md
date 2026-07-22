# ChatOL Docs

ChatOL is ChatArch's Overleaf workflow CLI/API package for self-hosted Overleaf. It exposes project discovery, source pulls, template initialization and uploads, remote compilation, and PDF/log downloads as importable Python APIs with a thin `oleaf` CLI for agents and scripts.

## Start Here

| Goal | Entry |
| --- | --- |
| Install ChatOL and connect to Overleaf | [Quickstart](overleaf-quickstart.md) |
| Understand Overleaf service endpoints, Docker/Toolkit, and safety boundaries | [Deployment and Connectivity Boundaries](overleaf-service-operations.md) |
| Let an agent pull, edit, upload, and compile an Overleaf project | [Agent Task Loop](agent-overleaf-flow.md) |
| Compile a project and download a PDF or log | [Compile and Artifacts](compile-flow-quickstart.md) |
| Look up `oleaf` commands, flags, and examples | [CLI Guide](cli-guide.md) |
| Call ChatOL from Python | [Python Interface Tree](interface-tree.md) |
| Review available commands and safety limits | [CLI Capability Map](chatol-cli-tree.md) |
| Review planned capability boundaries | [Feature Roadmap](development-plan.md) |

## Minimal Commands

```bash
python -m pip install -U ChatOL
oleaf --help
oleaf doctor --json
```

Common command tree:

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
├── templates
│   ├── list
│   ├── init <template> <dir>
│   └── upload <project> <dir>
├── compile
│   ├── run <project>
│   ├── pdf <project> -o <path>
│   ├── output <project> <output-type> -o <path>
│   └── bundle <project> -o <dir>
└── admin
    └── doctor
```

## Configuration Sources

ChatOL registers the ChatEnv target as `overleaf`. Configuration keys use the Overleaf namespace; ChatOL does not keep a parallel `CHATOL_*` compatibility path.

```text
OVERLEAF_SITE_URL
OVERLEAF_ADMIN_EMAIL
OVERLEAF_ADMIN_PASSWORD
OVERLEAF_SESSION_COOKIE
OVERLEAF_SESSION_COOKIE_NAME
OVERLEAF_HTTP_TIMEOUT
```

Precedence: explicit CLI/Python arguments > process environment variables > active ChatEnv `overleaf` profile.

## Local Preview

```bash
python -m pip install -e ".[docs]"
mkdocs serve
```

The Chinese home page is available at <https://arch.gh.wzhecnu.cn/ChatOL/>. Topic pages without English translations fall back to the default Chinese content through the i18n plugin.
