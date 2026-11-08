# Ripple — microphase implementation plan

This plan turns the Clocked Build Challenge project into **small, individually verifiable checkpoints**. The detailed status of each phase is in `checkpoint.json` and `docs/BUILD_CHECKPOINT.md`. Never mark a phase complete without a verified artifact or passing check.

## P00 — Baseline audit [COMPLETE]
- [x] Locate starter files and inspect backend, frontend, fixtures, and tests.
- [x] Confirm the known synthetic demo and four Clocked SDK call sites (Extract twice, Compare once, Rerank once).
- [x] Run baseline suite: 12 passed. Identify the live-key dependency.

## P01 — Project management and secret-safe setup [COMPLETE]
- [x] Create persistent phase plan, human checkpoint, machine checkpoint, and `AGENTS.md` resume protocol.
- [x] Add backend-only `.env` support without overriding host environment variables.
- [x] Ignore local `.env*` files except `.env.example`, avoid committing credentials.
- [x] Document secure local/hosting configuration.
- [x] Retest backend after configuration changes.

## P02 — Decision Flip Explorer [COMPLETE]
- [x] Implement a deterministic *componentwise threshold* path for the current policy.
- [x] Handle zero, one, two, or unknown failing conditions without fabricated recommendations.
- [x] Add a visible flip panel and an **Apply thresholds** interaction.
- [x] Link verbatim evidence to specific locations in the policy editor (text mode).
- [x] Test edges, inclusive boundaries, failures, and JavaScript syntax.
- [ ] Browser visual/mobile QA (moved to P06).

## P03 — Verify live Clocked API integration [ACTIVE — NEEDS USER CONFIGURATION]
- [ ] P03.1 User sets `CLOCKED_API_KEY` locally/inside deployment host, without posting it in chat.
- [ ] P03.2 Run a small authenticated Extract request; inspect the real response field and span shapes.
- [ ] P03.3 Compare the fictional old/new policies with the real Compare endpoint.
- [ ] P03.4 Verify Rerank IDs, scores, and response shape; display the trace honestly.
- [ ] P03.5 Harden parser for actual live responses, semantic direction, ambiguous clauses, and failure handling. (Directional checks and unit tests done; live shape/error checks outstanding.)
- [ ] P03.6 Record real endpoint evidence, latency/cost metadata if provided, and verified integration tests (redacted of any keys).

## P04 — Genuine source evidence and PDF workflow [QUEUED]
- [ ] P04.1 Accept constrained text-based PDF inputs, with strict file size and content validation.
- [ ] P04.2 Extract rules through Clocked PDF mode and correctly interpret its returned page offsets.
- [ ] P04.3 Display available Clocked-highlighted PDF outputs; fail gracefully if a PDF can't be marked.
- [ ] P04.4 Connect a case's reason to the evidence position, page, and policy version.
- [ ] P04.5 Add PDF-specific unit/integration tests. Do not promise PDF support before it is verified.

## P05 — Memorable judge demonstration [QUEUED]
- [ ] P05.1 Add a second fictional scenario with a clear *gain* as well as a *loss*.
- [ ] P05.2 Add a 60–120-second in-app guided story: change → affected applicant → evidence → counterfactual.
- [ ] P05.3 Improve distinctiveness (motion, accessibility, evidence-first design), keeping all controls functional.
- [ ] P05.4 Export a compact, transparent evidence report with synthetic/live provenance labels.

## P06 — Correctness, safety and visual QA [QUEUED]
- [ ] P06.1 Regression suite across boundaries, absent rules, contradictory directions, bad input, and simultaneous failures.
- [ ] P06.2 Basic security: no secrets in responses or files, live endpoint cost cap, useful API errors, no frontend key exposure.
- [ ] P06.3 Browser testing at desktop and mobile widths; fix overflow and keyboard navigation issues. (Isolated Chromium synthetic smoke passed at 1440px and 390px; live HTTP/keyboard review remains.)
- [ ] P06.4 Run an end-to-end test of the public judging workflow with **live** Clocked if configured.

## P07 — Deploy and submit [QUEUED]
- [ ] P07.1 Publish a public repository with accurate source history, setup instructions and test evidence.
- [ ] P07.2 Deploy a judge-accessible version. Set backend-only env vars in hosting settings.
- [ ] P07.3 Verify the deployment, demo fixture, real API flow and evidence trace on the public URL.
- [ ] P07.4 Record a concise screen demo and write submission copy describing actual endpoint usage.
- [ ] P07.5 Submit before the published deadline; check confirmation and links.

## Scope / non-goals
This is a *decision simulation* for **fictional scholarship applicants**, not a production aid-decision system. There is no guarantee of any award. Only two modeled requirements are eligible for automatic evaluation; any other case is flagged for review. User credentials and real personal applicant data are not necessary for the hackathon demo.
