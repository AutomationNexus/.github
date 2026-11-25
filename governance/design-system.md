# Frontend design system — org contract

One frontend stack, one token layer, one widget policy, one accessibility gate across
the org's web UIs. Approved by the operator on 2026-11-24. This file is normative for
every repo that ships a React SPA; `design/tokens.shared.css` is its machine-readable half.

**Wave 1:** CognitiveSystems + Uploadarr. ModelDeck follows at near-zero cost (it has no
widget library). MediaRefinery is a registered `exceptions:` entry in `registry.yml`.

## 1. The fixed stack

| Layer | Org choice | Why this is fixed |
|---|---|---|
| Framework | React 19 + Vite + TypeScript (strict) | Already identical in every repo; changing it buys nothing. |
| Test tool | vitest + `@testing-library/react` | Identical in every repo. |
| Styling | Hand-written CSS over three-layer custom properties (primitive → semantic → component) | Token-driven plain CSS is what lets one token file drive four apps without a build-time framework. |
| Shared tokens | `design/tokens.shared.css` (this repo) — vendored as `src/styles/tokens.shared.css` | Single source for color, type, spacing, radius, motion, control metrics. |
| Fonts | Inter Variable (UI) + JetBrains Mono Variable (code, ids, numerics), self-hosted from the app's own bundle via `@fontsource-variable/<face>` | Every app's CSP is `default-src 'self'`; a font CDN is not an option. Declare only the **latin slice** — two `@font-face` rules pointing at the package's `files/*-latin-wght-normal.woff2` (88 KB for both faces). Importing the package's `index.css` ships every subset (≈400 KB) because the bundler copies every referenced file, whatever its `unicode-range`. |
| Headless widgets | **Radix Primitives — the only headless UI library, used only where a widget needs one** | Menus, typeahead listboxes and positioning-aware tooltips are where hand-built code loses. Everything else stays native. |
| Icons | Inline SVG from one icon set | No icon font, no runtime fetch, no second dependency. |
| Accessibility gate | axe-core driven by Playwright — `@axe-core/playwright` in a Node suite, or the equivalent binding for the repo's test language (e.g. `axe-playwright-python`): zero violations on the WCAG 2.1 AA tag set (minimum: `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`), both themes, at 1440 / 1024 / 390 | A repo without this gate cannot claim the shared stack. The binding is free; the engine, the tag set, the widths, the themes and zero violations are not. |

### Radix rules (the part that replaces "install a component framework")

1. **Native first.** `<dialog>` + `showModal()`, `<details>`, `<input type="checkbox">`,
   `<select>` — use the platform. A modal is a native dialog with a focus trap the
   browser already implements.
2. **Radix only where a widget needs it.** The trigger is a widget spec — a menu with
   roving focus, a combobox with typeahead, a tooltip that must not clip, a listbox with
   keyboard selection. Installing `@radix-ui/*` before the widget exists is a rejected
   change: bundle weight and supply-chain surface for zero call sites.
3. **Wrapped, never imported by a page.** Every Radix package is imported only inside the
   repo's wrapper directory (`src/components/primitives/`; CognitiveSystems' existing
   `src/components/ui/` is accepted until its rename PR). Pages import the wrapper.
   Wrappers keep a stable public prop API so a widget library can be swapped without
   touching pages.
4. **One widget, one PR.** Migrating an existing native widget to Radix ships with the
   tests and a11y evidence for that widget, not as a batch.

## 2. Token rules

- `design/tokens.shared.css` owns the primitive and semantic layers. Consumers add only
  component-layer tokens (panels, rows, shell geometry) and **may not redefine a token
  declared in the shared file**.
- Every color is defined in both theme blocks. Dark is the default theme in
  CognitiveSystems; a consumer may invert which theme is the default but must define both.
- No component rule hardcodes a color; component CSS references tokens.
- The shared palette is **Glacier**. A repo that needs a different palette for brand
  reasons records a `palette-override` entry (owner + review trigger) — a deliberate,
  listed deviation, never a silent fork of the token file.

## 3. What is never shared

Class names, component-layer tokens, page layout, and repo-specific components. The
contract unifies the substrate, not the screens.

## 4. Change process

1. Change `design/tokens.shared.css` or this file by PR to `master` (human-merged; this
   repo never self-merges).
2. Consumers re-vendor the file verbatim, keeping its generated header, and run their own
   gates. A `scripts/sync-design.sh --check` (PR-based, modelled on
   `sync-shared-claude.sh`) is the **desired** mechanism; until it exists, re-vendoring is
   a manual copy with the header intact and a hash check in review.
3. A repo that cannot adopt part of the contract records it under `exceptions:` in
   `registry.yml` — rationale, owner, review trigger — rather than documenting a local
   workaround.

## 5. Adoption status

| Repo | Shared tokens | Fonts | Widget policy | a11y gate | State |
|---|---|---|---|---|---|
| CognitiveSystems | canonical source; vendored and shipped at v1.5.1 (`00bd29d2…`) | Inter + JetBrains Mono Variable, latin slice | native today; Radix per-widget going forward | Playwright + axe, green | `active` |
| Uploadarr | vendored + aliased onto the shared names (#110); palette is the shared **Glacier** (operator decision 2026-11-24 — no override) | Inter + JetBrains Mono Variable, latin slice | Radix behind `components/primitives/` (boundary test-enforced). DropdownMenu and Tooltip conform. **Native-first migration open** (§1 rule 1, one widget per PR): Dialog, ConfirmDialog, Drawer, Sheet and OverlayDialog → native `<dialog>`; Checkbox and Switch → native `<input type="checkbox">`; Tabs keeps Radix only with its widget need stated in the wrapper. A widget that must stay on Radix gets an `exceptions:` entry instead | CI-enforced axe gate in the shared `ci / e2e` job (#114): every dashboard route × 1440/1024/390 × both themes at **zero violations** (`axe-playwright-python`, WCAG 2.1 AA tags), with the allowlist in `tests/e2e_frontend/test_a11y_axe.py` empty by design (a new entry must name the milestone that deletes it, and a stale entry fails the run); green on merged `dev` since 2026-11-24 | `active` |
| ModelDeck | to vendor | to adopt | no library | to add | `desired` |
| MediaRefinery | Tailwind today — registered exception | — | Headless UI — registered exception | — | `exception` |

## 6. Reference implementation

CognitiveSystems `frontend/`: `src/styles/tokens.css` (imports the shared file) →
`base.css` → `components.css` → `pages/*.css`; `e2e/visual.spec.ts` (invariant-based —
no pixel baselines) and `scripts/check-selectors.mjs`. New repos start from these, not
from a blank sheet.
