# olcli CLI Tree Reference

This document summarizes the current understanding of `olcli` as a reference for ChatOL design. It intentionally records command structure and design lessons only. It does not include private service URLs, deployment paths, account names, cookies, or credentials.

## Reference Scope

`olcli` is a TypeScript/NPM CLI for Overleaf workflows. It combines four surfaces:

- a main CLI for humans and scripts;
- an importable client library;
- a Git remote helper;
- an MCP server for AI assistants.

ChatOL should learn from its command coverage, but should not copy the whole tree blindly.

## Binaries

```text
@aloth/olcli
├── olcli                  # main Overleaf CLI
├── olcli-mcp              # MCP server entrypoint
└── git-remote-overleaf    # git remote helper
```

## Global Options

```text
olcli [global-options] <command>

--base-url <url>       Overleaf instance base URL
--cookie-name <name>   session cookie name, e.g. self-hosted deployments may differ
--timeout <ms>         HTTP request timeout
--verbose              print HTTP request/status details
--version              show CLI version
--help                 show help
```

## Command Tree

```text
olcli
├── auth
│   ├── --cookie <session>
│   ├── --email <email>
│   ├── --password <password>
│   ├── --no-save-password
│   └── --save-local
├── whoami
├── logout
├── list | ls
│   ├── --json
│   ├── -n, --limit <n>
│   └── --cookie <session>
├── info [project]
│   ├── --json
│   └── --cookie <session>
├── comments
│   ├── list [project]
│   │   ├── --status <all|open|resolved>
│   │   ├── --context <n>
│   │   ├── --json
│   │   └── --cookie <session>
│   ├── add <file> <message> [project]
│   │   ├── --text <text>
│   │   ├── --occurrence <n>
│   │   ├── --position <n>
│   │   ├── --line <n>
│   │   ├── --column <n>
│   │   ├── --length <n>
│   │   ├── --json
│   │   └── --cookie <session>
│   ├── reply <threadId> <body> [project]
│   ├── resolve <threadId> [project]
│   ├── reopen <threadId> [project]
│   └── delete <threadId> [project]
├── download <file> [project]
│   ├── -o, --output <path>
│   └── --cookie <session>
├── zip [project]
│   ├── -o, --output <path>
│   └── --cookie <session>
├── pdf [project]
│   ├── -o, --output <path>
│   └── --cookie <session>
├── output [type]
│   ├── -o, --output <path>
│   ├── --list
│   ├── --project <name>
│   └── --cookie <session>
├── upload <file> [project]
│   ├── --folder <id>
│   └── --cookie <session>
├── delete | rm <file> [project]
│   └── --cookie <session>
├── rename | mv <oldname> <newname> [project]
│   └── --cookie <session>
├── compile [project]
│   └── --cookie <session>
├── pull [project] [dir]
│   ├── --force
│   └── --cookie <session>
├── push [dir]
│   ├── --project <name>
│   ├── --all
│   ├── --dry-run
│   ├── --probe-folder
│   ├── --no-default-ignore
│   ├── --no-ignore
│   ├── --show-ignored
│   └── --cookie <session>
├── sync [dir]
│   ├── --project <name>
│   ├── --verbose
│   ├── --no-delete
│   ├── --dry-run
│   ├── --no-default-ignore
│   ├── --no-ignore
│   ├── --show-ignored
│   └── --cookie <session>
├── config
│   ├── set-url <url>
│   ├── get-url
│   ├── set-cookie-name <name>
│   ├── get-cookie-name
│   ├── set-timeout <ms>
│   └── get-timeout
├── ignored [dir]
│   ├── --no-default-ignore
│   └── --no-ignore
└── check
```

## Functional Groups

### Auth and configuration

- `auth` supports browser session cookies and email/password login.
- `whoami` validates current credentials by querying projects.
- `logout` clears local credentials.
- `config` persists base URL, cookie name, and timeout.
- `check` reports config and credential sources.

### Project discovery

- `list` lists projects.
- `info` resolves a project and prints entity/file metadata.

### File and archive operations

- `download` fetches one remote file.
- `zip` downloads a project archive.
- `upload` uploads one file.
- `delete` / `rm` removes remote files or folders.
- `rename` / `mv` renames remote files or folders.

### Sync operations

- `pull` downloads project files and writes local metadata.
- `push` uploads local changed files, with ignore handling and dry-run support.
- `sync` performs bidirectional sync and can propagate local deletions.
- `ignored` explains effective ignore rules.

### Compile and artifacts

- `compile` triggers remote compilation.
- `pdf` compiles and downloads the PDF.
- `output` lists or downloads compile artifacts such as logs and bibliography outputs.

### Review comments

- `comments list` reads thread metadata and source context.
- `comments add` creates a thread against selected text or a source position.
- `comments reply`, `resolve`, `reopen`, and `delete` manage thread lifecycle.

## Lessons For ChatOL

Keep:

- explicit self-hosted base URL support;
- session cookie name override;
- password login for self-hosted deployments without browser CAPTCHA;
- JSON output for automation;
- compile artifact download as a first-class workflow;
- local metadata for project auto-detection.

Change:

- make the importable Python client the primary surface;
- keep the CLI as a thin wrapper;
- group commands by resource (`project`, `file`, `sync`, `compile`, `comment`);
- stage comments after auth, file, sync, and compile are stable;
- use ChatEnv/profile-backed credential storage instead of ad hoc files.
