# Obsidian Operating Layer Usable MVP Plan

> **For Hermes:** Use `obsidian-layer-triage-kanban` as the execution board. Hermes remains acceptance/safety owner; Codex handles substantive code slices; Nanobot reviews read-only/proposal-only; Ops verifies.

**Goal:** Bring Obsidian Operating Layer to a logical usable point where Dmitry can safely generate reviewable vault-fix proposals, inspect them, approve a tiny batch, apply it with backups, and verify the result.

**Architecture:** Keep the live vault protected by default. The product milestone is not “full automatic cleanup”; it is a usable control plane: observe/index/classify/score/propose/review/apply-approved/verify. All automation before approval is repo-only or read-only/proposal-only; live writes require explicit manifest + backup + post-verify.

**Tech Stack:** Python CLI tools under `tools/`, core library under `src/obslayer/`, pytest, `make verify`, Hermes Kanban board `obsidian-infra-triage`, generated artifacts under ignored `out/`, durable acceptance docs under `docs/spec-kit/` and `docs/acceptance/`.

---

## Current state

- Repo: `/home/hermesadmin/work/obsidian-operating-layer`
- Branch: `main`
- Safety stance: live vault protected; repo-only/read-only first.
- Existing accepted layers: safety core, observe/propose/verify/apply-dry-run, approval manifest binding, review dashboard, semantic proposal-only reports, proposal routing contract, unified queue/state/decision docs, single R7 apply pilot evidence.
- Current roadmap: `docs/spec-kit/37-vault-automation-indexing-roadmap.md`.
- Current full-vault evidence: `out/reports/full-vault-index-analysis/20260705T084734Z/`.
- Current next technical track: R1–R5 from lane schema through safe auto-proposal thresholds.
- Note: there is currently an uncommitted WIP edit in `src/obslayer/lane_schema_v1.py` from the interrupted lane-summary slice. First execution task must either finish/verify it or revert it before continuing.

---

## Definition of “usable”

The project is usable when Dmitry can run one documented command sequence that:

1. reads the live vault safely or uses the latest approved index evidence;
2. builds lane packets with `live_mutation_authorized: false`;
3. builds archive-shadow evidence so archive/backup/duplicate/redirect notes are not treated as active targets;
4. scores candidate link fixes with reason codes and confidence;
5. generates a reviewable dry-run proposal bundle with zero live writes;
6. shows the bundle in a dashboard/report that Dmitry can inspect;
7. accepts a tiny explicit approval manifest for 1–5 safe targets;
8. creates backups, applies exactly the approved changes, and post-verifies;
9. writes a concise acceptance report and leaves the board/repo clean.

Non-goal for this milestone: unattended vault cleanup, broad auto-apply, automatic note creation/rename/merge/delete, Soul/archive mutation, scheduled production indexing.

---

## Milestone plan

### M0: Stabilize current WIP and board state

**Objective:** Make the repo clean and board truthful before planning/executing new implementation.

**Files:**
- Modify or revert: `src/obslayer/lane_schema_v1.py`
- Test: `tests/test_lane_schema_v1.py`
- Board: `obsidian-infra-triage`

**Steps:**
1. Inspect `git status --short` and current diff.
2. Decide whether the lane-summary WIP is part of R1 acceptance.
3. If yes, add/update tests for `lane_summaries` fields.
4. Run `python3 -m pytest tests/test_lane_schema_v1.py -q`.
5. Run `git diff --check`.
6. Run `make verify`.
7. Commit/push if green.

**Acceptance:**
- Working tree clean except ignored `out/`.
- Board has no stale running card.
- Latest CI green after push.

---

### M1: R1 lane-schema-v1 complete enough for operators

**Objective:** Lane packets are machine-readable and explain each lane’s source class, issue type, allowed next action, forbidden actions, approval class, confidence policy, and sensitive flags.

**Files:**
- `src/obslayer/lane_schema_v1.py`
- `tools/obsidian_lane_schema_v1.py`
- `tests/test_lane_schema_v1.py`
- `docs/spec-kit/37-vault-automation-indexing-roadmap.md`
- `docs/acceptance/index.md`

