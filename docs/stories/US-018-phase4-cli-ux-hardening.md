# US-018 Phase 4 CLI UX Hardening

## Status

implemented

## Lane

normal

## Product Contract

The Harness CLI reduces Phase 4 command churn by exposing accepted values in
help output, giving actionable parse errors, supporting version checks, and
making decision verification fail mechanically when the configured command
fails.

## Relevant Product Docs

- `docs/HARNESS.md`
- `scripts/README.md`
- `docs/templates/story.md`
- `docs/HARNESS_BACKLOG.md`

## Acceptance Criteria

- `harness-cli --version` prints the installed CLI version.
- `intake`, `story add`, and `backlog add` help show accepted lane values.
- Invalid proof flags tell agents to use numeric `1` and `0`.
- Missing story and decision verification commands print a recovery command.
- `decision verify <id>` exits 1 when the configured command fails.
- `query matrix --numeric` renders proof columns as `1` and `0`.

## Design Notes

- Commands: `scripts/bin/harness-cli --version`, `query matrix --numeric`,
  `story update`, `story verify`, `decision verify`, `backlog add`.
- Queries: no schema change; reuse `query matrix`.
- API: CLI command shape changes only.
- Tables: no schema change.
- Domain rules: strict `0/1` proof input remains; help and errors carry the
  recovery path.
- UI surfaces: terminal help and error output.

## Validation

When updating durable proof status, use numeric booleans:
`scripts/bin/harness-cli story update --id US-018 --unit 1 --integration 1 --e2e 0 --platform 0`.

| Layer | Expected proof |
| --- | --- |
| Unit | Rust tests cover help text and version exposure. |
| Integration | CLI smoke covers version, numeric matrix, invalid proof hint, backlog risk hint, missing verify hint, and failing decision verify exit. |
| E2E | Not applicable; CLI-only story. |
| Platform | Rebuilt `scripts/bin/harness-cli` on the local macOS arm64 platform. |
| Release | `cargo fmt --check`, `cargo test --workspace`, `cargo clippy --workspace -- -D warnings`. |

## Harness Delta

Agents have less need to retry help/discovery commands during Phase 4-style
mechanical verification work.

## Evidence

- `cargo fmt --check`
- `cargo test --workspace` passed with 20 tests.
- `cargo clippy --workspace -- -D warnings`
- `scripts/build-harness-cli-release.sh`
- Rebuilt `scripts/bin/harness-cli`; `scripts/bin/harness-cli --version`
  prints `harness-cli 0.1.7`.
- CLI smoke verified backlog `--risk` help, `query matrix --numeric`,
  invalid `--risk low` recovery text, invalid `--unit yes` recovery text,
  missing story `verify_command` recovery text, and failing `decision verify`
  exit code 1.
- `scripts/bin/harness-cli story verify US-018` passed.
