# Changelog

## 2026-07-16

### Added

- Added a native Python Overleaf client for login/session bootstrap, project listing, project resolution, compile, PDF download, and compile output download.
- Added importable workflow functions backing the CLI: `client_from_env`, `list_projects`, `get_project`, `compile_project`, `download_pdf`, and `download_output`.
- Added CLI commands under the default `oleaf` command: `doctor`, `projects list`, `projects info`, `compile run`, `compile pdf`, and `compile output`.
- Added development plan and live-practice documentation for the first server-side Overleaf smoke.

### Changed

- Documented the rule that CLI commands must stay thin and call importable Python functions.
- Renamed the primary console entry point from `chatol` to `oleaf`; Python imports remain under `chatol`.
- Loaded active ChatEnv `chatol` profiles in `chatol.workflows.client_from_env`, while preserving process-env and explicit-argument precedence.
- Updated documentation links to the configured Pages custom-domain URL.

### Fixed

- Added redaction-oriented output defaults so compile URLs and private owner/updater metadata are not emitted by default.
- Rejected cross-origin compile-output URLs before download, preventing auth headers from being sent to unexpected hosts.
- Parsed Overleaf project meta names case-insensitively, including raw-list project payloads.
