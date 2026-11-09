# Ripple UI review — user-supplied AuditEase project video

**Date:** 2026-11-10. The user uploaded `Video Project 1.mp4` (4:03), and sampled timestamps throughout the clip were inspected. This is inspiration, not reuse of the source application's assets, text, credentials, or brand.

## Useful patterns observed

- The original product opens on a clear marketing page and enters a distinct task workspace.
- The audit workflow surfaces **Select → Upload → Review/Analyze** as a visible stepper, followed by an animated analysis state.
- Its report makes the verdict immediately scannable: prominent headline metric, small cards, grouped compliance findings, and drill-down explanations.
- Supporting interactions (download, change document, report tabs, chat) remain accessible without obstructing the main workflow.
- Visual transitions use smooth card elevation, progressive disclosure, status colors, and restrained movement. The content dashboard uses bright surfaces even when the marketing page is dark.

## Ripple adaptation (not a clone)

- Preserve Ripple's own light-first lavender/indigo identity, Manrope headings and DM Mono metadata, plus its original consequence-map landing page. Do not copy AuditEase's sidebar or green branding.
- In `/try`, start directly at **Upload your policy versions** with a three-stage journey line. The processing sequence updates only after real FastAPI requests complete; a visible progress bar shows stage completion rather than fabricating a percent of server work.
- Add motion as affordance: drop-zone lift, animated document scan while requests are underway, accessible progress meter, KPI card reveal, chart entry, and subtle result summary transitions. Respect `prefers-reduced-motion`.
- Surface a clear, inspectable summary of applicants lost/gained; detailed rule diffs and applicant evidence remain below, with printable report and CSV export.
- Provide a **new fictional 2025/2026 PDF pair** so a judge can demonstrate results that are not the preloaded 3.2/3.5 example.
- Keep results provenance explicit: the public `/try` models supported clauses *deterministically*, while the authenticated Clocked Extract/Compare/Rerank/native highlight evaluation is verified separately on the exact same PDFs and documented in QA receipts.

## Risks and scope

- Users may upload complex PDFs containing unsupported legal conditions. Ripple deliberately returns Needs review rather than fake certainty. The app does not claim OCR or universal legal compliance.
- Do not expose project Clocked secrets in client code or allow unbounded anonymous billable traffic.
- For contest judges, explain both the real provider-backed verification and the intentionally credit-free public preview honestly.