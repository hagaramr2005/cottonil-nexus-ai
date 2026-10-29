# COTTONIL NEXUS AI V10 — Brand & Arabic UX Report

Date: 2026-10-28. Everything below was measured or executed in this session unless marked **proposed** or **not done**.

## 0. Read this first (things that differ from the brief)

1. **V9 had no login.** There was no auth endpoint and no sign-in screen (only a write token for mutations). The brief asked to "preserve authentication behavior"; there was none to preserve. V10 adds a *minimal, opt-in* sign-in (`backend/app/auth.py`, off unless `NEXUS_AUTH_ENABLED=1`). It is **not** a full IAM product: no lockout, MFA, password reset, audit log or SSO. Do not describe the system as "secure" on the strength of this.
2. **The logo is a wordmark only** (345×50 px, transparent PNG). No icon/monogram version was supplied, so **no favicon was generated** (a 345×50 wordmark cannot be shrunk to 32×32 without cropping, which was forbidden). `theme-color` uses the logo blue.
3. **Dark mode was not retained.** The logo is navy-on-transparent and only works on light surfaces; a light corporate theme was implemented instead (the brief allows this).
4. **The suggested Arabic assistant questions are not all things the backend can answer.** See §6.

## 1. Colors

| Token | Value | Origin |
|---|---|---|
| `--c-brand` | `#003E8B` | **Measured**: dominant opaque pixel color of the supplied logo |
| `--c-brand-ink` | `#0A2A55` | Proposed (darker shade for headings) |
| `--c-brand-hover`, `-soft`, `-wash` | `#00316F`, `#E7EFFA`, `#F3F7FC` | Proposed tints/shades of the measured blue |
| `--c-accent` | `#B7791F` | **Proposed** complementary amber (focus ring, story marker); not an official brand color |
| Status ok / warn / risk | `#14705A` / `#8A5A00` / `#A4262C` | Proposed; each pair meets WCAG AA (5.3–6.3:1) |
| Chart palette | `#003E8B #4B82C8 #9DBBE3 #B7791F #6B7A90 #2E8B73` | Proposed, muted, brand-led |

No official brand guideline was supplied; none is claimed. All tokens live in `frontend/src/tokens.css` (colors, spacing, radius, shadows, type scale, motion, chart palette). Components reference tokens, not literals.

Logo rules applied: aspect ratio preserved (verified in browser: 190×27.53 px = 6.90 = 345/50), never recolored/cropped; on dark brand areas it sits on a white plate; clear space ≥ 16 px; shown in login, sidebar, story mode, reports page and PDF (not repeated elsewhere).

## 2. Typography

- Arabic: **IBM Plex Sans Arabic** (OFL). English/Latin: **Inter** (OFL). Self-hosted through `@fontsource` — no CDN dependency.
- Arabic line-height 1.8 vs 1.65 for English; weights 400/500/600/700 only.
- PDF embeds the IBM Plex Sans Arabic TTFs (`backend/app/assets/fonts`, OFL.txt included).
- Brand typography of the logo was **not** identified or claimed.

## 3. Localization

- Single dictionary `frontend/src/i18n.ts` (every key has `ar` and `en`; `i18n.test.ts` enforces both exist and that Arabic strings contain Arabic script).
- Terminology follows the brief’s glossary (e.g. مركز القيادة التنفيذية، التحليل المتعمق للإيرادات، رصد الأنماط غير المعتادة، مركز الإجراءات، موثوقية البيانات). Tone: professional business Arabic; one colloquial backend string (“دي الحقائق…”) was corrected.
- Navigation, headers, KPI labels/descriptions, chart titles/tooltips, filters, buttons, drawers, empty/loading/error states, login + validation, AI panel, reports page, story mode, and the analytics pages were moved to the dictionary.
- **Backend-supplied English sentences** (case dossiers, limitations, metric definitions; 57 strings found by crawling the API) are translated by an **exact-match presentation map** (`backendText.ts`). Unknown/new backend strings fall back to the original English — they are never guessed. Nothing is written back to the database.
- Raw API error text is no longer shown; users see a localized generic message.
- Numbers: Western digits in both languages (`ar-EG-u-nu-latn`) so a financial figure is character-identical across languages (tested: 841,274,176.32 / “841.27 مليون ج.م” vs “841.27 M EGP”). Missing values show “غير متاح/N/A”, never 0.

## 4. RTL/LTR decisions

- `<html lang dir>` switches without reload; language persists in localStorage; the current page and selected case are kept on switch (tested).
- CSS uses logical properties throughout (`inline-size`, `inset-inline-*`, `border-inline-*`, `margin-inline-*`); only chevrons/arrows are mirrored explicitly.
- Numbers/identifiers: values in `<bdi class="num">`; IDs/SKUs in `.num.code` (forced LTR); money is split into an LTR numeric run + direction-following unit words (this fixed a real bug where “841.27 مليون ج.م” rendered scrambled).
- **Charts never reverse chronology**: time always runs oldest→newest left→right in both languages; labels, tooltip text and number formatting follow the language.
- Story mode arrow keys follow reading direction (tested). Drawer opens from the reading-end edge.

## 5. Navigation

Grouped as specified (النظرة العامة / التحليلات / التحليل الذكي / القرارات والمتابعة / التقارير) using **existing routes only**; no empty pages were added. Inventory analysis is not offered (not supported). A “System” group holds product lineage, settings and operational readiness.
**Model Center**: it was not in V9’s client navigation; V10 additionally enforces on the **server**: `/api/cv/*`, `/api/ai/status`, `/api/product/readiness` return 403 for non-admin tokens when auth is enabled (tested). When auth is disabled (default, as in V9) these endpoints remain open, as before.

