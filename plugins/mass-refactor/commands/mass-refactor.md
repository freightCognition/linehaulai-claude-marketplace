---
description: Loop-driven mass refactor using an implementer/2-adversarial-reviewer/fixer cycle, run to convergence against a build or test command
argument-hint: "<refactor goal, e.g. 'migrate all fmt.Errorf calls to errors.Join' or 'fix every strict-mode type error'>"
---

# Mass Refactor

Runs a multi-agent workflow that mirrors the loop used in large-scale AI-driven codebase migrations: an error/task queue drives batches of work, each batch goes through an implementer, two independent adversarial reviewers, and a fixer, looped until the check command is clean.

This is a git-mutating, multi-commit operation. Confirm scope with the user before launching it.

## Steps

1. **Determine the refactor goal.** Use `$ARGUMENTS` if given. If empty, ask the user what the goal is.

2. **Determine the check command** — the fast command whose clean output defines "done" for this refactor (e.g. `tsc --noEmit`, `go build ./...`, `cargo check`, `eslint .`, `ruff check .`). Look at the repo (package.json scripts, Makefile, existing CI config) to guess a default, then confirm it with the user via AskUserQuestion rather than assuming. Sanity-check that the command actually enforces the stated goal (e.g. `go vet` won't catch unused imports; a broad linter might not fail on the specific pattern being migrated) — if it looks like a mismatch, say so before proceeding rather than let the loop report "clean" while the goal is still unmet.

3. **Determine the test command** (optional but recommended) — the command that proves behavior wasn't broken (e.g. `npm test`, `go test ./...`, `cargo test`). Ask the user; they can skip it if there's no test suite.

4. **Confirm before running.** Tell the user plainly: this will create a git worktree per batch, make real commits, and can run many agents. Ask them to confirm the goal, check command, test command, `maxRounds` (default 20 — how many survey/refactor rounds to allow before giving up), and that they're on a branch safe to mutate (recommend a dedicated branch if they're on `main`).

5. **Run the workflow.** Read `${CLAUDE_PLUGIN_ROOT}/workflows/mass-refactor.js` and pass its full contents as the `script` parameter to the `Workflow` tool, with:
   ```json
   {
     "goal": "<refactor goal>",
     "checkCommand": "<check command>",
     "testCommand": "<test command or null>",
     "maxRounds": 20
   }
   ```

6. **Report results.** When the workflow completes, summarize: how many rounds it took, how many batches were fixed, whether it converged clean, and the final check/test result. If it hit `maxRounds` without converging, say so explicitly and point out what's left — don't imply full coverage.
