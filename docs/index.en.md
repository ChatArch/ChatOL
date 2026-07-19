# ChatOL Docs

ChatOL is ChatArch's Overleaf workflow CLI/API package. It targets self-hosted Overleaf instances and exposes login, project discovery, compilation, PDF downloads, and output artifact downloads as importable Python APIs with a thin `oleaf` CLI for agents and scripts.

## Choose By Scenario

| Scenario | Document |
| --- | --- |
| Install ChatOL, configure an Overleaf connection, and run `oleaf doctor` | [Installation and Configuration](overleaf-quickstart.md) |
| Understand self-hosted Overleaf deployment, Docker/Toolkit, local/public endpoints, and connection boundaries | [Deployment and Connectivity Boundaries](overleaf-service-operations.md) |
| Let an agent pull, edit, upload, and compile an Overleaf project | [Agent Task Loop](agent-overleaf-flow.md) |
| Compile a paper, download a PDF, or read compile logs | [Compile and Artifacts](compile-flow-quickstart.md) |
| Check current CLI commands, parameters, safety rules, and examples | [CLI Guide](cli-guide.md) |
| Call ChatOL directly from Python | [Python Interface Tree](interface-tree.md) |
| See the implemented and planned CLI capability map | [CLI Capability Map](chatol-cli-tree.md) |
| Review the roadmap for files, sync, and admin/user management | [Development Plan](development-plan.md) |

## Documentation Sections

The site borrows ChatTea's MkDocs setup layer: grouped navigation, scenario-based entry points, Flow pages, suffix-based i18n, and language switching. The actual sections are ChatOL-specific and follow the current Overleaf workflow surface instead of copying ChatTea's Gitea/Runner/Actions categories.

- **Quickstart**: install ChatOL, configure ChatEnv/process env values, and verify the Overleaf connection.
- **Overleaf Connectivity**: explored. Document self-hosted Overleaf deployment shape, endpoints, credentials, and safety boundaries; ChatOL itself is not a deployer.
- **Paper Compile Flow**: covers project pull, root-file upload, compilation, PDF/log downloads, and log feedback boundaries.
- **CLI / API**: documents the current `oleaf` command tree and `chatol` Python API mapping.
- **Roadmap**: records planned capabilities and safety requirements.

## CLI

```bash
python -m pip install -U ChatOL
oleaf --help
oleaf doctor --json
```

Current command tree:

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

Every substantial command should call an importable API in `chatol.workflows` or `chatol.client.OverleafClient`. The CLI boundary only handles argument parsing, stdin credential reads, and JSON/text output.

## ChatEnv Fields

ChatOL registers the ChatEnv target as `overleaf`. Configuration keys use the Overleaf namespace; ChatOL does not keep a parallel `CHATOL_*` compatibility path.

```text
OVERLEAF_SITE_URL
OVERLEAF_ADMIN_EMAIL
OVERLEAF_ADMIN_PASSWORD
OVERLEAF_SESSION_COOKIE
OVERLEAF_SESSION_COOKIE_NAME
OVERLEAF_HTTP_TIMEOUT
```

Precedence is: explicit CLI/Python arguments > process environment variables > active ChatEnv `overleaf` profile.

## Local Preview

```bash
python -m pip install -e ".[docs]"
mkdocs serve
```

The Chinese home page is available at <https://arch.gh.wzhecnu.cn/ChatOL/>. Topic pages without English translations fall back to the default Chinese content through the i18n plugin.
