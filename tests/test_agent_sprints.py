"""Sprint routing, cumulative patches and durable budgets with real temporary Git trees."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import patch

from scripts import agent_workflow as flow


class SprintTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        for args in (
            ("init", "-q"),
            ("config", "user.name", "Sprint test"),
            ("config", "user.email", "test@example.invalid"),
        ):
            flow.git(self.repo, *args)
        (self.repo / ".gitignore").write_text("artifacts/\n", encoding="utf-8")
        (self.repo / "a.py").write_text("value = 0\n", encoding="utf-8")
        (self.repo / "b.py").write_text("value = 0\n", encoding="utf-8")
        flow.git(self.repo, "add", ".")
        flow.git(self.repo, "commit", "-qm", "fixture")
        sha = flow.git(self.repo, "rev-parse", "HEAD")
        self.manifest: dict[str, Any] = {
            "sprint": "Sprint fixture: authorized correction only",
            "critical_review": True,
            "task": {
                "id": "sprint-fixture",
                "base_sha": sha,
                "reference_sha": sha,
                "authorization": "Local tests",
                "objective": "Correct fixture",
                "allowed_paths": ["a.py", "b.py"],
                "profile": "s8-b01",
            },
            "policy": {"max_ag_calls": 6, "max_codex_calls": 1},
            "work_items": [{"id": "first", "objective": "Correct a", "allowed_paths": ["a.py"]}],
        }
        self.input_path = self.repo / "sprint-input.json"
        self.calls: list[tuple[str, str]] = []
        self.hook: Callable[[str, Path], None] | None = None
        self.review_findings = 0
        self.critical_findings = False
        self.ag_implementations = 0
        self.task = self.repo  # Replaced by init().
        self.worktree = self.repo
        self.check_code = "print('fixture checks observed')"

    def init(self) -> None:
        flow.save(self.input_path, self.manifest)
        self.task = flow.prepare_sprint(self.repo, self.input_path)
        self.worktree = self.task / "worktree"

    def execute(
        self, argv: list[str], cwd: Path, prefix: Path, timeout: int, input_text: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        phase = prefix.name.split("-")[0]
        model = argv[argv.index("--model") + 1]
        self.calls.append((phase, model))
        before = flow.snapshot(cwd)
        if phase == "implement":
            self.ag_implementations += 1
            target = "b.py" if "Correct b" in (input_text or "") else "a.py"
            (cwd / target).write_text(f"value = {self.ag_implementations}\n", encoding="utf-8")
        if self.hook:
            self.hook(phase, cwd)
        findings = []
        if phase == "review" and "read-only" not in argv and self.review_findings:
            findings = ["Reproducible fixture defect"]
            self.review_findings -= 1
        if "read-only" in argv and self.critical_findings:
            findings = ["Critical review still finds a defect"]
        report = {
            "status": "CHANGES_REQUIRED" if findings else "REVIEWED",
            "summary": "Observed fixture",
            "snapshot_hash": before,
            "findings": findings,
            "evidence": ["Read fixture and observed checks"],
        }
        if "-o" in argv:
            flow.save(Path(argv[argv.index("-o") + 1]), report)
            return subprocess.CompletedProcess(argv, 0, "{}", "")
        return subprocess.CompletedProcess(
            argv, 0, json.dumps({"status": "SUCCESS", "structured_output": report}), ""
        )

    def run_sprint(self, allow_codex: bool = False, adopt: bool = False) -> None:
        with (
            patch.object(shutil, "which", side_effect=lambda name: "/fake/" + name),
            patch.object(flow, "agent_command", self.execute),
            patch.object(flow, "checks", return_value=[[sys.executable, "-c", self.check_code]]),
        ):
            flow.run_sprint(self.task, 10, allow_codex, adopt)

    def state(self) -> dict[str, Any]:
        return flow.read(self.task / "sprint-state.json")  # type: ignore[no-any-return]

    def test_ag_default_completes_batch_without_codex_and_resumes_free(self) -> None:
        self.init()
        self.run_sprint()
        self.assertEqual(self.state()["status"], "AWAITING_CRITICAL_REVIEW")
        self.assertEqual(
            self.calls, [("implement", flow.AG_IMPLEMENT_MODEL), ("review", flow.AG_REVIEW_MODEL)]
        )
        self.run_sprint()
        self.assertEqual(len(self.calls), 2)
        self.assertTrue((self.task / "chatgpt-handoff.md").is_file())
        self.assertEqual(flow.sprint_packet(self.task)["calls_reserved"]["codex"], 0)

    def test_codex_used_once_at_critical_gate_and_cached_on_resume(self) -> None:
        self.init()
        self.run_sprint()
        self.run_sprint(allow_codex=True)
        self.assertEqual(self.state()["status"], "READY_FOR_HUMAN")
        self.assertEqual(self.calls[-1], ("review", flow.CODEX_CRITICAL_MODEL))
        self.assertEqual(len(self.calls), 3)
        self.run_sprint(allow_codex=True)
        self.assertEqual(len(self.calls), 3)
        self.assertTrue(flow.sprint_packet(self.task)["critical_review_current"])

    def test_local_failure_uses_ag_fallback_before_any_codex(self) -> None:
        self.check_code = "from pathlib import Path; assert '2' in Path('a.py').read_text()"
        self.init()
        self.run_sprint()
        self.assertEqual(self.state()["status"], "AWAITING_CRITICAL_REVIEW")
        self.assertEqual(
            self.calls,
            [
                ("implement", flow.AG_IMPLEMENT_MODEL),
                ("implement", flow.AG_FALLBACK_MODEL),
                ("review", flow.AG_REVIEW_MODEL),
            ],
        )

    def test_ag_review_findings_trigger_fix_and_new_snapshot_review(self) -> None:
        self.review_findings = 1
        self.init()
        self.run_sprint()
        self.assertEqual(self.state()["status"], "AWAITING_CRITICAL_REVIEW")
        self.assertEqual(self.ag_implementations, 2)
        self.assertEqual(len(self.calls), 4)

    def test_budget_is_persistent_across_resume(self) -> None:
        self.manifest["policy"]["max_ag_calls"] = 1
        self.init()
        self.run_sprint()
        self.assertEqual(self.state()["status"], "NEEDS_ATTENTION")
        self.assertIn("Orçamento", self.state()["reason"])
        self.run_sprint(allow_codex=True)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(len(self.state()["calls"]), 1)

    def test_repeated_test_failures_get_readonly_codex_diagnosis_only_when_enabled(self) -> None:
        self.check_code = "raise SystemExit(7)"
        self.init()
        self.run_sprint()
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.state()["status"], "NEEDS_ATTENTION")
        self.run_sprint(allow_codex=True)
        self.assertEqual(self.calls[-1], ("diagnose", flow.CODEX_CRITICAL_MODEL))
        self.assertEqual(flow.read(self.task / "state.json")["status"], "BLOCKED")
        self.assertFalse(flow.sprint_packet(self.task)["critical_review_current"])
        self.run_sprint(allow_codex=True)
        self.assertEqual(len(self.calls), 3)

    def test_critical_findings_cannot_pass_or_reset_codex_budget(self) -> None:
        self.critical_findings = True
        self.init()
        self.run_sprint(allow_codex=True)
        self.assertEqual(self.state()["status"], "NEEDS_ATTENTION")
        self.assertFalse(flow.sprint_packet(self.task)["critical_review_current"])
        self.run_sprint(allow_codex=True)
        self.assertEqual(len(self.calls), 3)
        self.assertIn("Orçamento", self.state()["reason"])

    def test_ordered_items_share_one_checkout_preserving_prior_patch(self) -> None:
        self.manifest["work_items"].append(
            {
                "id": "second",
                "objective": "Correct b",
                "allowed_paths": ["b.py"],
            }
        )
        self.init()
        self.run_sprint()
        self.assertEqual(self.state()["status"], "AWAITING_CRITICAL_REVIEW")
        self.assertEqual((self.worktree / "a.py").read_text(), "value = 1\n")
        self.assertEqual((self.worktree / "b.py").read_text(), "value = 2\n")
        self.assertEqual([p["phase"] for p in self.state()["items"]], ["DONE", "DONE"])
        self.assertEqual((self.repo / "a.py").read_text(), "value = 0\n")

    def test_item_scope_is_narrower_than_entire_sprint_scope(self) -> None:
        def alter_neighbor(phase: str, cwd: Path) -> None:
            if phase == "implement":
                (cwd / "b.py").write_text("unauthorized for this item\n", encoding="utf-8")

        self.hook = alter_neighbor
        self.init()
        self.run_sprint()
        self.assertIn("fora do item", self.state()["reason"])
        self.assertEqual(len(self.calls), 1)
        self.run_sprint()
        self.assertEqual(len(self.calls), 1)

    def test_external_edits_require_adoption_and_invalidate_cached_checks(self) -> None:
        self.init()
        (self.worktree / "a.py").write_text("manual edit\n", encoding="utf-8")
        self.run_sprint()
        self.assertEqual(len(self.calls), 0)
        self.assertEqual(flow.sprint_packet(self.task)["status"], "STALE")
        self.run_sprint(adopt=True)
        self.assertEqual(self.calls, [("review", flow.AG_REVIEW_MODEL)])
        self.assertEqual(self.state()["status"], "AWAITING_CRITICAL_REVIEW")

    def test_untrusted_external_edits_cannot_be_adopted_for_wrong_item(self) -> None:
        self.init()
        (self.worktree / "b.py").write_text("unexpected\n", encoding="utf-8")
        self.run_sprint(adopt=True)
        self.assertIn("ultrapassa", self.state()["reason"])
        self.assertEqual(self.calls, [])

    def test_check_mutation_stops_without_calling_a_repair_model(self) -> None:
        self.check_code = "from pathlib import Path; Path('a.py').write_text('check mutated')"
        self.init()
        self.run_sprint()
        self.assertIn("Checks alteraram", self.state()["reason"])
        self.assertEqual(len(self.calls), 1)

    def test_reviewer_mutation_never_becomes_accepted_baseline(self) -> None:
        def mutate(phase: str, cwd: Path) -> None:
            if phase == "review":
                (cwd / "a.py").write_text("reviewer changed\n", encoding="utf-8")

        self.hook = mutate
        self.init()
        self.run_sprint()
        self.assertEqual(flow.sprint_packet(self.task)["status"], "STALE")
        self.assertEqual(len(self.calls), 2)
        self.run_sprint()
        self.assertEqual(len(self.calls), 2)

    def test_denied_permission_does_not_trigger_other_models_or_codex(self) -> None:
        self.init()
        with (
            patch.object(shutil, "which", return_value="/fake/agy"),
            patch.object(flow, "agent_command", side_effect=flow.WorkflowError("ação negada")),
        ):
            flow.run_sprint(self.task, 10, allow_codex=True)
        self.assertEqual(len(self.state()["calls"]), 1)
        self.assertEqual(self.state()["calls"][0]["outcome"], "FAILED")
        self.assertIn("ação negada", self.state()["reason"])

    def test_manifest_cannot_disable_critical_review_or_expand_scope(self) -> None:
        self.manifest["critical_review"] = False
        with self.assertRaisesRegex(flow.WorkflowError, "não pode ser dispensada"):
            flow.validate_sprint(self.manifest)
        self.manifest["critical_review"] = True
        self.manifest["work_items"][0]["allowed_paths"] = ["forbidden.py"]
        with self.assertRaisesRegex(flow.WorkflowError, "amplia"):
            flow.validate_sprint(self.manifest)

    def test_manifest_and_budget_cannot_change_after_start(self) -> None:
        self.init()
        mutated = flow.read(self.task / "sprint.json")
        mutated["policy"]["max_codex_calls"] = 2
        flow.save(self.task / "sprint.json", mutated)
        with self.assertRaisesRegex(flow.WorkflowError, "Manifesto mudou"):
            flow.load_sprint(self.task)

    def test_interrupted_call_is_not_silently_reissued(self) -> None:
        self.init()
        state = self.state()
        state["calls"] = [{"provider": "antigravity", "outcome": "RUNNING"}]
        flow.save_sprint(self.task, state)
        self.run_sprint(allow_codex=True)
        self.assertIn("sem resultado", self.state()["reason"])
        self.assertEqual(len(self.calls), 0)

    def test_cli_review_defaults_to_antigravity(self) -> None:
        self.init()
        standalone = {**self.manifest["task"], "id": "standalone"}
        flow.save(self.input_path, standalone)
        flow.prepare(self.repo, self.input_path)
        with patch.object(flow, "run_agent") as mocked:
            result = flow.main(["--repo", str(self.repo), "review", "standalone"])
        self.assertEqual(result, 0)
        self.assertEqual(mocked.call_args.args[3:5], ("antigravity", flow.AG_REVIEW_MODEL))

    def test_sprint_task_cannot_bypass_budget_via_standalone_cli(self) -> None:
        self.init()
        with patch.object(flow, "run_agent") as mocked:
            result = flow.main(
                ["--repo", str(self.repo), "review", "sprint-fixture", "--provider", "codex"]
            )
        self.assertEqual(result, 2)
        mocked.assert_not_called()

    def add_local_remote(self) -> Path:
        remote = self.repo / "artifacts" / "remote.git"
        remote.parent.mkdir(exist_ok=True)
        flow.git(self.repo, "init", "--bare", "-q", str(remote))
        flow.git(self.repo, "remote", "add", "origin", str(remote))
        return remote

    def test_github_sync_only_publishes_evidence_and_preserves_source_head_and_index(self) -> None:
        self.init()
        self.add_local_remote()
        self.run_sprint()
        before = flow.snapshot(self.worktree)
        source_head = flow.git(self.repo, "rev-parse", "HEAD")
        branch = flow.sync_sprint(self.repo, self.task)
        self.assertEqual(branch, "workflow-status/sprint-fixture")
        self.assertEqual(flow.snapshot(self.worktree), before)
        self.assertEqual(flow.git(self.repo, "rev-parse", "HEAD"), source_head)
        refs = flow.git(self.repo, "ls-remote", "--heads", "origin")
        self.assertEqual(len(refs.splitlines()), 1)
        commit = refs.split()[0]
        names = flow.git(self.repo, "ls-tree", "-r", "--name-only", commit).splitlines()
        self.assertEqual(
            set(names),
            {"README.md", "STATE.json", "MANIFEST.json", "chatgpt-handoff.md", "candidate.patch"},
        )
        published = json.loads(flow.git(self.repo, "show", commit + ":STATE.json"))
        self.assertEqual(published["snapshot_hash"], before)
        self.assertEqual(published["calls_reserved"]["codex"], 0)
        self.assertIn("value = 1", flow.git(self.repo, "show", commit + ":candidate.patch"))

    def test_sync_updates_existing_branch_without_losing_parent_history(self) -> None:
        self.init()
        self.add_local_remote()
        flow.sync_sprint(self.repo, self.task)
        first = self.state()["github_last_commit"]
        self.run_sprint()
        flow.sync_sprint(self.repo, self.task)
        second = self.state()["github_last_commit"]
        self.assertEqual(flow.git(self.repo, "rev-parse", second + "^"), first)

    def test_sync_includes_permitted_new_files_without_staging_them(self) -> None:
        self.manifest["task"]["allowed_paths"].append("new.py")
        self.manifest["work_items"][0]["allowed_paths"].append("new.py")
        self.init()
        self.add_local_remote()
        (self.worktree / "new.py").write_text("new_value = 42\n", encoding="utf-8")
        self.run_sprint(adopt=True)
        before_index = flow.git(self.worktree, "ls-files", "--stage")
        flow.sync_sprint(self.repo, self.task)
        commit = self.state()["github_last_commit"]
        self.assertIn("new_value = 42", flow.git(self.repo, "show", commit + ":candidate.patch"))
        self.assertEqual(flow.git(self.worktree, "ls-files", "--stage"), before_index)

    def test_sync_rejects_stale_and_out_of_scope_edits(self) -> None:
        self.init()
        self.add_local_remote()
        (self.worktree / "a.py").write_text("unadmitted edit\n", encoding="utf-8")
        with self.assertRaisesRegex(flow.WorkflowError, "não admitido"):
            flow.sync_sprint(self.repo, self.task)
        self.assertEqual(flow.git(self.repo, "ls-remote", "--heads", "origin"), "")

    def test_sync_refuses_existing_branch_with_unrelated_files(self) -> None:
        self.init()
        self.add_local_remote()
        flow.sync_sprint(self.repo, self.task)
        prior = self.state()["github_last_commit"]
        # A source commit is fast-forward unrelated only on a fresh remote branch fixture.
        other = "workflow-status/other"
        flow.git(self.repo, "push", "origin", "HEAD:refs/heads/" + other)
        flow.git(self.repo, "fetch", "origin", other)
        branch = "refs/heads/workflow-status/sprint-fixture"
        # Replace test remote ref directly; the workflow itself never force-pushes.
        remote = self.repo / "artifacts/remote.git"
        flow.git(remote, "update-ref", branch, flow.git(self.repo, "rev-parse", "HEAD"), prior)
        with self.assertRaises(flow.WorkflowError):
            flow.sync_sprint(self.repo, self.task)


if __name__ == "__main__":
    unittest.main()
