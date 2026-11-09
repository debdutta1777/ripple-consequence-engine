# Ripple — the two-minute judge demonstration

**Tagline:** Don't just compare what changed. Discover who it changes.

**Setup:** Open the production URL in an ordinary browser. No account, real applicant data, or Clocked credits are required for the fictional interactive demo. Start at the new landing page `/`, review the problem and click **Launch studio**. Within `/studio`, click **Guided tour** for the in-app narration.

## 0:00–0:20 — Explain the problem

> “A new scholarship policy can change someone's eligibility overnight. Typical AI document tools tell you what words changed. Ripple reveals which decisions change, who is affected, and where the evidence came from.”

Show the two fictional source documents: 2025 has a GPA minimum of 3.2 and a $50,000 income ceiling; 2026 has GPA 3.5 and a $60,000 income ceiling. Both constraints matter; a stricter GPA requirement causes losses while a higher income ceiling causes gains.

## 0:20–0:45 — The consequence map

> “Each line is one fictional applicant. Red flows lose eligibility; green flows gain it. These are precise calculations, not AI-estimated statistics.”

Point to the impact counts (16 cases, 4 lost, 4 gained) and select one red line in the interactive map.

## 0:45–1:10 — The policy time machine

> “What if the 2026 GPA requirement were even higher? I can explore the consequences without spending AI credits or pretending this is the actual text.”

Click **Tighter rules** and watch the map and all counts update; click **Wider access** for the opposite scenario, then **Reset**. State that these are unsourced, explicitly marked counterfactuals.

## 1:10–1:40 — Individual proof and source

> “Now we select a student whose decision flipped. Ripple shows exactly why, the minimum threshold adjustments that would reverse the modeled outcome, and the original source clause.”

Select Applicant 01 after Reset, click **Try minimum changes**, then **Find GPA** in updated policy. The Source Lens marks the verbatim clause in context. Click **Export this case's proof card** to download a standalone printable report.

## 1:40–2:00 — Real Clocked integration + trust boundary

> “Clocked's Extract endpoint is our source evidence extractor, Compare checks policy conflicts, and Rerank prioritizes relevant clauses. The rule engine makes transparent, deterministic eligibility decisions. If policy requirements are ambiguous, Ripple says 'needs review' rather than inventing certainty.”

Show the **Inspect API trace** control and the honest mode badge. **Do not describe a mock/synthetic result as a live Clocked run.** The live endpoints are implemented but protected from unbounded public spending; only describe them as verified after the protected test returns actual responses.

## Judge FAQs

- **Is this real scholarship data?** No, all policies and applicants are fictional.
- **Does changing the slider call the AI?** No. It performs deterministic threshold comparisons in the browser.
- **Can it decide arbitrary complex policies?** No, only two narrow thresholds. Exceptions, eligibility conditions, and missing evidence require review.
- **Do you store uploaded PDFs?** The PDF is submitted to the server for text parsing for that request, but the application does not persist it to project storage. A temporary browser object URL is used to open the original PDF on the user's own device.
- **Does the API key appear in the browser?** No. It is configured as a Sensitive Vercel Production secret; administrative Clocked tests need a second, expiring, independently configured token.