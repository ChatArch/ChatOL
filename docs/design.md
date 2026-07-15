# ChatOL Initial API And CLI Design

This document proposes ChatOL's first real implementation direction. It is based on two references:

- the `olcli` command tree and feature surface;
- a localhost-first self-hosted Overleaf deployment behind a reverse proxy.

The current package release is only a scaffold. Feature work should start with a small, testable auth and project-list milestone.

## Product Positioning

ChatOL is a Python package for working with Overleaf-like workflows from agents, scripts, and terminals.

Primary surfaces:

- importable Python client API;
- thin `chatol` CLI;
- ChatEnv-backed credential/profile management;
- later optional integrations such as MCP or research-agent workflows.

## Non-Goals For The First Implementation

- Do not clone the entire `olcli` feature set at once.
- Do not manage Docker deployment from the core project API.
- Do not put real service URLs, cookies, passwords, or account emails in repository docs.
- Do not assume Overleaf exposes a stable full public REST API.

## Package Architecture

```text
chatol
├── client.py        # session, request, CSRF, base URL handling
├── auth.py          # cookie auth, password login, credential persistence adapters
├── projects.py      # list, info, create helpers
├── files.py         # tree, upload, download, delete, rename
├── sync.py          # manifest, pull, push, sync
├── compile.py       # compile trigger, PDF/log/output artifacts
├── comments.py      # later-stage comment workflows
├── config.py        # ChatEnv config schema
└── cli.py           # thin CLI wrapper
```

The Python API should be usable without invoking the CLI.

## Configuration Model

ChatEnv fields should be explicit and self-hosted friendly.

```text
CHATOL_BASE_URL              # e.g. https://<public-overleaf-host>
CHATOL_SESSION_COOKIE        # sensitive session cookie value
CHATOL_SESSION_COOKIE_NAME   # e.g. overleaf.sid or another deployment-specific name
CHATOL_EMAIL                 # optional login email
CHATOL_PASSWORD              # sensitive password, optional
CHATOL_TIMEOUT_MS            # request timeout
CHATOL_PROFILE               # optional profile name
```

Rules:

- sensitive values are never logged;
- repository docs use placeholders only;
- live tests are opt-in and require explicit env/profile configuration.

## Proposed CLI Tree

```text
chatol
├── auth
│   ├── login
│   │   ├── --base-url <url>
│   │   ├── --email <email>
│   │   ├── --password <password>
│   │   ├── --cookie <value>
│   │   ├── --cookie-name <name>
│   │   └── --profile <name>
│   ├── whoami
│   │   ├── --profile <name>
│   │   └── --json
│   └── logout
│       └── --profile <name>
├── config
│   ├── show
│   │   └── --json
│   ├── get <key>
│   ├── set <key> <value>
│   └── test
├── project
│   ├── list
│   │   ├── --json
│   │   └── --limit <n>
│   ├── info <project>
│   │   └── --json
│   └── create <name>
│       ├── --template <blank|example>
│       └── --json
├── file
│   ├── tree <project>
│   │   └── --json
│   ├── download <project> <remote-path>
│   │   └── --output <path>
│   ├── upload <project> <local-path>
│   │   └── --remote-path <path>
│   ├── delete <project> <remote-path>
│   └── rename <project> <old-path> <new-path>
├── sync
│   ├── pull <project> [dir]
│   │   ├── --force
│   │   └── --json
│   ├── push [dir]
│   │   ├── --project <project>
│   │   ├── --all
│   │   ├── --dry-run
│   │   ├── --no-ignore
│   │   └── --json
│   └── sync [dir]
│       ├── --project <project>
│       ├── --dry-run
│       ├── --no-delete
│       └── --json
├── compile
│   ├── run <project>
│   │   ├── --compiler <pdflatex|xelatex|lualatex>
│   │   ├── --root <path>
│   │   ├── --timeout <seconds>
│   │   └── --json
│   ├── pdf <project>
│   │   └── --output <path>
│   ├── log <project>
│   │   └── --output <path>
│   └── output <project> [type]
│       ├── --list
│       └── --output <path>
└── comment
    ├── list <project>
    │   ├── --status <all|open|resolved>
    │   ├── --context <n>
    │   └── --json
    ├── add <project> <file> <message>
    │   ├── --text <text>
    │   ├── --line <n>
    │   ├── --column <n>
    │   └── --json
    ├── reply <project> <thread-id> <body>
    ├── resolve <project> <thread-id>
    └── reopen <project> <thread-id>
```

## Python API Sketch

```python
from chatol import ChatOLClient

client = ChatOLClient.from_profile("default")
projects = client.projects.list()
project = client.projects.get("Example Project")

client.files.download(project.id, "main.tex", "main.tex")
client.files.upload(project.id, "main.tex", "main.tex")

result = client.compile.run(project.id, root="main.tex")
client.compile.download_pdf(project.id, result.build_id, "paper.pdf")
```

Lower-level construction should also work:

```python
client = ChatOLClient(
    base_url="https://<public-overleaf-host>",
    session_cookie="...",
    cookie_name="overleaf.sid",
    timeout=30,
)
```

## Implementation Stages

### Stage 1: Auth and project list

Goal: prove reliable self-hosted access.

Scope:

- ChatEnv config fields;
- session/cookie handling;
- password login path;
- CSRF extraction;
- `chatol auth whoami --json`;
- `chatol project list --json`;
- mocked tests plus optional live smoke docs.

Acceptance:

```text
chatol auth whoami --json
chatol project list --json
```

### Stage 2: Project files

Goal: let an agent read and write project files.

Scope:

- file tree;
- download file;
- upload file;
- local metadata file;
- basic pull/push without deletion propagation first.

### Stage 3: Compile feedback loop

Goal: make LaTeX compile errors and artifacts visible to agents.

Scope:

- compile trigger;
- compile result parsing;
- PDF download;
- log download;
- normalized error summary for model repair loops.

### Stage 4: Sync semantics

Goal: useful local editing workflow.

Scope:

- manifest;
- dry-run;
- ignore rules;
- optional deletion propagation;
- conflict handling.

### Stage 5: Comments

Goal: review automation after file and compile operations are stable.

Scope:

- list comments;
- add comment;
- reply;
- resolve/reopen.

## Recommended First Feature PR

```text
Title: Add self-hosted auth and project list client

Scope:
- ChatEnv config fields for base URL, cookie name, email/password, and session cookie
- ChatOLClient with requests session, CSRF extraction, cookie auth, and password login
- `chatol auth whoami --json`
- `chatol project list --json`
- unit tests with mocked responses
- optional live smoke instructions using placeholders only
```

This creates a stable base before implementing sync and compile.
