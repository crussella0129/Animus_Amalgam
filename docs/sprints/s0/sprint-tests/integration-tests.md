# Sprint 0 Integration Test Results

- **Runner:** [`run-tests.sh`](run-tests.sh) `integration`, run as part of `all`
- **Tested head:** `8827c4e6f4b910ff481e62092679bd59c3a2dff1` (`dev`); `main` at `782886f87d`, the fork point
- **Result:** 5 passed / 0 failed / 5 total

## Book integrity ([INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) AC1, AC2, AC5)
| Test | Criterion | What is asserted | Result |
|------|-----------|------------------|--------|
| `test_check_book_passes` | AC2 | installed `check-book.sh` output is exactly `check-book: valid v2 Book (3 intent chapters)` | pass |
| `test_summary_reaches_every_intent` | AC2 | each `docs/intents/INT-*.md` appears as `(intents/<basename>)` in `docs/SUMMARY.md` | pass |
| `test_all_relative_links_resolve` | AC2 | [`check-links.sh`](check-links.sh) `docs` checked 67 relative links and found 0 broken, including these result records, which were uncommitted at run time. Fenced code and inline code spans are skipped, so link syntax quoted as an example is not counted. | pass |
| `test_substrate_complete` | AC1 | `check-substrate.sh` prints `substrate-complete`; the marker has `schema-version: 2` and `substrate-version: 4`; `remote-profile.sh` resolves `github`, `main`, `dev` and `human-approve` field by field | pass |
| `test_diff_scope_docs_only` | AC5 | every path in `git diff --name-only main..dev` is under `docs/` or is `.gitignore`; no `.gitignore` line is removed; every added line lies within the `# >>> sprint-loops >>>` … `# <<< sprint-loops <<<` markers, and both markers are present | pass |
