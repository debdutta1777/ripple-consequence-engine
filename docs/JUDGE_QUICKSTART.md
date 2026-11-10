# Judge Quickstart — Ripple (2 minutes)

Live homepage: https://ripple-consequence-engine.vercel.app/

## Experience A: Your own PDFs (about 60 seconds)

Open https://ripple-consequence-engine.vercel.app/try . It begins at **Upload your policy versions**. Choose the built-in fresh sample pair, or download these files and upload them in the Previous and Updated boxes:

- 2025: https://ripple-consequence-engine.vercel.app/assets/samples/judge-policy-2025.pdf
- 2026: https://ripple-consequence-engine.vercel.app/assets/samples/judge-policy-2026.pdf

The 2025 policy requires GPA ≥3.25 and income ≤USD 52,000. The 2026 policy requires GPA ≥3.65 and income ≤USD 66,000. Leave the 16 fictional applicants selected, then run analysis.

Expected modeled outcome: **4 lost, 2 gained, 2 still eligible, 8 still ineligible, 0 for review**. Review the animated analysis stages, impact dashboard, textual clause comparisons, affected applicant table and case-specific source evidence. Try export and applicant CSV upload.

This page parses the actual PDFs and evaluates supported scholarship rules deterministically. It does **not** call the paid Clocked API for visitor uploads. Other rule types, OCR and ambiguous conditions require review; supplied cohort data is needed to calculate real population counts.

## Experience B: Consequence Map demo (about 40 seconds)

Open https://ripple-consequence-engine.vercel.app/studio. Choose an applicant path. Observe red eligibility losses, green gains and unchanged cases across the original fictional sample (GPA 3.2→3.5, USD-income cap 50,000→60,000). Explore a hypothetical threshold via Rule Lab, inspect the minimum decision flip, and reveal a supporting clause via Source Lens.

## Clocked evidence (about 20 seconds)

View **real authenticated** Extract ×2, Compare ×1 and Rerank ×1 on the newer fictional policies: https://github.com/debdutta1777/ripple-consequence-engine/actions/runs/42713532903. The SDK returned matching thresholds, a conflicts verdict, and four reranked evidence items.

A separate authenticated native PDF Compare proof on the original simple policy PDFs produced five PDF annotations: https://github.com/debdutta1777/ripple-consequence-engine/actions/runs/42695749607.

The newer styled PDFs had no native highlight spans; do not confuse the source-linked UI evidence with Clocked-generated PDF marks. The UI remains useful without pretending that every arbitrary PDF is automatically interpretable.

Technical details: https://github.com/debdutta1777/ripple-consequence-engine/blob/main/docs/VERIFICATION_RESULTS.md