# Test Critique — Sprint 2

Round 2, an independent read-only re-review at head `5be1ed4331`. The
responses to these concerns are recorded in the test report.

Status of round 1 (C-001 to C-015):

- C-012, C-013 and C-015 resolved.
- C-005 and C-006 resolved or legitimately deferred to T-211.
- C-001 deferred properly. D1's stable-bytes clause must be reported as failed
  across sessions.
- C-002, C-003, C-004, C-008, C-010 and C-011 partly open (see below).
- C-007, C-009 and C-014 resolved.

## Concerns

### C-016: The receipt audit passes M1 for all 13 attempts, but 3 manifests lack M1 fields
- **Where:** `test_every_published_attempt_resolves_to_a_valid_frozen_manifest` (`REQUIRED_FIELDS`); T-201 entry.
- **Quote:** "every attempt resolves to a published manifest with artifact/tokenizer/template/runtime hashes, … task corpus, seed"
- **Failure mode:** weak-assertion
- **Why it matters:** Manifests for attempts 01–05 lack `interpreter` and `task_corpus_sha256`. The audit also freezes `rendered_prefix == "not-measured"`, which T-211 plans to change.
- **Suggested response:** tighten-assertion. Scope full M1 to attempts 06 onward, require zero inference for bring-up manifests, correct T-201, and accept either a measured prefix or `not-measured`.

### C-017: Completed-tasks and the ledger still carry claims the revised evidence contradicts
- **Where:** completed-tasks T-206, T-208, T-209; ledger header; E2E defect-repair list.
- **Failure mode:** evidence-drift
- **Why it matters:**
  - A sentinel was present only in attempts 08–09.
  - The confidence text postdates the first formal run.
  - Smokes 07–09 were checked after the fact.
  - The audit did not screen for privacy.
  - The stated test count is stale.
  - The policy extraction is listed as a defect repair.
  - The owner of the post-attempt-13 replay is ambiguous.
- **Suggested response:** tighten-assertion (correction entries; align the ledger; choose one replay owner).

### C-018: The P1 exclusion clause and P2 `book_scope_review` have no recorded checks
- **Failure mode:** EARS-coverage
- **Suggested response:** add a privacy screen to the audit and record `book_scope_review` honestly (the confidence record postdates the first run; the operation predates it).

### C-019: D2's output-limit clause has no check or test; the planned wire test has no disposition
- **Failure mode:** EARS-coverage
- **Suggested response:** add the check, or name it in T-211 and mark D2 partial. Disposition `test_hermes_wire_and_isolation_contract` by name.

### C-020: Time accounting is still unratified, and the overrun claim doesn't match the receipts
- **Failure mode:** evidence-drift
- **Why it matters:** Wall-clock accounting with both intervals excluded puts attempts 10–11 inside the allowance and 12–13 outside. Whether interval 2 is chargeable decides the rest. The direction review and sprint meta present the change as adopted.
- **Suggested response:** tighten-assertion (publish the computation, mark the change unratified, and ask the owner).

### C-021: The tested head for the critique-response tests is unnamed, and the first critique is unsaved
- **Failure mode:** evidence-drift
- **Suggested response:** tighten-assertion (name the head with per-file counts; save critique-01 and critique-02).

### C-022: Launch identity never re-checks for uncommitted changes, and the `source_dirty` case only trips the digest
- **Where:** `run.py` (only `git rev-parse HEAD`); the identity test.
- **Failure mode:** negative-path
- **Suggested response:** add-test (pass launch-time dirty status into `identity_mismatch`), or name the gap in T-211.

### C-023: The floor exception's "matching pin" check works in one direction only
- **Where:** `agent/agent_init.py::_enforce_minimum_context`.
- **Quote:** `_ctx = max(_ctx or 0, agent._ollama_num_ctx)`
- **Failure mode:** weak-assertion
- **Why it matters:** A pin of 8192 with a served window of 4096 is admitted below the floor. The test does not patch the local num_ctx probe.
- **Suggested response:** add-test (a served window below the pin must be refused; patch the probe).

## Confidence
block
