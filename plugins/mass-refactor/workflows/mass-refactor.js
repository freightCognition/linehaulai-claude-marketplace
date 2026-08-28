export const meta = {
  name: 'mass-refactor',
  description: 'Error-queue-driven mass refactor: implementer + 2 adversarial reviewers + fixer, looped to convergence against a check command, verified by a test command.',
  phases: [
    { title: 'Survey', detail: 'run the check command, batch the remaining work' },
    { title: 'Refactor', detail: 'implement -> 2 adversarial reviews -> fixer, per batch' },
    { title: 'Verify', detail: 'final check + test run' },
  ],
}

const BATCH_SCHEMA = {
  type: 'object',
  properties: {
    clean: { type: 'boolean', description: 'true if the check command is already clean and the goal is satisfied' },
    batches: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          files: { type: 'array', items: { type: 'string' } },
          description: { type: 'string' },
          errorText: { type: 'string' },
        },
        required: ['id', 'files', 'description'],
      },
    },
  },
  required: ['clean', 'batches'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    ok: { type: 'boolean' },
    issues: { type: 'array', items: { type: 'string' } },
  },
  required: ['ok', 'issues'],
}

const FINAL_SCHEMA = {
  type: 'object',
  properties: {
    checkPassed: { type: 'boolean' },
    testsPassed: { type: 'boolean' },
    summary: { type: 'string' },
  },
  required: ['checkPassed', 'summary'],
}

const goal = args.goal
const checkCommand = args.checkCommand
const testCommand = args.testCommand || null
const maxRounds = args.maxRounds || 20

let round = 0
let batchesFixed = 0
let convergedClean = false

while (round < maxRounds) {
  round++
  phase('Survey')
  const survey = await agent(
    `You are surveying a codebase for a mass refactor. Refactor goal: ${goal}\n\n` +
      `Run this check command in the repo root: \`${checkCommand}\`. Capture its full output.\n` +
      `Group any remaining errors/warnings/TODOs relevant to the goal into small batches by file or module ` +
      `(a batch should be small enough for one focused commit — a handful of related files at most).\n` +
      `If the command is clean AND the goal is already satisfied, return {clean: true, batches: []}.\n` +
      `Otherwise return {clean: false, batches: [{id, files, description, errorText}, ...]}.`,
    { schema: BATCH_SCHEMA, phase: 'Survey', label: `survey-round-${round}` }
  )

  if (!survey || survey.clean || !survey.batches || survey.batches.length === 0) {
    convergedClean = !!(survey && survey.clean)
    log(`Round ${round}: ${convergedClean ? 'clean, goal satisfied' : 'no batches returned'} — stopping.`)
    break
  }

  log(`Round ${round}: ${survey.batches.length} batch(es) queued.`)

  const results = await pipeline(
    survey.batches,
    batch =>
      agent(
        `Refactor goal: ${goal}\n\n` +
          `Fix ONLY this batch, touching only these files: ${batch.files.join(', ')}\n` +
          `Batch: ${batch.description}\n` +
          `Relevant errors:\n${batch.errorText || '(none captured — use the goal and files to figure out the change)'}\n\n` +
          `Make the minimal correct change — no stubs, no workarounds papered over with a long justifying comment. ` +
          `If a comment that long feels necessary, the code is wrong; fix the code instead. ` +
          `Re-run \`${checkCommand}\` scoped to these files if possible to confirm the batch is clean. ` +
          `Commit only these files to git with a message describing the fix. Report what you changed and why in one paragraph.`,
        { phase: 'Refactor', label: `implement-${batch.id}`, isolation: 'worktree' }
      ),
    (implNote, batch) =>
      parallel(
        [1, 2].map(n => () =>
          agent(
            `You are an adversarial code reviewer with no visibility into the implementer's reasoning — only this summary of the change: ${implNote}\n\n` +
              `Refactor goal: ${goal}\nFiles touched: ${batch.files.join(', ')}\n\n` +
              `Inspect the actual diff yourself (git diff / git show against the base branch, on these files). ` +
              `Assume the change is wrong until you've verified it. Look specifically for: stubbed-out logic that ` +
              `merely satisfies \`${checkCommand}\`, a workaround defended by a paragraph-long comment instead of a ` +
              `real fix, behavior changes with no matching test coverage, and anything scoped outside this batch's files. ` +
              `Return {ok, issues}.`,
            { phase: 'Verify', label: `review-${batch.id}-${n}`, schema: REVIEW_SCHEMA }
          )
        )
      ),
    (reviews, batch) => {
      const issues = reviews.filter(Boolean).flatMap(r => r.issues || [])
      if (issues.length === 0) return { batch: batch.id, fixed: true, issues: [] }
      return agent(
        `Two adversarial reviewers flagged issues with the fix to batch "${batch.description}" ` +
          `(files: ${batch.files.join(', ')}). Address them for real — fix the underlying code, don't add a comment ` +
          `justifying the problem. Issues:\n${issues.map(i => `- ${i}`).join('\n')}\n\n` +
          `Amend the commit, touching only these files.`,
        { phase: 'Refactor', label: `fix-${batch.id}` }
      ).then(() => ({ batch: batch.id, fixed: true, issues }))
    }
  )

  batchesFixed += results.filter(Boolean).length
}

if (round >= maxRounds && !convergedClean) {
  log(`Hit maxRounds (${maxRounds}) without converging — remaining work was not fully covered.`)
}

phase('Verify')
const final = await agent(
  `Run the check command \`${checkCommand}\` in the repo root.` +
    (testCommand ? ` Then run the test command \`${testCommand}\`.` : '') +
    ` Report whether each passed, and if anything failed, include the tail of its output in the summary.`,
  { schema: FINAL_SCHEMA, phase: 'Verify' }
)

return { rounds: round, batchesFixed, convergedClean, final }
