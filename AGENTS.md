# CRM — Project Context

## What this project is

Frappe CRM frontend. Vue 3 + frappe-ui. The backend is Frappe Python. Scripts in
`frontend/` only; Python in `crm/` (Frappe app). No build step for Form Scripts —
they run as evaluated strings in the browser.

---

## Where to read before working

| Task | Read first |
|---|---|
| What are we building next | [PLAN.md](./.pi/PLAN.md) |
| Stable API contracts (setFieldProperty, formDialog, helpers) | [SPEC.md](./.pi/SPEC.md) |
| **i18n / 多语言（默认中文）** | [feats/i18n/guide.md](./.pi/feats/i18n/guide.md) |
| Why code is the way it is (decisions, bugs fixed, history) | [ARCHIVE.md](./.pi/ARCHIVE.md) |
| Form scripting user guide | [feats/form-scripting/guide.md](./.pi/feats/form-scripting/guide.md) |
| formDialog() API reference | [feats/form-scripting/form-dialog.md](./.pi/feats/form-scripting/form-dialog.md) |
| **Sync code to Ubuntu server & restart** | [scripts/README.md](./scripts/README.md) |

---

## Deploy to Ubuntu (Windows dev → remote server)

Development happens on **Windows**; Frappe bench runs on **Ubuntu** (`10.0.161.126`).

**After completing a feature or when the user wants to see changes on the server**, run from repo root:

```bash
python scripts/sync_to_server.py --deploy
```

This syncs changed files to `~/crm-src` on the server, runs `yarn build`, and restarts bench. Full details, config, and troubleshooting: **[scripts/README.md](./scripts/README.md)**.

Do **not** commit `scripts/deploy.config.json` (local credentials; gitignored).

---

## i18n / 多语言（默认中文）

**This deployment defaults to Chinese (Simplified).** All production code must keep language switching correct — not only wrap strings, but ensure `crm/locale/zh.po` has matching translations.

Full guide: **[feats/i18n/guide.md](./.pi/feats/i18n/guide.md)**

### Agent checklist (every UI/backend change)

| Layer | Rule |
|---|---|
| **Frontend** | User-visible text → `__('English msgid')`. Field labels → `translateLabel(field.label)`. Select options → `translateSelectOptions()` / `processField()`. Status/enum values from DB → `__(value)` at display. |
| **Backend** | User-visible text → `_('English msgid')`. Progress messages, API errors, validation throws — never raw English literals. |
| **DocType** | Master data shown by name (status, source, …) → `"translated_doctype": 1` + `zh.po` entry for each record name. |
| **Translations** | New msgids → add `msgstr` to `crm/locale/zh.po` or extend `scripts/fill_zh_translations.py` and run it. |
| **Defaults** | Do not change system defaults away from zh / China / Asia/Shanghai / CNY without explicit user request. |

### Key files

| File | Role |
|---|---|
| `frontend/src/translation.js` | Global `__()` |
| `frontend/src/utils/translateField.js` | `translateLabel`, `translateSelectOptions` |
| `frontend/src/utils/fieldTransforms.js` | Select option translation in `processField()` |
| `crm/locale/zh.po` | Chinese catalog |
| `crm/setup/defaults.py` | Install/migrate Chinese system defaults |
| `crm/public/js/setup_wizard.js` | Setup Wizard prefills 中文/中国/CNY |
| `scripts/fill_zh_translations.py` | Safely fill missing `zh.po` entries |

### Anti-patterns (never ship)

- Hardcoded English in templates: `description="..."`, `label: 'Set'`, `{{ job.status }}`
- Raw meta: `:label="field.label"`, `:options="field.options"`
- Backend: `progress_message = "Starting sync"` without `_()`
- New features with `__()` calls but no `zh.po` entries → UI stays English for Chinese users

---

## Key files

### Scripting engine
| File | Role |
|---|---|
| `frontend/src/data/document.js` | `useDocument` — loads doc, wires script, patches `save.submit`, exposes triggers |
| `frontend/src/data/script.js` | `getScript` — fetches Form Script records, evaluates class via `new Function`, injects helpers, `setupHelperMethods` |
| `frontend/src/utils/scriptHelpers.js` | `createDocProxy`, `getClassNames` — extracted pure helpers |

### Field rendering
| File | Role |
|---|---|
| `frontend/src/components/FieldLayout/FieldLayout.vue` | Tab/section/column layout. Accepts `context` prop for standalone mode (no useDocument) |
| `frontend/src/components/FieldLayout/Field.vue` | Renders a single field. Calls `useDocument` unless `fieldLayoutContext` is injected |
| `frontend/src/components/FieldLayout/Section.vue` | Section with CollapsibleSection |
| `frontend/src/components/FieldLayout/Column.vue` | Column wrapper |

### Form dialog system
| File | Role |
|---|---|
| `frontend/src/components/Modals/FieldLayoutDialog.vue` | Dialog shell + standalone FieldLayout + local reactive doc |
| `frontend/src/components/Modals/FieldLayoutDialogContainer.vue` | Renders dialog entries from reactive array |
| `frontend/src/utils/renderFieldLayoutDialog.js` | `formDialog()` — pushes to array, returns Promise |
| `frontend/src/components/Modals/GlobalModals.vue` | Mounts FieldLayoutDialogContainer + other app-wide modals |

### Field transforms & validation
| File | Role |
|---|---|
| `frontend/src/utils/fieldTransforms.js` | `processField()`, `findMissingMandatory()`, `parseLinkFilters()` — pure, tested |
| `frontend/src/utils/translateField.js` | `translateLabel()`, `translateSelectOptions()` — i18n for field meta |
| `frontend/src/utils/expressions.js` | `evaluateDependsOnValue()`, `evaluateExpression()` |

### Meta & stores
| File | Role |
|---|---|
| `frontend/src/stores/meta.js` | `getMeta(doctype)` — fetches DocType meta, exposes `getFields()`, formatters |
| `frontend/src/stores/global.js` | `$dialog`, `$socket`, `makeCall` |

---

## Tests

```bash
cd frontend
yarn test:run      # single run
yarn test          # watch mode
```

- **118 tests · ~250ms** — all must pass before committing
- Location: `frontend/tests/unit/`
- Only pure utility functions are unit-tested (no Vue component tests yet)
- Add tests in `tests/unit/` when adding pure logic to `src/utils/`

---

## Commit style

```
feat: short description
fix: short description
refactor: short description
test: short description
docs: short description
```

Multiple logical commits per PR — one commit per coherent change, not one giant commit.
Pre-commit hooks run prettier + eslint + oxlint automatically. If they modify a file,
`git add` the file again and re-commit.

---

## Docs structure

```
PLAN.md          — future only (phases 3B, 4, 5, 6)
SPEC.md          — stable contracts
ARCHIVE.md       — completed phases + decision rationale
feats/           — user-facing feature docs (incl. feats/i18n/guide.md)
archives/        — old docs preserved verbatim
```

When a phase completes: move its spec from PLAN.md to ARCHIVE.md, update SPEC.md if
the API surface changed.
