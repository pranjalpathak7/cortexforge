# Demonstration procedure

1. Follow README setup. Start Docker and build the sandbox image.
2. Run `python scripts/init_sample.py`; copy the printed repository path.
3. Start backend/frontend. Enter your backend REVIEW_TOKEN into the local UI.
4. Create a run, select fixture demo, paste the sample path and use the default
   apply_discount requirement. Select the `test` fault.
5. Observe analyst criteria, architecture scope and clean baseline. Developer
   applies a deliberately wrong divisor; real pytest fails. Inspect stdout and
   exit code. A bounded repair changes the divisor and checks run again.
6. Inspect the successful security scan, code diff, model/fixture usage labels,
   source branch and baseline/candidate rubric.
7. At Human review, enter your identity and rationale. Review all evidence,
   then explicitly approve or reject. An approved patch can be downloaded.
   Approval never pushes, merges or deploys.
8. Repeat with `security` to see Bandit find eval, `malformed` for schema retries,
   `provider` for durable outage state, `scope` for pre-write rejection, `repeat`
   for cycle detection and `disagree` for bounded architect escalation.
9. Run `python evaluation/run.py` to reproduce all cases automatically, ending
   successful cases at the human checkpoint. Run `pytest` for restart coverage.

For live mode set GROQ_API_KEY and LLM_MODEL, restart the backend and choose
Live AI. Use a supplied controlled local Python Git repository and a clear
requirement. Live outputs and token usage come from the provider, not fixtures.

If interrupted, inspect the run and use Retry / resume for BLOCKED states.
An interrupted patch requires inspection and a fresh run. Existing artifacts
remain under `.cortexforge/runs/<id>/worktree` for review.
