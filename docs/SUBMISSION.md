# Ripple — The Consequence Engine

**Tagline:** Don't just compare what changed. Discover who it changes.

**Project URL:** https://ripple-consequence-engine.vercel.app/

**Explore Demo:** https://ripple-consequence-engine.vercel.app/studio

**Try It Yourself:** https://ripple-consequence-engine.vercel.app/try

**Public repository:** https://github.com/debdutta1777/ripple-consequence-engine

**Verified live Clocked test:** https://github.com/debdutta1777/ripple-consequence-engine/actions/runs/42713532903

**Native Clocked PDF highlight verification (separate fixture):** https://github.com/debdutta1777/ripple-consequence-engine/actions/runs/42695749607

**Recommended judged award focus:** Best Use of Verify / Compare / Rerank; also enter Best Overall if the form permits selection of multiple categories.

## Short overview (paste into the submission form)

A policy change can look tiny on paper and enormous in its consequences. Ripple helps reviewers compare two scholarship-policy versions, inspect the exact rules that changed, and model which applicants gain or lose eligibility. Its interactive Consequence Map, Decision Flip Explorer and Rule Lab turn a static document diff into clear, source-linked before/after decisions. Judges can explore a fictional demo or upload their own text-based policies and an optional applicant CSV. The bounded public preview uses transparent GPA and USD-income rules; uncertain conditions are flagged for review. Separately, an authenticated Clocked SDK pipeline uses Extract to capture evidence, Compare to identify conflicting provisions and Rerank to prioritize relevant clauses. Real API results and a native PDF highlight proof are available in public GitHub Actions logs. No login is required for the demo.

## Why it matters

Scholarship administrators, policy teams and auditors need to answer more than “what words changed?” They need to know who may be affected, why, and which source clause supports the conclusion. Ripple makes the effect of a change explorable while keeping unsupported rules out of automated eligibility decisions.

## Live demo / showcase steps

1. Open the main landing page and select **Try It Yourself**.
2. Download and upload the two fresh fictional documents:
   - 2025: https://ripple-consequence-engine.vercel.app/assets/samples/judge-policy-2025.pdf
   - 2026: https://ripple-consequence-engine.vercel.app/assets/samples/judge-policy-2026.pdf
3. Select the 16-person fictional sample and click **Analyze policy impact**.
4. Inspect the modeled counts: **4 lost eligibility; 2 gained; 2 remained eligible; 8 remained ineligible; 0 require review**. These apply only to the fictional sample cohort and the supported GPA / income constraints.
5. Open individual decisions, compare source clauses, and export a CSV. For a completely different cohort, upload an applicant CSV instead.
6. Return to the landing page and select **Explore Demo** to use the Consequence Map, Rule Lab, Decision Flip Explorer and guided tour.
7. Show the authenticated Clocked workflow run and the verified API output logs as independent evidence.

## How Clocked is used

The private backend integration implements **Extract**, **Compare**, and **Rerank** with the official Clocked Python SDK. Real tests extracted the fresh 2025 and 2026 scholarship thresholds (GPA 3.25 / 3.65; USD-income ceiling 52,000 / 66,000), detected a conflict, and returned four reranked evidence items. A separate genuine native annotated-PDF proof on the original simple policy pair generated five PDF Highlight annotations.

**Important qualification:** The public Try It Yourself flow performs real PDF text parsing and local deterministic impact computation without paid Clocked calls. Authenticated Clocked verification was run separately using a repository secret in GitHub Actions. On the freshly formatted 2025/2026 PDFs, Clocked Compare returned a conflict but no native PDF highlight spans; do not claim it produced highlighted copies of these particular files. Complex policy conditions, scanned PDFs and arbitrary legal eligibility rules are not automatically supported.

## Implementation and reproducibility

FastAPI, Python, clocked-sdk 0.7.0, pypdf, HTML/CSS/JavaScript, Vercel, GitHub Actions. Public demo is light-mode first, responsive, no login and no visitor API charges. Server PDF inputs are bounded, and original documents are not retained in project storage by the application. Source, automated tests, real Clocked evidence, checkpoint history and build instructions are in the public repository. Latest tests reported 53 passing backend cases and passing browser QA across mobile and desktop.

## Required manual submission steps

- [ ] Open https://clocked.rezolve.ai/challenge using your Clocked account.
- [ ] Submit the project name, short overview, audience/problem and links above.
- [ ] Include the source repository and API evidence links.
- [ ] Add a demo URL or publicly accessible video as requested by the form.
- [ ] Fill in your own team member name, email and GitHub handle, and verify eligibility.
- [ ] Select relevant judged award categories. Optional People's Choice requires the qualifying public LinkedIn post and entry URL by the deadline.
- [ ] Click Submit/Save and keep the **official confirmation/receipt**. Registration alone is not submission.

**Deadline: Wednesday, November 11, 2026, 10:29 AM IST** (Tuesday, November 10, 2026, 11:59 PM US Eastern). Leave ample margin for form or upload issues.