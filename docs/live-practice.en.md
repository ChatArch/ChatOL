# Live Practice: Server-Side Overleaf Smoke

This page records the server-side live practice for ChatOL's native Python client and the `oleaf` CLI. It is intentionally redacted: no real public service URL, account email, password, cookie, internal build URL, project ID, or entity ID is stored here.

## Environment Shape

```text
ChatOL checkout
  -> local loopback Overleaf URL on the same server
  -> private env file loaded at runtime
  -> self-hosted Overleaf smoke project
```

Secrets are stored outside the repository and passed at runtime through Overleaf-namespaced environment variables or the active ChatEnv `overleaf` profile supported by `chatol.workflows.client_from_env`.

```bash
set -a
source <private-overleaf-env>
set +a
export OVERLEAF_SITE_URL=http://127.0.0.1:<overleaf-port>
export OVERLEAF_HTTP_TIMEOUT=45
```

## Practiced Commands

```bash
oleaf doctor --json
oleaf projects list --json
oleaf projects info "<smoke-project-name>" --json
oleaf compile run "<smoke-project-name>" --json
oleaf compile pdf "<smoke-project-name>" -o smoke.pdf --json
oleaf compile output "<smoke-project-name>" log -o smoke.log --json
oleaf files zip "<smoke-project-name>" -o project.zip --json
oleaf files pull "<smoke-project-name>" ./source --json
oleaf files list "<smoke-project-name>" --json
oleaf files upload "<smoke-project-name>" ./chatol-agent-practice.tex --remote-path chatol-agent-practice.tex --json
oleaf files delete "<smoke-project-name>" chatol-agent-practice.tex --apply --json
```

## Results

| Workflow | Result |
| --- | --- |
| `doctor` | success |
| `projects list` | success; one project was visible in the practice instance |
| `projects info` | success |
| `compile run` | success |
| `compile pdf` | success; PDF written locally |
| `compile output log` | success; log written locally |
| `files zip` | success; project zip written locally |
| `files pull` | success; 3 files extracted locally |
| `files list` | success; project file count was 3 before and after the reversible mutation |
| `files upload` | success for the root-only practice file `chatol-agent-practice.tex` |
| `files delete --apply` | success; the practice file was removed and verified absent |

Observed artifact sizes:

```text
pdf_bytes: 247915
log_bytes: 17466
project_zip_bytes: 99242
pulled_count: 3
practice_pdf_bytes: 248106
practice_log_bytes: 17466
```

## Review Notes

- CLI commands stay thin; real logic lives in importable workflow functions.
- The same behavior can be called from Python through `chatol.workflows`.
- JSON output excludes internal compile URLs by default.
- Passwords and cookies were not passed as ordinary process arguments.
- `files upload` was scoped to a single reversible root file: `chatol-agent-practice.tex`.
- `files delete --apply` was used only for that exact filename; `files list` verified there was no residue after deletion.
- This Overleaf instance did not expose root folder metadata in project HTML; ChatOL used the Socket.IO project-tree fallback to resolve the file ID needed for deletion.
- This smoke does not cover nested directory upload, full sync, rename, comments, or admin capabilities yet.

## Follow-Up

Next live-practice slices should cover:

1. nested directory upload, including folder discovery and missing-folder creation;
2. safe sync planning before any destructive sync;
3. admin route probing before user-management implementation;
4. compile log diagnosis for actionable Agent feedback;
5. optional single-file download and rename commands.
