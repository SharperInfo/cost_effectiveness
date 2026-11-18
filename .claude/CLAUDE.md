# Team Claude instructions

Shared rules for everyone using Claude Code in this repository. They're checked in so the whole team works the same way; change them through a PR like any other code.

These rules take precedence over any personal or global CLAUDE.md (e.g. `~/.claude/CLAUDE.md`) where they conflict, such as where plans and logs are stored. Personal details (your background and goals, local environment quirks) go in your own `CLAUDE.local.md` at the repo root, which is gitignored.

## Working style

- Ask clarifying questions instead of assuming. When intent is ambiguous — scope, approach, which files, which behavior — stop and ask before proceeding, rather than guessing or proceeding with "maybes." This applies in planning mode and during implementation.

## While building

### Work folders

All prompts, plans, and decision logs for this repository live under `.claude/work/`, one folder per branch, so any session or teammate can find them without asking.

- When work starts on a new branch, create `.claude/work/<branch-name>/`. Replace any `/` in the branch name with `-` (e.g. `feature/login` → `.claude/work/feature-login/`). Outside a git repo, ask where files should go.
- When I start a distinct component of a feature on that branch, create `.claude/work/<branch-name>/<component-name>/`, using a short kebab-case name for the component (confirm it with me), and write the component name to `.claude/work/<branch-name>/.active_component`. When I switch components, update that file; when I go back to branch-level work, delete it. The file is gitignored because it's per-developer state.
- If work moves to a different branch or the branch is renamed, rename its work folder to match (with `git mv` if already committed) and note the original branch name at the top of `plan.md`.
- Below, `<work-folder>` means the active component's folder if one is set, otherwise the branch folder.

Each work folder holds:
- `prompts/`: one file per Claude session, holding that session's prompts verbatim. Files are named `<YYYY-MM-DD>_<HHMM>_<developer>_<session>.md`: the session's start time, git `user.name` (lowercased, spaces as `-`), and the first 8 characters of the session id. Each file has a single writer, so prompt logs never conflict on merge, and sorting by name gives the history in order.
- `plan.md`: the current plan
- `decisions.md`: the decision log

### Prompt log

- Every prompt is logged verbatim to the current session's file in `<work-folder>/prompts/` by the `UserPromptSubmit` hook configured in `.claude/settings.json` (`.claude/hooks/log_prompt.py`). Don't write to or rewrite these files yourself; the only allowed edit is redacting sensitive data (see below).
- At the start of a session, check that this session's file exists in `<work-folder>/prompts/` and has the first prompt. If it doesn't, tell me the hook isn't running (common causes: the workspace isn't trusted, or `python3` isn't on PATH) and log each prompt yourself until it's fixed, verbatim and in the same format as existing files: a header naming the branch, developer, and session, then each prompt under a `## <YYYY-MM-DD HH:MM>` heading inside a code fence longer than any run of backticks in the prompt. If you don't know the session id, use `manual` in its place.

### Secrets and sensitive data

Prompts are committed to git word-for-word, and git history is permanent.

- Never paste secrets (API keys, passwords, tokens, connection strings, private keys) or client/customer data into a prompt. Refer to them by name or location instead (e.g. "the key in `.env`").
- If a prompt does contain any, tell me immediately. Replace the value in the prompt log with `[REDACTED: <what it was>]` before it's committed, and remind me to rotate the secret. If it was already committed or pushed, the secret must be rotated; redacting the file doesn't remove it from git history.
- Before suggesting a commit that includes `.claude/work/`, review the diff of the `prompts/` files for secrets and sensitive data, and tell me what you checked. Developers should review that diff themselves before committing, too.

### Plans, decisions, and slices

- For any task touching more than ~3 files, write a plan to `<work-folder>/plan.md` first and wait for my approval before coding.
- Keep the plan current: when implementation deviates from it, update the plan and note what changed and why.
- Append significant decisions to `<work-folder>/decisions.md` at the moment they are made, not at the end: decision, reason, alternatives considered. Also log approaches that were tried and abandoned (dead ends), and why.
- Build in slices. At the end of each slice, stop and give me:
  - a short summary of what changed,
  - the files to read, in order, as clickable links,
  - how to verify it works,
  - a suggested commit message.

## Code style

- Use full, descriptive variable names. Never abbreviate (e.g. avoid things like `cz`, `perm`, `val`, `dt`, `b`, `m`). Every name should clearly describe what it holds, so the code stays readable once the context is forgotten. Examples: `customer_zip_code` instead of `czc`, `climate_zone_code` instead of `cz_code`, `permutation` instead of `perm`, and in zip loops `base1_hour, measure_hour` instead of `b, m`.
- Follow DRY principles: before writing new code, search the relevant file and related files for existing helper functions, methods, and utilities that can be reused instead of duplicating logic.
- But don't invent new abstractions to avoid repetition. Write logic inline rather than adding a small helper, closure, or property used in one place — and don't add a property or helper for a one-line expression even when it's repeated in a few places (e.g. inline `f"IP{pk:05d}"` rather than adding a `.reference` property). Reserve new helpers for non-trivial, multi-step logic. Small abstractions make a codebase harder to navigate and maintain; explicit, repeated-but-obvious code is preferred.
- Clean up deprecated or unnecessary code as you go. After a change, check whether it left behind dead code (stubs, old implementations, unused imports/variables) and remove it within reason — don't go far out of scope, but don't leave obvious dead code behind either.

## Django projects

- Never write migration files by hand. Always generate them via `./manage.py makemigrations` / `./manage.py migrate` (or the project's equivalent invocation), either running them directly or asking me to run them. If a hand-written migration already exists, flag it for deletion before regenerating.

## PR descriptions

Write PR descriptions in my own conversational first-person voice, not a bulleted changelog:
- Open with the ticket context ("The next piece of #NNNN" / "PR for the first piece of #NNNN"), then a paragraph or two on what the PR does and why, including scope caveats (what's not included, and which upcoming PR covers it, by number).
- Reference the ticket for field lists rather than repeating them; plain lists are fine when the content is a list.
- A "Testing" section: where reviewers can test, then numbered user-facing steps, plus expected edge-case behavior.
- An "AI Disclosure" section saying honestly what Claude helped with. Leave it as a placeholder for me to confirm unless the extent of Claude's involvement is clear — don't guess.
- Plain-text section headers ("Testing", "AI Disclosure"). No "## Summary" template, no file-by-file breakdown, no "Generated with Claude Code" footer.

## Review mode

- When I say "review mode", or a `review:`-prefixed command (e.g. `review: decisions`, `review: trace`, `review: quiz me`, `review: tests`, `review: draft PR`, `review: teach-back`), first read `.claude/modes/review_mode.md` and follow its instructions.

## Learning mode

- When I say "learning mode", first read `.claude/modes/learning_mode.md` and follow it until I say "normal mode".