**Steps:**
1. Add failing test that asserts the four roadmap lanes produce `lane_summaries`.
2. Implement minimal lane summary mapping.
3. Ensure every lane has `live_mutation_authorized: false`.
4. Ensure `archive_or_backup_noise` and `active_soul_source` route to report-only/human-gated.
5. Generate a real packet from `out/reports/full-vault-index-analysis/20260705T084734Z/actionable-lanes.json`.
6. Save evidence under `out/reports/lane-schema-v1/<stamp>/`.
7. Update docs/acceptance with the accepted R1 boundary.

**Verification:**
- `python3 -m pytest tests/test_lane_schema_v1.py -q`
- `python3 tools/obsidian_lane_schema_v1.py --actionable-lanes-json out/reports/full-vault-index-analysis/20260705T084734Z/actionable-lanes.json --notes-index-jsonl out/reports/full-vault-index-analysis/20260705T084734Z/notes-index.jsonl --wikilinks-jsonl out/reports/full-vault-index-analysis/20260705T084734Z/wikilinks.jsonl --out-dir out/reports/lane-schema-v1/<stamp>`
- `git diff --check`
- `make verify`

**Acceptance:**
- R1 accepted in docs.
- No live vault mutation.

---

### M2: R2 archive-shadow-index as explicit resolver input

**Objective:** Archive/backup/duplicate/redirect collisions become first-class evidence and cannot be chosen as default active replacements.

**Files:**
- `src/obslayer/archive_shadow_index.py`
- `tests/test_archive_shadow_index.py`
- possibly `tools/obsidian_archive_shadow_index.py`
- `docs/spec-kit/37-vault-automation-indexing-roadmap.md`

**Steps:**
1. Add counts/summary fields: total shadows, by kind, active-target collisions, shadow-only records.
2. Add reason codes required by roadmap: `active_target_available`, `archive_shadow_only`, `memory_plus_archive_collision`, `redirect_collision`, `duplicate_title_group`.
3. Add CLI if missing, so archive-shadow can be generated independently from notes-index.
4. Generate real evidence for the 20260705 index.
5. Document that archives are evidence-only by default.

**Verification:**
- `python3 -m pytest tests/test_archive_shadow_index.py -q`
- real CLI generation under `out/reports/archive-shadow-index/<stamp>/`
- `make verify`

**Acceptance:**
- Covers archive collision groups and memory+archive ambiguity explanation.
- Does not propose archive targets as active replacements.

---

### M3: R3 candidate-scorer-v1 produces reviewable candidate packets

**Objective:** Score candidate link fixes without editing notes, starting with `active_memory_ambiguous_memory_plus_archive`.

**Files:**
- `src/obslayer/candidate_scorer_v1.py`
- `tests/test_candidate_scorer_v1.py`
- possibly `tools/obsidian_candidate_scorer_v1.py`
- `docs/spec-kit/37-vault-automation-indexing-roadmap.md`

**Steps:**
1. Add tests for exact title/path/alias, folder locality, archive-shadow penalty, source/target sensitivity, and top-two gap.
2. Add route classification: `suggest`, `auto-propose`, `needs-human-review`, `blocked/refuse`.
3. Ensure Soul/archive/canonical risks force human gate or block.
4. Generate a sample packet over current evidence, limited to a safe cap first.
5. Save report under `out/reports/candidate-scorer-v1/<stamp>/`.

**Verification:**
- `python3 -m pytest tests/test_candidate_scorer_v1.py -q`
- generated sample JSON validates safety fields
- `make verify`

**Acceptance:**
- Every candidate has confidence, reason codes, risk gates, and route.
- No proposal manifest or live apply is created.

---

### M4: R4 operator-decision-ledger-v1

**Objective:** Past approve/reject/held decisions become weak, reviewable scoring evidence without becoming apply authority.

**Files:**
- Create: `src/obslayer/operator_decision_ledger_v1.py`
- Create: `tools/obsidian_operator_decision_ledger_v1.py`
- Create: `tests/test_operator_decision_ledger_v1.py`
- Docs: `docs/spec-kit/37-vault-automation-indexing-roadmap.md`

