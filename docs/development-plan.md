# ChatOL Development Plan

## Review Contract

ChatOL development follows these review rules:

- Every CLI command must be a thin wrapper over an importable Python function or class method.
- Core behavior lives in `chatol.client` and `chatol.workflows`, not inside Click command bodies.
- CLI commands must support machine-readable JSON output for agent usage.
- Secrets must never be passed as positional command arguments; use stdin, environment variables, or private profile storage.
- Destructive operations must default to dry-run or require an explicit `--apply` style flag.
- Live-practice reports must redact emails, passwords, session cookies, build URLs, and internal project/user IDs.
- Tests should cover both importable functions and CLI wrappers.

## Phase 1: Native Read/Compile Core

Scope implemented in the first development branch:

```text
chatol
├── Python API
│   ├── OverleafClient.from_password
│   ├── OverleafClient.from_session_cookie
│   ├── OverleafClient.list_projects
│   ├── OverleafClient.get_project
│   ├── OverleafClient.compile_project
│   ├── OverleafClient.download_pdf
│   └── OverleafClient.download_output
├── workflow functions
│   ├── client_from_env
│   ├── list_projects
│   ├── get_project
│   ├── compile_project
│   ├── download_pdf
│   └── download_output
└── CLI thin wrappers
    ├── chatol doctor
    ├── chatol projects list
    ├── chatol projects info <project>
    ├── chatol compile run <project>
    ├── chatol compile pdf <project> -o <path>
    └── chatol compile output <project> <type> -o <path>
```

Design choices:

- Use the Python standard library HTTP stack first to keep the dependency surface small.
- Support both `CHATOL_*` and existing `OVERLEAF_*` environment variable names for server-side practice.
- Parse Overleaf project metadata from HTML meta tags, matching the working `olcli` approach.
- Hide internal compile URLs from CLI output by default.
- Put compile cooldown/retry in workflow functions, not the CLI.

## Phase 2: File Operations

Planned next slice after Phase 1 live practice:

```text
chatol files
├── tree <project>
├── download <project> <remote-path> -o <local-path>
├── upload <project> <local-path> [--remote-path <path>]
├── rename <project> <old-path> <new-name>
└── delete <project> <remote-path> --apply
```

Requirements:

- All mutation commands must call importable functions.
- Upload/delete/rename should return structured before/after results.
- Delete requires `--apply`.
- Reports redact project IDs and internal entity IDs.

## Phase 3: Safe Sync Planning

```text
chatol sync
├── plan <project> <dir>
├── push <project> <dir> --apply
├── pull <project> <dir>
└── sync <project> <dir> --no-delete by default
```

Requirements:

- `plan` is the default safe entry point.
- Deletes are never applied unless explicitly requested.
- Ignore rules must cover LaTeX artifacts and project-local ignore files.
- Conflict reports must be JSON serializable.

## Phase 4: Admin/User Management

Admin is intentionally separate from ordinary project workflows.

```text
chatol admin
├── doctor
├── users list/get
├── users create/invite
├── users set-password --password-stdin
├── users disable/enable
├── users delete --apply --transfer-projects-to <user>
├── projects list-all
└── projects transfer <project> --to <user> --apply
```

Admin prerequisites:

- Detect whether the session is actually admin-capable.
- Probe admin routes and Overleaf version compatibility before mutation.
- Use `--password-stdin`; never password command arguments.
- Use dry-run and idempotency for all mutations.
- Emit audit events with redacted target identifiers.

## Live Practice Loop

For each phase:

1. Add/adjust importable Python API.
2. Add CLI thin wrapper.
3. Add unit tests for parser/client/workflow behavior.
4. Run CLI smoke against the server-local Overleaf endpoint.
5. Save redacted practice markdown under `docs/` or a task report.
6. Feed findings back into the next implementation slice.
