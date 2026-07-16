# Live Practice: Server-Side Overleaf Smoke

This page records the first live practice for ChatOL's native Python client and `oleaf` CLI. It is intentionally redacted: no real public service URLs, account emails, passwords, cookies, or internal build URLs are stored here.

## Environment Shape

```text
ChatOL checkout
  -> local loopback Overleaf base URL on the same server
  -> private env file loaded at runtime
  -> self-hosted Overleaf smoke project
```

Secrets are loaded outside the repository, then passed through Overleaf-namespaced process environment variables or the active ChatEnv `overleaf` profile supported by `chatol.workflows.client_from_env`.

```bash
set -a
source <private-overleaf-env>
set +a
export OVERLEAF_SITE_URL=http://127.0.0.1:<overleaf-port>
export OVERLEAF_HTTP_TIMEOUT=45
```

## Commands Practiced

```bash
oleaf doctor --json
oleaf projects list --json
oleaf projects info "<smoke-project-name>" --json
oleaf compile run "<smoke-project-name>" --json
oleaf compile pdf "<smoke-project-name>" -o smoke.pdf --json
oleaf compile output "<smoke-project-name>" log -o smoke.log --json
```

## Results

| Workflow | Result |
|---|---|
| `doctor` | success |
| `projects list` | success, one project visible in the practice instance |
| `projects info` | success |
| `compile run` | success |
| `compile pdf` | success, PDF written to disk |
| `compile output log` | success, log written to disk |

Observed artifact sizes in this run:

```text
pdf_bytes: 247915
log_bytes: 17466
```

## Review Notes

- CLI commands are thin wrappers over importable workflow functions.
- The same behavior can be called from Python through `chatol.workflows`.
- JSON output excludes internal compile URLs by default.
- Passwords and cookies were not passed as process arguments.
- This smoke does not cover file mutation, sync, comments, or admin management yet.

## Follow-Up

Next live-practice slices should cover:

1. file upload/download/rename/delete using native ChatOL functions;
2. safe sync planning before any destructive sync;
3. admin route probing before user-management implementation;
4. compile log diagnosis for agent feedback loops.
