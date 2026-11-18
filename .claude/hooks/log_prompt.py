"""Claude Code UserPromptSubmit hook: log every prompt verbatim.

Each Claude session gets its own file, so prompt logs never conflict on merge:

    .claude/work/<branch>/prompts/<YYYY-MM-DD>_<HHMM>_<developer>_<session>.md

If .claude/work/<branch>/.active_component names a component, the prompt goes
to .claude/work/<branch>/<component>/prompts/ instead. See .claude/CLAUDE.md.

Never prints to stdout (Claude Code adds a UserPromptSubmit hook's stdout to
Claude's context) and always exits 0, so a logging failure never blocks a prompt.
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def main():
    hook_input = json.load(sys.stdin)
    prompt = hook_input["prompt"]
    session_id = hook_input.get("session_id") or "unknown"
    working_directory = hook_input.get("cwd") or "."

    repository_root_result = subprocess.run(
        ["git", "-C", working_directory, "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if repository_root_result.returncode != 0:
        return  # Not in a git repo: the rules say to ask where files go, so log nothing.
    repository_root = Path(repository_root_result.stdout.strip())

    # symbolic-ref also works on a new branch with no commits yet.
    branch_result = subprocess.run(
        ["git", "-C", str(repository_root), "symbolic-ref", "--short", "-q", "HEAD"],
        capture_output=True,
        text=True,
    )
    branch_name = branch_result.stdout.strip()
    if not branch_name:
        commit_result = subprocess.run(
            ["git", "-C", str(repository_root), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
        )
        branch_name = f"detached-{commit_result.stdout.strip() or 'unknown'}"

    user_name_result = subprocess.run(
        ["git", "-C", str(repository_root), "config", "user.name"],
        capture_output=True,
        text=True,
    )
    developer_name = user_name_result.stdout.strip() or "unknown"

    branch_folder = repository_root / ".claude" / "work" / branch_name.replace("/", "-")
    work_folder = branch_folder
    active_component_file = branch_folder / ".active_component"
    if active_component_file.is_file():
        component_name = active_component_file.read_text(encoding="utf-8").strip().replace("/", "-")
        if component_name and component_name not in (".", ".."):
            work_folder = branch_folder / component_name

    prompts_folder = work_folder / "prompts"
    prompts_folder.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    session_short_id = session_id[:8]
    existing_session_files = sorted(prompts_folder.glob(f"*_{session_short_id}.md"))
    if existing_session_files:
        session_file = existing_session_files[0]
    else:
        developer_slug = re.sub(r"[^a-z0-9._-]+", "-", developer_name.lower()).strip("-") or "unknown"
        session_file = prompts_folder / f"{now:%Y-%m-%d_%H%M}_{developer_slug}_{session_short_id}.md"
        session_file.write_text(
            f"# Prompt log: session {session_short_id}\n"
            f"\n"
            f"Branch: {branch_name} · Developer: {developer_name} · Started: {now:%Y-%m-%d %H:%M}\n"
            f"\n"
            f"Written by `.claude/hooks/log_prompt.py`. Don't edit except to redact sensitive data.\n",
            encoding="utf-8",
        )

    # A fence longer than any backtick run in the prompt, so pasted code blocks
    # can't close it early.
    longest_backtick_run = max((len(run) for run in re.findall(r"`+", prompt)), default=0)
    fence = "`" * max(3, longest_backtick_run + 1)
    prompt_with_final_newline = prompt if prompt.endswith("\n") else prompt + "\n"
    with session_file.open("a", encoding="utf-8") as session_log:
        session_log.write(f"\n## {now:%Y-%m-%d %H:%M}\n\n{fence}\n{prompt_with_final_newline}{fence}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # Never block the prompt; stderr shows in Claude Code's debug output.
        print(f"log_prompt.py: prompt not logged: {error!r}", file=sys.stderr)
    sys.exit(0)
