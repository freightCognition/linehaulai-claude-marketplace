# Mass Refactor Plugin

Loop-driven mass refactor across many files, modeled on the implementer/2-adversarial-reviewer/fixer loop used in large-scale AI-driven codebase migrations (error-queue-driven task batching, git-worktree isolation per batch, loop-until-clean against a check command, test suite as final oracle).

## Usage

```
/mass-refactor <goal>
```

```bash
/mass-refactor migrate all fmt.Errorf(%v) calls to %w
/mass-refactor fix every strict-mode TypeScript error
/mass-refactor replace the deprecated http.Client wrapper everywhere it's used
```

The command asks you to confirm the refactor goal, a **check command** (fast, defines "done" — `tsc --noEmit`, `go build ./...`, `cargo check`, a linter, etc.) and an optional **test command** (proves nothing broke), then launches the `mass-refactor` workflow.

## How the loop works

1. **Survey** — an agent runs the check command, groups the remaining failures into small batches by file/module.
2. **Refactor** — each batch runs, independently and in parallel, through:
   - an **implementer** (its own git worktree) that makes the minimal fix and commits it,
   - **two adversarial reviewers**, each blind to the implementer's reasoning, told to assume the change is wrong and look specifically for stubbed-out logic and workarounds justified by a long comment instead of a real fix,
   - a **fixer** that applies any confirmed issues for real (not with more justifying comments) and amends the commit.
3. Repeat **Survey → Refactor** until the check command comes back clean, or `maxRounds` is hit.
4. **Verify** — a final pass re-runs the check command and the test command as the correctness oracle.

## Prerequisites

- A git repository, ideally on a dedicated branch — this makes real commits across worktrees.
- A check command that fails loudly on the thing you're refactoring (compiler, type checker, or linter).
