#!/usr/bin/env python3
"""AWTT: minimal Claude Code session journal + conservative Git checkpoint.

Install into <git-project>/.claude/hooks/session.py.
No dependencies besides Python 3 and Git. No network calls.
Never runs Git outside the project containing this file.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

PROJECT = Path(__file__).resolve().parents[2]
EVENTS = {"SessionStart", "UserPromptSubmit", "Stop"}
DIRECTORIES = {"src", "tests", "docs", "scripts", "artifacts"}
ROOT_FILES = {"README.md", "CLAUDE.md"}
SENSITIVE_PARTS = {
    ".git", ".claude", ".sessions", ".ssh", ".venv", "node_modules",
    "__pycache__", ".cache", "secrets", "credentials"
}
SENSITIVE_NAMES = {
    "credentials.json", "token.json", "id_rsa", "id_ed25519",
    "known_hosts", "config.xml"
}
SENSITIVE_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".kdbx")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(PROJECT), *args],
        capture_output=True, text=True, errors="replace",
        timeout=30, check=False,
    )


def output(*args: str) -> str | None:
    result = git(*args)
    return result.stdout.strip() if result.returncode == 0 else None


def allowed(path_str: str) -> bool:
    path = PurePosixPath(path_str)
    parts = path.parts
    if not parts or path.is_absolute() or ".." in parts:
        return False
    if any(p in SENSITIVE_PARTS for p in parts):
        return False
    name = parts[-1].lower()
    if name.startswith(".env") or name in SENSITIVE_NAMES:
        return False
    if name.endswith(SENSITIVE_SUFFIXES):
        return False
    if not (parts[0] in DIRECTORIES or path_str in ROOT_FILES):
        return False
    # A symlink could point outside the working tree.
    if (PROJECT / path_str).is_symlink():
        return False
    return True


def checkpoint(session: str) -> dict:
    branch = output("branch", "--show-current")
    if not branch or not branch.startswith("agent/"):
        return {"status": "skipped", "reason": "not_agent_branch"}
    # Do not mix the agent checkpoint with changes the user staged.
    prior = git("diff", "--cached", "--name-only")
    if prior.returncode != 0:
        return {"status": "error", "reason": "cannot_inspect_index"}
    if prior.stdout.strip():
        return {"status": "skipped", "reason": "preexisting_staged_changes"}

    listing = subprocess.run(
        ["git", "-C", str(PROJECT), "ls-files", "-z",
         "--modified", "--deleted", "--others", "--exclude-standard"],
        capture_output=True, check=False, timeout=30,
    )
    if listing.returncode != 0:
        return {"status": "error", "reason": "cannot_list_changes"}
    names = sorted({
        name.decode("utf-8", "surrogateescape")
        for name in listing.stdout.split(b"\0") if name
    })
    candidates = [name for name in names if allowed(name)]
    if not candidates:
        return {"status": "no_eligible_changes"}

    staged = git("add", "-A", "--", *candidates)
    if staged.returncode != 0:
        return {"status": "error", "reason": "git_add_failed",
                "detail": staged.stderr[-300:]}
    now_staged = git("diff", "--cached", "--name-only")
    if now_staged.returncode != 0:
        return {"status": "error", "reason": "cannot_inspect_staged"}
    staged_names = set(filter(None, now_staged.stdout.splitlines()))
    if not staged_names:
        return {"status": "no_eligible_changes"}
    if not staged_names.issubset(set(candidates)):
        return {"status": "error", "reason": "unexpected_staged_files"}

    message = f"checkpoint: {session} {utc_now()}"
    committed = git("commit", "-m", message)
    if committed.returncode != 0:
        return {"status": "error", "reason": "git_commit_failed",
                "detail": committed.stderr[-300:]}
    return {
        "status": "committed",
        "commit": output("rev-parse", "HEAD"),
        "files": sorted(staged_names),
    }


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (OSError, ValueError):
        return
    event = payload.get("hook_event_name")
    if event not in EVENTS:
        return

    cwd = Path(payload.get("cwd") or str(PROJECT)).resolve()
    if cwd != PROJECT and PROJECT not in cwd.parents:
        return

    session = re.sub(
        r"[^A-Za-z0-9_-]", "_",
        str(payload.get("session_id") or "unknown")
    )[:80]
    folder = PROJECT / ".sessions" / session
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)

    item: dict = {
        "timeUTC": utc_now(),
        "sessionId": session,
        "event": event,
        "branch": output("branch", "--show-current"),
    }
    if event == "UserPromptSubmit":
        prompt = str(payload.get("prompt") or "")
        item["promptSha256"] = hashlib.sha256(
            prompt.encode("utf-8")
        ).hexdigest()

    if event == "Stop":
        try:
            item["checkpoint"] = checkpoint(session)
        except Exception as exc:  # Hook must not block the conversation.
            item["checkpoint"] = {
                "status": "error", "reason": type(exc).__name__
            }
        item["gitHead"] = output("rev-parse", "--verify", "HEAD")
        item["gitStatus"] = output("status", "--short")

    with (folder / "events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(item, ensure_ascii=False) + "\n")

    if event == "Stop":
        target = folder / "manifest.json"
        temporary = folder / "manifest.json.tmp"
        temporary.write_text(
            json.dumps(item, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, target)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # The sample must never interrupt Claude's answer.
        sys.exit(0)
