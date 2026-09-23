# Test Critique — Sprint 1 (second pass)

## Concerns

### C-003: Remediated results still identify the pre-remediation build

- **Where:** `unit-tests.md`, `integration-tests.md`, and `e2e-tests.md`
  tested-build headers.
- **Quote:** “**Tested build head:**
  `1e3c15a9606fb23e6af35ca92b4dbb86ebd21f4f`”
- **Failure mode:** evidence-drift
- **Why it matters:** Both previous substantive concerns are resolved in the
  working tree, but the cited commit lacks the Kinesin successor correction
  and INT-0004/0005 lesson mappings. The updated passing receipts therefore
  attribute their results to the earlier, deficient documents.
- **Suggested response:** tighten-assertion — commit the remediation, rerun
  the affected checks against that commit, and update the tested-head
  references before finalizing the report. Alternatively, identify the tested
  working-tree delta with reproducible fingerprints explicitly.

## Confidence

block