**Steps:**
1. Define append-only JSONL schema: source pattern, proposed target, decision, reason, scorer version, verification outcome.
2. Add loader that returns weak prior signals.
3. Add tests proving reject/held lowers future confidence and approve does not authorize live apply.
4. Add CLI to validate and summarize a ledger.
5. Add empty starter ledger under repo-controlled safe path if appropriate, or document generated `out/` ledger first.

**Verification:**
- `python3 -m pytest tests/test_operator_decision_ledger_v1.py -q`
- `make verify`

**Acceptance:**
- Ledger is reviewable, secret-safe, and never grants apply authority.

---

### M5: R5 dry-run proposal generator for deterministic-high safe cases

**Objective:** Generate proposal bundles only for deterministic-high, non-sensitive, non-archive-collision candidates.

**Files:**
- Existing proposal tools, likely `tools/obsidian_semantic_targeted_proposal.py` / proposal routing modules
- New or updated generator under `src/obslayer/` if needed
- Tests under `tests/`
- Docs: `docs/spec-kit/31-operator-flow-and-review-queue.md`, `docs/spec-kit/37-vault-automation-indexing-roadmap.md`

**Steps:**
1. Add tests for allowed deterministic-high candidate → proposal target.
2. Add tests for blocked Soul/archive/global/rename/delete/merge candidates.
3. Ensure bundle includes file, position, old link, proposed link, confidence, reason, policy tag, rollback key.
4. Ensure output says `dry_run_default: true`, `approval_required: true`, `live_mutation_authorized: false`.
5. Generate a real proposal-only bundle from capped evidence.

**Verification:**
- focused pytest for proposal generator
- JSON schema/safety assertions over generated proposal
- `make verify`

**Acceptance:**
- Dmitry can inspect proposal candidates safely.
- Zero live writes.

---

### M6: Usable operator command/runbook

**Objective:** One documented command path for normal use.

**Files:**
- `Makefile`
- `docs/runbooks/` new or updated runbook
- `docs/acceptance/index.md`

**Steps:**
1. Add or update make targets for: lane packet, archive shadow, candidate scoring, proposal bundle, dashboard/report, verify.
2. Write runbook: “Generate reviewable Obsidian proposal bundle”.
3. Include expected artifacts and safety checks.
4. Add smoke test for critical make targets if feasible.

**Verification:**
- Run the full command path on current evidence.
- `make verify`.

**Acceptance:**
- Дмитрий can use the system without knowing internal file layout.

---

### M7: Narrow approved apply pilot, only after explicit approval

**Objective:** Apply 1–5 reviewed safe targets with backup and post-verify.

**Precondition:** Dmitry explicitly approves a concrete approval manifest. Do not start automatically.

**Steps:**
1. Present proposal bundle summary to Dmitry.
2. Ask for approval of exact targets.
3. Create/validate approval manifest.
4. Backup.
5. Apply.
6. Post-verify.
7. Save acceptance report.

**Verification:**
- proposal target hashes match
- backup exists
- apply report exists
- post-verify green
- no unexpected file changes

**Acceptance:**
- This proves the project is usable end-to-end, but not broadly autonomous.

---

## Kanban execution model

For each milestone, use chain:

```text
intake/brief → code_slice → ops_verification → nanobot_review → docs_update → final_report
```

- Codex handles substantive code changes.
- Hermes verifies and owns acceptance.
- Nanobot reviews only artifacts/repo, no live mutation.
- Push after each green slice.

---

## Final project “logical point” checklist

- [ ] `make verify` green.
- [ ] CI green on `origin/main`.
- [ ] Runbook exists for proposal generation.
- [ ] Proposal bundle can be generated from current evidence.
- [ ] Review/dashboard output is readable.
- [ ] Approval manifest flow is documented and tested.
- [ ] At least one tiny approved apply pilot completed or ready for Dmitry approval.
- [ ] Live vault safety boundary documented in acceptance index.
- [ ] Board has no stale running cards.
