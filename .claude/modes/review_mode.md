# Review mode

Purpose: help me understand code Claude wrote well enough to own, review, and
defend it in the PR. Claude has no memory across sessions and context gets
summarized, so rationale must come from written records, not recall. This pairs
with the "While building" rules in `.claude/CLAUDE.md`, which produce the plan,
decision log, and prompt log used here.

When I say "review mode" (optionally naming a branch, commit range, or files),
stop writing code and help me understand existing code. Do not modify code in
review mode unless I explicitly ask.

## Triggers
- Sub-commands ("decisions", "trace", "quiz me", "tests", "draft PR",
  "teach-back") only count when prefixed with `review:` (e.g. `review: tests`)
  or once review mode is already on. Otherwise treat them as normal requests.
- Review mode stays on until I say "exit review mode" or "normal mode", or ask
  you to write code. Entering review mode ends learning mode
  (`.claude/modes/learning_mode.md`).

## Scope and sources
- Default scope, if I don't name one: the current branch's diff against the
  repo's main branch (the branch PRs target — check the project's
  `CLAUDE.local.md`, or ask if unclear).
- Before starting, read the plan (`plan.md`), decision log (`decisions.md`),
  and prompt logs (`prompts/`) in the branch's work folder
  (`.claude/work/<branch-name>/`) and any component subfolders, if they exist.
- Tag every claim about *why* something was done with its source:
  **[log]** (decision log, plan, or prompt log), **[code]** (evident from the
  code or comments), or **[inferred]** (your reconstruction). Never present an
  inference as if it were recorded.

## Walkthrough (default)
- Start with a one-paragraph overview of what the change does, then a reading
  order: entry point first, core logic next, supporting changes last.
- Walk through one file or logical unit at a time: what it does, why it exists,
  what calls it, and what it calls. Reference specific functions and line ranges.
- Stop after each unit and wait for me to say "continue" or ask questions.

## "decisions"
- List the significant design decisions, the alternatives that were rejected
  (including dead ends recorded in the decision log), and the tradeoffs involved.
- Rank the riskiest parts of the change and explain why each is risky.
- List edge cases that are handled and, separately, ones that are not.
- If the rationale for something isn't recorded in the decision log or evident
  from the code, say you don't know rather than inventing a reason.

## "trace <scenario>"
Follow one concrete scenario (e.g. "user submits an invalid form") through the
code step by step, naming each function it passes through and how the data
changes along the way.

## "quiz me"
Ask 5–8 questions a skeptical reviewer would ask about this change, one at a
time. Wait for my answer before giving yours, then tell me what I missed or got
wrong.

## "tests"
Summarize what the tests say the intended behavior is. Flag important behavior
that has no test coverage.

## "draft PR"
Write a PR description with: problem, approach and why, a reading guide for
reviewers, risks and how they were tested, and what's out of scope. Follow the
PR description style in `.claude/CLAUDE.md`. Build it from the plan and
decision log first, using the diff to confirm and fill gaps. Mark any claim I
should personally verify before submitting, and any claim tagged [inferred].

## "teach-back"
I explain the change's architecture and reasoning in a few sentences. Tell me
what I got wrong, what I left out, and which parts of the code to revisit.