## 6. Nexus AI — what is and isn’t supported

The assistant is keyword/tool based (metric lookups, investigation lists, case evidence). V10 suggestions are limited to that:
- General: net sales + reliability, order count, procurement vs sales, recorded investigations (run through the assistant).
- “ما أهم التغيرات في المبيعات؟” **opens Revenue X-Ray** (the verified tool that computes period change) — the assistant itself cannot compute it.
- With an investigation selected: why flagged / supporting data / next step run through the case-evidence endpoint. “Can the numbers be relied on?” opens Data Reliability.
- Answers show evidence chips, expandable detail, copy, related investigations; internal config messages (env var names) are hidden. Free-text answers still come from the backend and are English unless in the translation map.

## 7. Tests executed (this session)

| Check | Result |
|---|---|
| `tsc -b` | pass |
| `vitest` (translation coverage, number formatting) | 4/4 |
| `vite build` | pass |
| Backend, each file in its own process | **39/39** (30 from V9 + 6 auth + 3 PDF) |
| Backend, single combined pytest run | 4 failures — **pre-existing V9 isolation issue** (`test_api.py` sets a temp DB at import; the same 4 tests pass alone). Use `scripts/run_backend_tests.sh`. |
| Browser QA (`scripts/run_qa.sh`, Chromium, desktop 1440 + mobile 390, AR+EN) | **42/42** |

Browser checks include: drawer opens from the inline-end edge (found and fixed during QA: it originally failed to mirror), real login against an auth-enabled backend (empty validation, wrong password, success), dir=rtl/ltr, logo aspect, net-sales value 841.27, chart rendered, no horizontal overflow (desktop+mobile), no English UI leftovers on the Arabic overview, no env-var leak in AI answers, story arrow keys + Escape, language switch keeps page, viewer cannot see admin readiness, console clean.
PDF (AR/EN) rendered and visually inspected: shaped Arabic, RTL alignment, logo intact, figures identical to source.

Screenshots: `docs/screenshots/` (login ×2 + validation/error states, overview ×2, explain drawer, revenue, X-Ray, investigations, AI, story slides, reports, mobile, PDF page 1).
**Visually reviewed by me:** Arabic login, Arabic + English overview, Arabic AI, Arabic story slide 1, Arabic mobile overview, Arabic investigations, Arabic PDF. **Captured but not individually reviewed:** the other screenshots.

## 8. Known gaps / limitations

- Branch/Product/SKU, Risk, Anomaly, Decision, Passport and Lineage pages were translated and pass type-check, but were **not** individually reviewed visually or against complex data states.
- Tables on those pages still use the V9 structure restyled by the new CSS; no per-page redesign was done.
- Excel export is unchanged (not branded/localized).
- PDF has no embedded charts and covers metrics, reliability notes and investigations only; verified only for the current dataset size (page break logic exercised, not stress-tested).
- Story mode: 5 slides, one chart; no speaker notes.
- Data values from the source (channel “Retail POS”, branch names, SKU codes) are shown as stored.
- Accessibility: focus rings, labels, `aria-live`, keyboard story navigation, reduced-motion support, and contrast measured on token pairs (AA). **No screen-reader or axe audit was run.**
- Auth: see §0.1. Tokens live in `sessionStorage`; download links pass `access_token` in the query string when auth is on (acceptable for local use, not ideal for production).
- The single-file V9 frontend (`main.tsx`) was extended rather than fully decomposed; new UI lives in `components/`.

## 9. Windows startup

```powershell
cd cottonil-nexus-ai
.\scripts\start_windows.ps1        # installs deps (incl. arabic-reshaper, python-bidi), builds mart, starts API :8000 + UI :5173
```
Optional login (set before running the script; child windows inherit it):
```powershell
$env:NEXUS_AUTH_ENABLED='1'; $env:NEXUS_AUTH_SECRET='<64 random hex>'
.\.venv\Scripts\python scripts\make_user_hash.py     # prints a salted hash for a password
$env:NEXUS_USERS='manager:<hash>:viewer;admin:<hash>:admin'
```
Run QA: `bash scripts/run_qa.sh` (needs Playwright Chromium), backend tests: `bash scripts/run_backend_tests.sh`.

## 10. Files changed
- `.env.example` — modified
- `backend/app/client_intelligence.py` — modified
- `backend/app/main.py` — modified
- `backend/requirements.txt` — modified
- `frontend/index.html` — modified
- `frontend/package.json` — modified
- `frontend/src/main.tsx` — modified
- `frontend/src/style.css` — modified
- `frontend/vite.config.ts` — modified
- `backend/app/assets` — new
- `backend/app/auth.py` — new
- `backend/app/report_pdf.py` — new
- `backend/tests/test_auth_v10.py` — new
- `backend/tests/test_pdf_v10.py` — new
- `frontend/src/backendText.ts` — new
- `frontend/src/components` — new
- `frontend/src/i18n.test.ts` — new
- `frontend/src/i18n.ts` — new
- `frontend/src/tokens.css` — new
- `scripts/make_user_hash.py` — new
- `scripts/qa_browser.py` — new
- `scripts/run_qa.sh` — new
- `frontend/public/brand/cottonil-logo.png` — the supplied logo, unmodified
- `docs/screenshots/*` — captured screenshots
