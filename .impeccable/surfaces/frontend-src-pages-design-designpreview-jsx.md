---
version: 1
slug: "frontend-src-pages-design-designpreview-jsx"
primary_target: "frontend/src/pages/design/DesignPreview.jsx"
related_targets: ["frontend/src/pages/design/design.css", "frontend/src/pages/design/OpdFields.jsx", "frontend/src/pages/design/ServiceCatalog.jsx"]
---

# Clinic prototype surface brief

Scope: `/design/today`, `/design/calendar`, `/design/patients`, `/design/treatment`, `/design/services`, `/design/palette`. Primary source: `frontend/src/pages/design/DesignPreview.jsx` and `design.css`. Mode: Operate; this is a reviewable clinic workspace prototype.

Audience and job: clinic reception and practitioners inspect today's queue, select an appointment, review the corresponding synthetic person, and explore clinical entry screens. Primary flow is queue/calendar → person record → treatment. Four DEMO identities supply the examples.

Direction and memorable moment: the today surface places a readable queue beside an indigo “next patient” panel. Desktop today and treatment grids are `minmax(0,1fr) 280px`, with 24px gap; at ≤1250px these stack. The care panel temporarily becomes a two-column internal grid and returns to block layout at ≤760px. The secondary next-appointment summary hides at ≤1250px.

Calendar uses a locally scrolling grid with 620px minimum width and columns `75px 1fr 1fr`. Patient view uses a 300px list beside a flexible record, reduced to 260px at ≤1250px and one column at ≤760px. Treatment fields use two equal columns, collapsing on mobile; the context panel wraps horizontally at the intermediate breakpoint and returns to blocks on mobile. Palette uses four swatches, then two on mobile; its two specimen panels stack on mobile.

At ≤760px appointment table headers hide and rows become two-column stacked blocks. Identity and service span both columns; status and opening action remain visible. History badges are hidden on mobile, while record details and the visit banner wrap. Clinical tabs scroll horizontally. Search filters synthetic names/IDs; selection is persistent visually. Clinical fields retain independent local state across section tabs during the mounted treatment screen; changing patient or leaving treatment remounts the form. No backend call or localStorage persistence is implemented. Notices explicitly describe prototype actions. Zodiac computation is not implemented.

Proof and status: `docs/design-preview/review.md` passed the five prior material findings for prototype review on 2026-09-11. It is not production certification; some runtime checks were reported by the implementer rather than independently repeated by the reviewer. The palette's short type caption describes base sizes, not every component's computed size. Remaining decisions: user visual approval, real-device readability evaluation, and future real application behavior/integration.

## OPD extension — 2026-09-11

`OpdFields.jsx` extends `/design/treatment` within the established indigo/cream Operate surface. Native disclosure groups (`details`/`summary`) sit inside the three existing tabs: history holds personal/contact and health history; examination holds vitals, causes, element assessments, and diagnosis; care holds treatment, medicines, follow-up, and recorder/consent fields. Preserve the existing shell, field styling, and responsive field layout. Field coverage and source distinctions are recorded in `docs/04-opd-reference-mapping.md`.

All groups start collapsed and can open independently. The examination tab includes nine tri-element text fields, 12 coordinate selectors, and 42 element selectors grouped as fire 4, wind 6, water 12, and earth 20. Assessments remain practitioner-entered; selectors start unrecorded. Care supports adding demo medicine rows. Values persist across the three tabs in mounted React state only, and reset with the treatment form on patient change, navigation away, or reload.

This extension adds no backend or durable record, body diagram, calculation (including BMI, age, lunar birth date, or zodiac), prescription integration, signature, or consent evidence. Pain location is text; recorder and consent fields are demo inputs. The prior review above predates this extension and does not establish its QA status.

## Service catalog extension — 2026-09-11

`ServiceCatalog.jsx` adds `/design/services` using the established indigo/cream Operate identity, with a searchable service list, status filter, and add/edit form. Twelve initial clinic services, prices, and durations come from the dated source snapshot in `docs/05-service-catalog.md`; they are not fictional or live-synced. The demo strip therefore identifies simulated patients rather than calling all data fictional.

Simulated admin actions add or edit names, prices, and durations, deactivate services, and restore them. Duplicate names (including inactive entries), negative prices, and non-positive/non-integer durations are rejected. The care-plan tab draws its service dropdown from the same catalog and allows active services for new selections. Catalog edits remain in `DesignPreview` React state across menu navigation; reload restores the initial snapshot. No backend, authentication, authorization, or durable saving is implemented. Prior review results do not establish QA status for this extension.


## Permanent records extension — 2026-09-12

Related implementation: `frontend/src/pages/staff/Records.jsx` and `Workspace.jsx`, at `/staff`. Preserve the existing indigo/cream Operate identity, clinic logo, labeled fields, and explicit status feedback. This initial single-clinic workflow lets reception register name, birth date, phone, and one responsible practitioner. Practitioners search and open assigned patients, save a new free-text visit draft (chief complaint and examination/care notes) through the API, then review and explicitly confirm it before it becomes immutable. Account confirmation is not a certificate-backed digital signature.

Unsaved registration or visit text displays a notice and explicit discard action; patient switching, section navigation, and logout are disabled until saved or discarded. A browser unload warning protects pending text, and busy state blocks context changes while requests run. This is a dirty guard, not autosave.

Scope boundary: `/design/*` remains the prior in-memory prototype. Structured OPD fields are not integrated with durable records; draft editing through the UI, amendments, audit logging, and export remain outstanding. This is not production completion. `docs/09-records-progress.md` records implementation evidence and remaining work; earlier prototype review results do not certify this extension.
