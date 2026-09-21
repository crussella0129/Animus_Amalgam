# Sprint 0 Unit Test Results

- **Runner:** [`run-tests.sh`](run-tests.sh) `unit`, run as part of `all`
- **Command:** `SPRINT_LOOP_SKILL_DIR=<installed skill dir> bash docs/sprints/s0/sprint-tests/run-tests.sh all`
- **Tested head:** `8827c4e6f4b910ff481e62092679bd59c3a2dff1` (`dev`)
- **Bundle:** sprint-loops 0.22.0
- **Result:** 9 passed / 0 failed / 9 total

## T-001: Book front matter ([INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) AC3, AC2)
| Test | EARS clause | What is asserted | Result |
|------|-------------|------------------|--------|
| `test_readme_fork_identity` | README names Hermes Agent and links upstream | "Hermes Agent" and `https://github.com/NousResearch/hermes-agent` both appear | pass |
| `test_readme_fork_purpose` | README names AACD, Ferric and Kinesin, and links INT-0002 and INT-0003 | all three names appear, plus link targets matching `](intents/INT-0002-*.md)` and `](intents/INT-0003-*.md)` | pass |
| `test_readme_authority_order` | README states intents → work → sprints → SUMMARY | the four numbered authority items exist, and their line numbers strictly increase | pass |
| `test_readme_upstream_boundary` | the `## Where the Book ends` section names `website/`, `README.md` and `AGENTS.md` | exactly one such heading; the three names are searched in the extracted section body only; the section says `website/` is where "Fork records do not go", and says the root files including `AGENTS.md` "are owned by upstream and are outside the Book". The last two checks were tightened after test critique C-001, and each was confirmed to fail on a mutated README. | pass |
| `test_intent_index_complete` | the index links every `INT-*.md`, and no missing path | every chapter's basename is linked, and every `INT-*.md` link target exists | pass |

## T-002: Sprint 1 backlog ([INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) AC4)
| Test | EARS clause | What is asserted | Result |
|------|-------------|------------------|--------|
| `test_backlog_format` | backlog lines are well formed, and exactly T-101 to T-106 | no `(backlog)` line fails the locked regex, and the sorted ID set equals `T-101 … T-106` | pass |
| `test_backlog_intent_linkage` | each named intent's Work evidence links the task | for all 7 task-to-intent pairs, the `Work evidence` line contains `[…T-NNN…](` | pass |
| `test_no_sprint0_tasks_remain` | no `(sprint 0)` entry after Build | `grep -c '(sprint 0)' docs/work/tasks.md` is 0 | pass |
| `test_link_checker_detects_broken_link` | negative path for AC2 link resolution | on a temporary copy of `docs/` with `[x](does-not-exist.md)` appended, `check-links.sh` exits non-zero and prints `BROKEN …README.md: does-not-exist.md` | pass |

Stubs: none. Every assertion reads committed Book files, or a temporary copy of
them for the negative test.
