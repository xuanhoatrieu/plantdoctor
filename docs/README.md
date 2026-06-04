# 📖 Project Documentation Map (Rig v5.0)

This directory holds project-specific documentation and state tracking managed by the **Rig — Harness-Core Workflow Framework**.

The core harness rules and templates are stored globally in `~/.gemini/antigravity/core/`, while local execution history is persisted in `harness.db` (managed via the `rig` CLI).

## Directory Structure

* [product/](file:///mnt/nvme/leaf/docs/product/) — Product contracts, features specifications, and source of truth documents.
* [stories/](file:///mnt/nvme/leaf/docs/stories/) — active story packets and tasks tracking.
* [decisions/](file:///mnt/nvme/leaf/docs/decisions/) — Architecture decision records (ADRs) explaining tradeoffs and decisions.
* [demo/](file:///mnt/nvme/leaf/docs/demo/) — Visual walkthroughs, screenshots, and verified behavior recordings.

## Quick commands
* View current project stats:
  ```bash
  rig query stats
  ```
* View test proof matrix:
  ```bash
  rig query matrix
  ```
