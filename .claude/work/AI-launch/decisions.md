# Decision log: AI-launch

## 2026-11-18: Shared Claude workflow setup

**Prompt logging uses a UserPromptSubmit hook plus a CLAUDE.md rule.**
Reason: an instruction alone is best-effort; Claude can skip turns, paraphrase,
or lose the rule after context summarization, and it costs a tool call per turn.
A hook runs deterministically on every prompt and records it verbatim.
Alternative considered: CLAUDE.md rule only (rejected for reliability).

**Hook written in Python, not bash + jq.**
Reason: Python 3 is already required for this repo; jq isn't guaranteed on
teammates' machines, and Python makes the fence-length escaping simple.

**Shared instructions live in `.claude/CLAUDE.md`, logs in `.claude/work/`.**
Reason: Claude Code auto-loads `.claude/CLAUDE.md` as project instructions, so
one folder holds rules, settings, hooks, modes, and logs. A `work/` subfolder
keeps per-branch folders from mixing with config files. The old
`.claude/plans/` and `.claude/decisions/` paths are in Derya's global gitignore,
so they couldn't have been shared anyway.

**Components nest inside their branch folder** (`work/<branch>/<component>/`).
Reason: you can always tell which branch a component came from.
Alternative considered: flat sibling folders (rejected: loses branch context).

**Active component is tracked by a gitignored `.active_component` file in the
branch folder.** Reason: the hook can't know what the developer is working on
except from the branch; a per-branch marker lets it route prompts to the right
component folder without leaking one developer's state to others.

**Review and learning modes are copied into `.claude/modes/` and generalized.**
Reason: teammates don't have `~/.claude/modes/`. Learning mode's personal
profile moves to each developer's `CLAUDE.local.md`.

**Append-only logs use git's built-in `merge=union` driver (`.gitattributes`).**
Reason: two people adding to the same branch's `prompts.md` or `decisions.md`
would otherwise conflict at the end of the file on every merge. Tradeoff: union
merge keeps both sides' lines without checking them, so entries from
different people may end up out of time order, and if two people edit the
*same* existing line (rare for append-only files) both versions are kept.
Alternative considered: one log file per developer (rejected: splits the
branch's story across files).

**Dead end (found while testing): `merge=union` silently loses lines.**
Tested by merging two branches that each appended an entry (scratch repo).
Git's union merge treats lines that appear in *both* sides' additions as
shared and keeps one copy. Results:
- Prompt entries in ``` fences: the fence lines collapsed, so Alice's heading
  landed inside Bob's code block.
- Decision prose: both entries ended with "Alternative: none."; only one
  survived, so Bob's entry silently lost a line.
- Entries whose every line was unique merged correctly, but prompt text
  itself can't be guaranteed unique (blank lines, "continue", pasted code).
So union merge can't keep a word-for-word record.

**One prompt file per Claude session; `.gitattributes` removed** (approved by
Derya). Files live in `<work-folder>/prompts/` and are named
`<YYYY-MM-DD>_<HHMM>_<developer>_<session>.md`. Reason: each file has exactly
one writer, so merges never conflict and nothing is lost; names sort into
chronological order. `decisions.md` stays one file per folder with normal git
merges: it should read as one story, concurrent decision entries on the same
branch are rare, and the fix for a conflict is "keep both sides".
Alternatives considered: `merge=union` (dead end above); one log file per
developer (rejected: still conflicts when a developer has parallel sessions or
machines, and doesn't separate sessions).

**Secret scanner deferred to the `pre-commit` branch.** Reason: the
pre-commit config only exists on the unmerged `pre-commit` / `github-actions`
branches; creating one here would conflict. The secrets rule in CLAUDE.md
covers the gap until then. Also found: that config's `typos`,
`trailing-whitespace`, and `end-of-file-fixer` hooks would fail on or rewrite
verbatim prompts, so the `prompts/` files need excluding from them (recorded in the
plan).

**Superseded: the `.gitattributes` / `merge=union` entry above.** Kept for
the record; see the per-session prompt files entry.

**Prompt log backfilled in slice 1, not slice 2.** Reason: prompts kept
arriving before the hook existed. Added a CLAUDE.md fallback rule (Claude
appends prompts itself when the hook isn't running), which also handles a
teammate whose hook isn't working.

**Precedence line instead of editing the global CLAUDE.md.** Reason: every
teammate may have their own global file; a repo-level "these win on conflict"
line resolves path conflicts for everyone without touching personal config.
