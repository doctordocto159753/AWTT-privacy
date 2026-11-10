"""Smoke tests for the public sample Hook. Run: python3 -m unittest discover -s tests -v"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples/project-template/.claude/hooks/session.py"


class SessionHookTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name) / "project"
        self.project.mkdir()
        hook_dir = self.project / ".claude/hooks"
        hook_dir.mkdir(parents=True)
        shutil.copyfile(SAMPLE, hook_dir / "session.py")
        (self.project / ".gitignore").write_text(
            ".sessions/\n.env\n.env.*\n", encoding="utf-8"
        )
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "AWTT Test")
        self.git("config", "user.email", "test@example.invalid")
        self.hook = hook_dir / "session.py"

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.project), *args],
            capture_output=True, text=True, check=False
        )

    def event(self, name="Stop", session="smoke"):
        data = {
            "hook_event_name": name,
            "session_id": session,
            "cwd": str(self.project),
            "prompt": "this text must not be logged",
        }
        result = subprocess.run(
            [sys.executable, str(self.hook)], cwd=self.project,
            input=json.dumps(data), capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = self.project / ".sessions" / session / "manifest.json"
        return json.loads(manifest.read_text()) if manifest.exists() else None

    def test_creates_initial_commit_on_agent_branch(self):
        self.git("switch", "-q", "-c", "agent/smoke")
        target = self.project / "artifacts/report.txt"
        target.parent.mkdir()
        target.write_text("hello", encoding="utf-8")
        m = self.event()
        self.assertEqual(m["checkpoint"]["status"], "committed")
        self.assertTrue(m["checkpoint"]["commit"])
        self.assertIn("artifacts/report.txt", self.git(
            "show", "--pretty=format:", "--name-only", "HEAD"
        ).stdout)

    def test_no_changes_does_not_create_second_commit(self):
        self.git("switch", "-q", "-c", "agent/smoke")
        folder = self.project / "docs"
        folder.mkdir()
        (folder / "a.md").write_text("a", encoding="utf-8")
        self.event()
        head_before = self.git("rev-parse", "HEAD").stdout.strip()
        m = self.event()
        self.assertEqual(m["checkpoint"]["status"], "no_eligible_changes")
        self.assertEqual(head_before, self.git("rev-parse", "HEAD").stdout.strip())

    def test_main_branch_never_auto_commits(self):
        folder = self.project / "artifacts"
        folder.mkdir()
        (folder / "a.txt").write_text("a", encoding="utf-8")
        m = self.event()
        self.assertEqual(m["checkpoint"]["reason"], "not_agent_branch")
        self.assertNotEqual(self.git("rev-parse", "--verify", "HEAD").returncode, 0)

    def test_preexisting_staged_changes_are_preserved(self):
        self.git("switch", "-q", "-c", "agent/smoke")
        folder = self.project / "artifacts"
        folder.mkdir()
        (folder / "a.txt").write_text("a", encoding="utf-8")
        self.git("add", "artifacts/a.txt")
        m = self.event()
        self.assertEqual(m["checkpoint"]["reason"], "preexisting_staged_changes")
        self.assertNotEqual(self.git("rev-parse", "--verify", "HEAD").returncode, 0)
        self.assertIn("artifacts/a.txt", self.git(
            "diff", "--cached", "--name-only"
        ).stdout)

    def test_secret_file_not_committed(self):
        self.git("switch", "-q", "-c", "agent/smoke")
        folder = self.project / "artifacts"
        folder.mkdir()
        (folder / ".env").write_text("API_KEY=FAKE", encoding="utf-8")
        (folder / "report.txt").write_text("public", encoding="utf-8")
        m = self.event()
        self.assertEqual(m["checkpoint"]["status"], "committed")
        names = self.git("show", "--pretty=format:", "--name-only", "HEAD").stdout
        self.assertIn("artifacts/report.txt", names)
        self.assertNotIn(".env", names)

    def test_prompt_text_is_not_stored(self):
        self.event(name="UserPromptSubmit")
        log = (self.project / ".sessions/smoke/events.jsonl").read_text()
        self.assertIn("promptSha256", log)
        self.assertNotIn("this text must not be logged", log)


if __name__ == "__main__":
    unittest.main()
