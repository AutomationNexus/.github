# `design/` — shared frontend substrate

| File | Role |
|---|---|
| `tokens.shared.css` | The org's primitive + semantic design tokens. Vendored by every React SPA. |
| `../governance/design-system.md` | The normative contract: stack, Radix policy, token rules, adoption status. |

**Editing:** PR to `master`, human-merged — same as any other change in this repo. Never
edit a vendored copy inside a consumer repo; change the file here and re-vendor.

**Vendoring:** copy this file to the consumer's `src/styles/tokens.shared.css` verbatim,
header included, then import it from the repo's own `tokens.css` (or equivalent) and keep
component-layer tokens there. Verify the copy is byte-identical
(`sha256sum` / `Get-FileHash`) in the consuming PR.

A `scripts/sync-design.sh --check` that reports drift across consumer repos is the
desired state; see `governance/design-system.md` §4.
