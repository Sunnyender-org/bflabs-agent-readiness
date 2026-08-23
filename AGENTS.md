# BF Labs Agent Bootstrap

This file is intentionally thin.

1. Read `BFLABS.md` completely before any task. It contains this repository's rules.
2. Use `README.md` for product and setup orientation.
3. Use `docs/INDEX.md` when it exists and the owning module, specification, test, or runbook is not already known.
4. Use the active issue, specification, task packet, and pull request for change-specific scope and acceptance.
5. For every rendered or customer-facing surface, apply this rule exactly: `用户看见的字只对使用者负责。实现约束用来遵守，不要写进产品。没见过这次讨论的人读不懂的句子，就不该出现。` Keep runtime contracts, status enums, routing mechanics, validation receipts, and rollback procedures in agent-only references, code, or tests unless a user needs them to complete the task.

Do not expand this file into another engineering playbook. Keep `BFLABS.md` concise: repository invariants, reading paths, safety boundaries, and verification. Move detailed designs and task history to their owning documents.
