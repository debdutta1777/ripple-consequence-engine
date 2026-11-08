# Working rules for Ripple contributors and coding agents

1. **Resume from the checkpoint.** Before changing code, read `checkpoint.json`, `docs/BUILD_CHECKPOINT.md`, and `docs/PHASE_PLAN.md`. The checkpoint is the canonical statement of what was verified, what is currently active, and what is blocked.
2. Work on **one small, testable milestone at a time**. Do not silently skip blocked steps or change scope to boost the number of endpoints.
3. On finishing a milestone, run the applicable tests, update `checkpoint.json` (statuses, `last_completed`, `current_phase`, test evidence, blockers), and append an entry to `docs/BUILD_CHECKPOINT.md` with changed files, test results, and the next concrete action. The next session must be able to resume without reading the conversation.
4. **Never place Clocked credentials in chat or source code.** Only read `CLOCKED_API_KEY` from the backend environment or the locally ignored `.env` file. No API keys in test fixtures or exported traces.
5. Label synthetic and real Clocked results distinctly. Do not replace failed live API calls with sample data or claim mocked responses came from Clocked.
6. Only model the explicit GPA minimum and annual household-income maximum. Unsupported conditions, ambiguous interpretations, missing evidence, or misaligned source spans must yield **review**, not a fabricated eligibility decision.
7. Check category fit and demo quality, but prioritize correctness, evidence integrity, and reproducibility. Never claim an award is guaranteed.
8. Keep the project ready to submit before **2026-11-10 23:59 US Eastern / 2026-11-11 10:29 IST**.
