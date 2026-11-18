# Plan: shared, logged Claude workflow for the team

Branch: `AI-launch` (work started on `cet_prototyping_01` and moved here
before the first commit on 2026-11-18; the work folder was renamed to match)
Status: slice 1 done; slice 2 (prompt-logging hook) next

## Goal

Move the personal Claude rules from `~/.claude/CLAUDE.md` into the repo so the
whole team shares them, log every prompt verbatim, and keep each branch's (and
component's) prompts, plan, and decision log together in one folder.

## Target layout

```
.claude/
├── CLAUDE.md                 shared team rules (auto-loaded by Claude Code)
├── settings.json             shared settings: the prompt-logging hook
├── settings.local.json       personal, gitignored (already exists)
├── hooks/
│   └── log_prompt.py         UserPromptSubmit hook
├── modes/
│   ├── review_mode.md        copied from ~/.claude/modes, generalized
│   └── learning_mode.md      copied from ~/.claude/modes, generalized
└── work/
    └── <branch>/
        ├── prompts/          one file per session, written by the hook (edit only to redact)
        │   └── <YYYY-MM-DD>_<HHMM>_<developer>_<session>.md
        ├── decisions.md
        ├── plan.md
        ├── .active_component gitignored, per-developer; names the component in progress
        └── <component>/
            ├── prompts/
            ├── decisions.md
            └── plan.md
```

Branch names containing `/` (e.g. `feature/foo`) become `feature-foo` so they
don't create accidental nesting that looks like a component folder.

## Slice 1: shared instructions

1. `.claude/CLAUDE.md`: copy of `~/.claude/CLAUDE.md` with these changes only:
   - Title and intro describe it as the team's shared rules; add a precedence
     line (repo rules win over any personal/global CLAUDE.md where they
     conflict, e.g. file locations); personal details belong in
     `CLAUDE.local.md`.
   - "While building": replace `.claude/plans/<branch-name>.md` and
     `.claude/decisions/<branch-name>.md` with the `.claude/work/` layout above;
     add the work-folder rule (create on new branch/component, nested
     components, `.active_component`); add the prompt-logging rule.
   - Review / learning mode sections point at `.claude/modes/*.md`.
   - Everything else (code style, Django, PR descriptions) copied verbatim.
     "I/me/my" stays as-is: in a shared file it reads as whoever is driving
     the session.
2. `.claude/modes/review_mode.md` and `learning_mode.md`: copies with path
   references updated (`~/.claude/CLAUDE.md` → `.claude/CLAUDE.md`, plan and
   decision log paths → `.claude/work/...`). Learning mode's personal profile
   ("mid-level developer working in Django and Postgres") is replaced by
   "read the developer's background and goals from `CLAUDE.local.md`; if absent,
   ask once"; the Django/Postgres performance section is kept but scoped to
   projects that use them, with a short general database line for others.
   The TIL file stays personal at `~/.claude/learning/til.md`.
3. `.gitignore`: add `.claude/settings.local.json`, `CLAUDE.local.md`,
   `.claude/work/**/.active_component` (today these are only covered by
   Derya's personal global gitignore, not teammates').
4. Added on approval, then removed: `.gitattributes` with `merge=union`.
   Testing showed union merge silently drops lines that appear in both sides'
   additions (see decisions.md). Replaced by one prompt file per session in
   `prompts/` (can never conflict); `decisions.md` stays one file per folder
   with normal merges.
5. Added on approval: a "Secrets and sensitive data" rule in `.claude/CLAUDE.md`
   (never paste secrets or client data; redact and rotate if it happens;
   review the `prompts/` diff before committing).

Changes from the original plan in slice 1:
- The single `prompts.md` became a `prompts/` folder with one file per session
  (see item 4).
- This session's prompts were backfilled now rather than in slice 2, because
  prompts kept arriving before the hook exists. Timestamps come from the
  session transcript. The new CLAUDE.md fallback rule (Claude
  appends prompts itself when the hook isn't running) covers the gap.
- The secret scanner was **not** added yet. The pre-commit config exists only
  on the unmerged `pre-commit` and `github-actions` branches, so adding a
  `.pre-commit-config.yaml` here would conflict. See "Follow-up when
  pre-commit is merged" below.

## Slice 2: prompt logging

1. `.claude/hooks/log_prompt.py` (Python 3 standard library only, since every
   teammate has Python for this repo):
   - Reads the hook's JSON from stdin (`prompt`, `session_id`, `cwd`).
   - Resolves the branch with `git rev-parse --abbrev-ref HEAD`; detached HEAD
     becomes `detached-<short sha>`; outside a git repo it does nothing.
   - If `.claude/work/<branch>/.active_component` exists, logs to that
     component's `prompts/` folder; otherwise to the branch's. Creates folders
     as needed.
   - Finds this session's file by globbing `*_<first 8 of session id>.md` in
     that folder. If there isn't one, creates
     `<YYYY-MM-DD>_<HHMM>_<developer>_<session>.md` (developer = git
     `user.name`, lowercased, spaces as `-`) with a header naming the branch,
     developer, session, and start time.
   - Appends `## <local YYYY-MM-DD HH:MM>` followed by the prompt verbatim
     inside a code fence longer than any backtick run in the prompt, so pasted
     code or markdown can't break the log.
   - Never prints to stdout (UserPromptSubmit stdout is injected into Claude's
     context) and always exits 0 so a logging failure never blocks a prompt.
2. `.claude/settings.json`: registers the hook with
   `python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/log_prompt.py`.
3. Verify by piping sample JSON into the script: a normal prompt, two prompts
   in the same session (both land in one file), a prompt containing a ```
   fence, an active component set, and a non-git directory.

## Follow-up when pre-commit is merged

The `pre-commit` branch's `.pre-commit-config.yaml` needs two changes before it
lands alongside this work:
- Add a secret scanner, e.g. the `gitleaks` hook
  (`https://github.com/gitleaks/gitleaks`) or `detect-secrets`, covering at
  least `.claude/work/`.
- Exclude `^\.claude/work/.*/prompts/` from `typos`, `trailing-whitespace`,
  and `end-of-file-fixer`. Prompts are logged verbatim, so they'll contain
  typos and trailing spaces; those hooks would fail every commit or rewrite
  the record. (`detect-private-key` should still run on them.)

## Out of scope / for later

- Editing `~/.claude/CLAUDE.md`. The precedence line handles conflicts; trimming
  the now-duplicated global rules is Derya's call.

## Proposals for team discussion

Suggested on 2026-11-18, not adopted yet. Decide as a team; anything adopted
goes into `.claude/CLAUDE.md` or `.claude/settings.json` through a PR.

1. **Share project facts that every session needs.** Put the base branch
   (`main`), the test command, and how to run the API in the shared
   `.claude/CLAUDE.md`. None of these are written down today, and the rules
   currently expect them in each person's `CLAUDE.local.md`.
2. **Share permission rules.** An allow-list (e.g. pytest, read-only git) and a
   deny-list (e.g. `git push --force`, reading `.env`) in `.claude/settings.json`
   so everyone gets the same safety settings.
3. **Link the logs from each PR.** Each PR links its `.claude/work/<branch>/`
   folder next to the AI Disclosure section, so reviewers can see the prompts
   and decisions behind the code.
4. **Change the rules by PR.** Edits to `.claude/CLAUDE.md` and
   `.claude/modes/` go through a PR with at least one teammate's review, the
   same as code.
5. **Require review mode before opening a PR.** The author must be able to
   explain the change without Claude; review mode (`review: teach-back`,
   `review: quiz me`) already supports this.
