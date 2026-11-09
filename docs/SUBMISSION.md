# Hackathon submission draft — Ripple

**Project name:** Ripple — The Consequence Engine  
**Tagline:** Don't just compare what changed. Discover who it changes.  
**Public demo:** https://ripple-consequence-engine.vercel.app/  
**Public repository:** https://github.com/debdutta1777/ripple-consequence-engine

## Project description

A scholarship policy is edited. A GPA threshold rises; an income ceiling changes. A document diff can point to the changed text, but it won't tell a program manager who loses eligibility or which changed clause caused the decision. Ripple closes that gap.

Ripple turns two policy versions into an interactive **Consequence Map** of before-and-after decisions for a fictional cohort. Select any path to see the exact conditions; use the **Decision Flip Explorer** to calculate which threshold needs to change; use the **Source Lens** to trace the verbatim evidence. In the **Rule Lab**, experiment with stricter or more inclusive proposals and watch all the outcome paths update instantly, without another AI call. Export a self-contained case proof card that clearly distinguishes actual source evidence from a hypothetical rule.

The backend is designed to use Clocked **Extract** (verbatim rule excerpts), **Compare** (cross-document consistency), and **Rerank** (prioritization of relevant clauses). A protected sample-PDF path also implements Clocked's native `return_pdf="highlight"`. The rule engine deliberately handles only explicit GPA and income constraints; missing or exceptional conditions result in **Needs review**. The public interactive sample is synthetic and does not make paid calls.

**Important before publishing this paragraph:** update this description with **actual** integration-test evidence only if the protected Clocked test has succeeded. Never imply the public synthetic results are real Clocked responses.

## What makes it different

1. **Consequence-first rather than document-first:** a visual map connecting each applicant's before/after eligibility decision.
2. **Instant policy time travel:** edit the modeled policy (not a student's attributes) to simulate how the whole cohort moves.
3. **Counterfactual flip paths:** show the exact minimum modeled threshold changes that would reverse a given case's outcome.
4. **Explainability with proof:** source-language highlights, version-aware evidence, a transparent API trace, and printable proof cards.
5. **Spend-safe demonstration:** optional live calls are protected; experiments and offline PDF preview never consume Clocked credits.

## Technically important choices

- FastAPI + dependency-free responsive HTML/CSS/JavaScript for a single Vercel deployment.
- Python `clocked-sdk==0.7.0`, `pypdf`, and a narrow deterministic eligibility evaluator.
- Bounded PDF uploads: 2 MB, 12 pages, and 12k characters; no app-layer persistent storage.
- Separate security, test and checkpoint logs; `pytest` offline checks and isolated Chromium interaction tests.
- Credible negative results: unsupported rules and missing source evidence are never automatically called eligible.

## Judges' 90-second experience

Open the sample. Follow any red path in the Consequence Map, inspect why it lost eligibility, activate a more restrictive Rule Lab preset to watch changes propagate, reset, then export the source-backed proof card. The full two-minute guided walkthrough is in `docs/JUDGE_DEMO.md` and within the **Guided tour** button in the app.

## Submission checklist (must be confirmed by the owner)

- [ ] Latest GitHub commit is deployed and public sample loads in a private/incognito browser.
- [ ] Screenshot or demo video shows actual UI, not a mockup.
- [ ] Verified Clocked API call result recorded in `docs/VERIFICATION_RESULTS.md` or transparently marked unverified.
- [ ] A short demo video URL is supplied, if required by the organizer.
- [ ] Team details, project links, and challenge-specific fields are completed on the organizer's page.
- [ ] Submission is **actually submitted and confirmed** by November 10, 2026, 11:59 PM US Eastern Time.

**This document is a submission draft, not proof that the project has been submitted.**