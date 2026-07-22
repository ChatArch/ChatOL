# Changelog

## Unreleased

### Added

- Added `oleaf files list`, `files zip`, `files pull`, `files upload`, and guarded `files delete --apply` for the first Agent-oriented Overleaf file loop.
- Added importable file workflow APIs: `list_files`, `download_project_zip`, `pull_project`, `upload_file`, and `delete_file`.
- Added `oleaf compile bundle` and `download_compile_bundle` for one-compile PDF/log/source-zip export workflows.
- Added `oleaf templates list/init/upload` and importable template workflows for local paper templates.
- Added `oleaf admin doctor` and `admin_status` for read-only admin/user-management entrypoint probing.
- Added public documentation for the Overleaf Agent task loop and file workflow commands.

### Fixed

- Added Socket.IO project tree fallback for Overleaf instances that no longer expose `rootFolder` metadata in project HTML.

## 0.1.1 - 2026-07-16

### Added

- Added a native Python Overleaf client for login/session bootstrap, project listing, project resolution, compile, PDF download, and compile output download.
- Added importable workflow functions backing the CLI: `client_from_env`, `list_projects`, `get_project`, `compile_project`, `download_pdf`, and `download_output`.
- Added CLI commands under the default `oleaf` command: `doctor`, `projects list`, `projects info`, `compile run`, `compile pdf`, and `compile output`.
- Added development plan documentation and a server-side Overleaf connection guide.

### Changed

- Documented the rule that CLI commands must stay thin and call importable Python functions.
- Renamed the primary console entry point from `chatol` to `oleaf`; Python imports remain under `chatol`.
- Loaded active ChatEnv `overleaf` profiles in `chatol.workflows.client_from_env`, while preserving process-env and explicit-argument precedence.
- Standardized configuration on Overleaf names: official `OVERLEAF_SITE_URL` / `OVERLEAF_ADMIN_EMAIL` plus `OVERLEAF_*` ChatOL extras, without a parallel `CHATOL_*` env-key path.
- Updated documentation links to the configured Pages custom-domain URL.

### Fixed

- Added redaction-oriented output defaults so compile URLs and private owner/updater metadata are not emitted by default.
- Rejected cross-origin compile-output URLs before download, preventing auth headers from being sent to unexpected hosts.
- Parsed Overleaf project meta names case-insensitively, including raw-list project payloads.
