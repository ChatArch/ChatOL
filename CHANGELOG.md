# Changelog

## 2026-07-16

### Added

- Added a native Python Overleaf client for login/session bootstrap, project listing, project resolution, compile, PDF download, and compile output download.
- Added importable workflow functions backing the CLI: `client_from_env`, `list_projects`, `get_project`, `compile_project`, `download_pdf`, and `download_output`.
- Added CLI commands: `doctor`, `projects list`, `projects info`, `compile run`, `compile pdf`, and `compile output`.
- Added development plan and live-practice documentation for the first server-side Overleaf smoke.

### Changed

- Documented the rule that CLI commands must stay thin and call importable Python functions.
- Updated documentation links to the configured Pages custom-domain URL.

### Fixed

- Added redaction-oriented output defaults so compile URLs are not emitted by default.
