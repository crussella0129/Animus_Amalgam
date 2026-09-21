# Sprint 0 End-to-End Test Results

- **Status:** possible, and executed
- **Runner:** [`run-tests.sh`](run-tests.sh) `e2e`, run as part of `all`
- **Tested head:** `8827c4e6f4b910ff481e62092679bd59c3a2dff1` (`dev`)
- **Result:** 1 passed / 0 failed / 1 total

## `test_cold_clone_orientation` ([INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) Intent: someone new can orient and resume from the tracked Book alone)

**Arrangement:**

1. Run `git clone --branch dev` from the local repository into a temporary
   directory under the session scratchpad. The clone is sparse and checks out
   only `/docs/` and `/.gitignore`.
2. Create a local `main` from `origin/main`.

**Assertions:**

- the router's phase in the clone equals the phase in the working repository;
- `check-book.sh` exits 0;
- `check-substrate.sh` prints `substrate-complete`;
- `docs/README.md` exists.

**Observed:** the clone was at `8827c4e6f4`, and its phase was `test`, the same
as in the working repository. The test passed.

### First run failed, and the arrangement was corrected

The first execution, before the tooling was committed and still on a full
checkout, failed. In the clone, `check-substrate.sh` reported
`substrate-partial:branch:main`.

The cause was in the test, not the Book. `git clone --branch dev` creates only
a local `dev`, and `check-substrate.sh` requires local branches for both
profile branches (`main` and `dev`). A real newcomer clones from GitHub, which
checks out the default branch `main`, and then runs `git checkout dev`. That
leaves both branches local, and the substrate check passes. The corrected setup
reproduces that state: it creates `main` from `origin/main`. It does not
weaken any assertion; all four assertions are unchanged from the locked plan.

A related first-run artifact: Git Bash rewrites a sparse pattern that starts
with `/` into a Windows path. The runner sets `MSYS_NO_PATHCONV=1` for the
`sparse-checkout` call. Without it, the clone's working tree was empty and
`check-substrate.sh` reported `substrate-absent`. That reading came from the
test setup, not from the Book.

Also observed: a full checkout of this repository hit Windows `Device or
resource busy` errors while the temporary clone was being removed. The sparse
checkout avoids them.
