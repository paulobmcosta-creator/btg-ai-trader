"""Workflow failure and provenance tests using temporary Git repositories."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from scripts import agent_workflow as flow


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.email", "workflow-test@example.invalid")
        self.git("config", "user.name", "Workflow Test")
        (self.repo / ".gitignore").write_text("artifacts/\n__pycache__/\n", encoding="utf-8")
        (self.repo / "src").mkdir()
        (self.repo / "src/allowed.py").write_text("value = 1\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        self.sha = self.git("rev-parse", "HEAD")
        self.spec: dict[str, Any] = {
            "id": "fixture-task",
            "base_sha": self.sha,
            "reference_sha": self.sha,
            "authorization": "Local test only",
            "objective": "Inspect fixture",
            "allowed_paths": ["src/allowed.py"],
            "profile": "s8-b01",
        }
        self.spec_path = self.repo / "spec.json"
        flow.save(self.spec_path, self.spec)
        self.task = flow.prepare(self.repo, self.spec_path)
        self.worktree = self.task / "worktree"

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def successful_checks(self) -> None:
        with patch.object(
            flow, "checks", return_value=[[sys.executable, "-c", "print('checked')"]]
        ):
            flow.check_task(self.task, self.worktree, self.spec, 10)

    def report(self, fingerprint: str) -> dict[str, object]:
        return {
            "status": "REVIEWED",
            "summary": "Fixture inspected",
            "snapshot_hash": fingerprint,
            "findings": [],
            "evidence": ["Observed fixture source"],
        }

    def test_prepare_is_isolated_and_resumable_without_overwrite(self) -> None:
        self.assertEqual(flow.git(self.worktree, "rev-parse", "HEAD"), self.sha)
        self.assertTrue((self.task / "handoff.md").is_file())
        self.assertEqual(flow.read(self.task / "state.json")["status"], "READY")
        with self.assertRaisesRegex(flow.WorkflowError, "já existe"):
            flow.prepare(self.repo, self.spec_path)

    def test_snapshot_detects_tracked_untracked_and_index_changes(self) -> None:
        before = flow.snapshot(self.worktree)
        source = self.worktree / "src/allowed.py"
        source.write_text("value = 2\n", encoding="utf-8")
        modified = flow.snapshot(self.worktree)
        self.assertNotEqual(before, modified)
        flow.git(self.worktree, "add", "src/allowed.py")
        self.assertNotEqual(modified, flow.snapshot(self.worktree))
        extra = self.worktree / " extra.txt"
        extra.write_text("new", encoding="utf-8")
        with_extra = flow.snapshot(self.worktree)
        extra.write_text("changed", encoding="utf-8")
        self.assertNotEqual(with_extra, flow.snapshot(self.worktree))

    def test_scope_detects_unauthorized_and_untracked_paths(self) -> None:
        (self.worktree / "forbidden.py").write_text("unexpected", encoding="utf-8")
        with self.assertRaisesRegex(flow.WorkflowError, "fora do escopo"):
            flow.enforce_scope(self.worktree, self.spec)

    def test_scope_prefix_does_not_match_neighbor_directory(self) -> None:
        spec = {**self.spec, "allowed_paths": ["src/"]}
        (self.worktree / "src2").mkdir()
        (self.worktree / "src2/other.py").write_text("unexpected", encoding="utf-8")
        with self.assertRaises(flow.WorkflowError):
            flow.enforce_scope(self.worktree, spec)

    def test_scope_rejects_new_head(self) -> None:
        flow.git(self.worktree, "commit", "--allow-empty", "-qm", "unexpected")
        with self.assertRaisesRegex(flow.WorkflowError, "HEAD mudou"):
            flow.enforce_scope(self.worktree, self.spec)

    def test_check_failure_cannot_claim_success(self) -> None:
        with patch.object(
            flow, "checks", return_value=[[sys.executable, "-c", "raise SystemExit(9)"]]
        ):
            with self.assertRaises(flow.WorkflowError):
                flow.check_task(self.task, self.worktree, self.spec, 10)
        evidence = flow.read(self.task / "checks.json")
        self.assertFalse(evidence["passed"])
        self.assertEqual(evidence["results"][0]["exit_code"], 9)

    def test_check_mutation_invalidates_evidence(self) -> None:
        code = "from pathlib import Path; Path('src/allowed.py').write_text('changed')"
        with patch.object(flow, "checks", return_value=[[sys.executable, "-c", code]]):
            with self.assertRaises(flow.WorkflowError):
                flow.check_task(self.task, self.worktree, self.spec, 10)
        self.assertFalse(flow.read(self.task / "checks.json")["passed"])

    def test_stale_checks_block_review(self) -> None:
        self.successful_checks()
        (self.worktree / "src/allowed.py").write_text("changed", encoding="utf-8")
        with patch.object(shutil, "which", return_value="/fake/codex"):
            with self.assertRaisesRegex(flow.WorkflowError, "snapshot atual"):
                flow.run_agent(self.task, self.worktree, self.spec, "codex", "test-model", 10)

    def test_report_must_match_snapshot_and_contain_observed_evidence(self) -> None:
        report = self.report("expected")
        with self.assertRaisesRegex(flow.WorkflowError, "outro snapshot"):
            flow.validate_report(report, "new")
        report["evidence"] = []
        with self.assertRaises(flow.WorkflowError):
            flow.validate_report(report, "expected")
        report = self.report("expected")
        report["findings"] = ["Unresolved finding"]
        with self.assertRaises(flow.WorkflowError):
            flow.validate_report(report, "expected")

    def test_reviewed_with_findings_requests_changes_and_preserves_original(self) -> None:
        fingerprint = flow.snapshot(self.worktree)
        report = self.report(fingerprint)
        report["findings"] = ["CI e revisão do commit ainda pendentes."]
        output = self.task / "review-01.json"
        flow.save(output, report)
        flow.accept_report(
            self.task, output, "codex", "test-model", fingerprint, fingerprint, False
        )
        self.assertEqual(flow.read(output)["status"], "REVIEWED")
        assessed = flow.read(self.task / "latest-agent.json")
        self.assertEqual(assessed["report"]["status"], "CHANGES_REQUIRED")
        self.assertEqual(assessed["report"]["findings"], report["findings"])
        self.assertEqual(flow.read(self.task / "state.json")["status"], "CHANGES_REQUIRED")
        next_output = self.task / "review-02.json"
        flow.save(next_output, self.report(fingerprint))
        flow.accept_report(
            self.task, next_output, "antigravity", "test-model", fingerprint, fingerprint, False
        )
        self.assertEqual(flow.read(self.task / "state.json")["status"], "CHANGES_REQUIRED")

    def test_antigravity_empty_response_with_denied_command_stays_blocked(self) -> None:
        actual_shape = {
            "conversation_id": "fixture",
            "status": "SUCCESS",
            "response": "",
            "denied_actions": [{"action": "command", "display_name": "RunCommand"}],
        }
        with self.assertRaisesRegex(flow.WorkflowError, "ação negada"):
            flow.parse_antigravity(json.dumps(actual_shape))

    def test_antigravity_json_response_fallback_still_requires_valid_schema(self) -> None:
        report = self.report("expected")
        for payload in (json.dumps(report), "```json\n" + json.dumps(report) + "\n```"):
            parsed = flow.parse_antigravity(json.dumps({"status": "SUCCESS", "response": payload}))
            flow.validate_report(parsed, "expected")
        with self.assertRaisesRegex(flow.WorkflowError, "não concluída"):
            flow.parse_antigravity(json.dumps({"status": "WAITING", "structured_output": report}))
        with self.assertRaises(flow.WorkflowError):
            flow.parse_antigravity('{"status":"SUCCESS","response":""}')

    def test_replay_reuses_completed_inventory_without_calling_cli(self) -> None:
        spec = {**self.spec, "allowed_paths": []}
        self.successful_checks()
        fingerprint = flow.snapshot(self.worktree)
        report = self.report(fingerprint)
        report["findings"] = ["Evidência de CI ainda pendente."]
        flow.save(self.task / "review-01.json", report)
        (self.task / "review-01.stdout.txt").write_text(
            '{"type":"turn.started"}\n{"type":"turn.completed"}\n', encoding="utf-8"
        )
        flow.transition(self.task, "BLOCKED", agent_attempts=1)
        with patch.object(flow, "agent_command", side_effect=AssertionError("No generation")):
            flow.replay_review(self.task, self.worktree, spec, "codex", "test-model", 1)
        self.assertEqual(flow.read(self.task / "state.json")["status"], "CHANGES_REQUIRED")
        self.assertEqual(flow.read(self.task / "state.json")["agent_attempts"], 1)
        (self.task / "review-01.stdout.txt").write_text('{"type":"turn.failed"}', encoding="utf-8")
        with self.assertRaisesRegex(flow.WorkflowError, "conclusão"):
            flow.replay_review(self.task, self.worktree, spec, "codex", "test-model", 1)

    def test_inventory_brief_supplies_evidence_without_requesting_commands(self) -> None:
        (self.worktree / "AGENTS.md").write_text("Norma para o inventário.", encoding="utf-8")
        packet = flow.inventory_brief(self.spec, self.worktree, "expected")
        self.assertIn("NÃO use ferramentas", packet)
        self.assertIn("1: Norma para o inventário.", packet)
        self.assertIn("snapshot_hash obrigatório: expected", packet)
        self.assertIn("Arquivo indisponível no pacote", packet)

    def test_successful_review_produces_human_handoff_without_gate_closure(self) -> None:
        self.successful_checks()

        def execute(
            argv: list[str], cwd: Path, prefix: Path, timeout: int, input_text: str | None = None
        ) -> subprocess.CompletedProcess[str]:
            self.assertIn("read-only", argv)
            self.assertEqual(argv[-1], "-")
            self.assertIn("Tarefa: fixture-task", input_text or "")
            flow.save(Path(argv[argv.index("-o") + 1]), self.report(flow.snapshot(cwd)))
            return subprocess.CompletedProcess(argv, 0, "{}", "")

        with (
            patch.object(shutil, "which", return_value="/fake/codex"),
            patch.object(flow, "agent_command", execute),
        ):
            flow.run_agent(self.task, self.worktree, self.spec, "codex", "test-model", 10)
        self.assertEqual(flow.read(self.task / "state.json")["status"], "READY_FOR_HUMAN")
        self.assertEqual(flow.git(self.worktree, "rev-parse", "HEAD"), self.sha)

    def test_zero_exit_without_report_is_not_success(self) -> None:
        self.successful_checks()

        def execute(
            argv: list[str], cwd: Path, prefix: Path, timeout: int, input_text: str | None = None
        ) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(argv, 0, "{}", "permission denied")

        with (
            patch.object(shutil, "which", return_value="/fake/codex"),
            patch.object(flow, "agent_command", execute),
        ):
            with self.assertRaisesRegex(flow.WorkflowError, "relatório esperado"):
                flow.run_agent(self.task, self.worktree, self.spec, "codex", "test-model", 10)

    def test_missing_cli_keeps_manual_handoff(self) -> None:
        with patch.object(shutil, "which", return_value=None):
            with self.assertRaisesRegex(flow.WorkflowError, "CLI ausente"):
                flow.run_agent(self.task, self.worktree, self.spec, "antigravity", "test-model", 10)
        self.assertTrue((self.task / "handoff.md").is_file())

    def test_antigravity_analysis_accepts_only_structured_success(self) -> None:
        self.successful_checks()

        def execute(
            argv: list[str], cwd: Path, prefix: Path, timeout: int, input_text: str | None = None
        ) -> subprocess.CompletedProcess[str]:
            self.assertIn("--sandbox", argv)
            envelope = {"status": "SUCCESS", "structured_output": self.report(flow.snapshot(cwd))}
            return subprocess.CompletedProcess(argv, 0, json.dumps(envelope), "")

        with (
            patch.object(shutil, "which", return_value="/fake/agy"),
            patch.object(flow, "agent_command", execute),
        ):
            flow.run_agent(self.task, self.worktree, self.spec, "antigravity", "test-model", 10)
        self.assertEqual(flow.read(self.task / "state.json")["status"], "READY_FOR_HUMAN")

        with (
            patch.object(shutil, "which", return_value="/fake/agy"),
            patch.object(
                flow,
                "agent_command",
                return_value=subprocess.CompletedProcess(
                    ["agy"],
                    0,
                    '{"status":"SUCCESS","response":"tools denied"}',
                    "permission denied",
                ),
            ),
        ):
            with self.assertRaisesRegex(flow.WorkflowError, "resultado estruturado"):
                flow.run_agent(self.task, self.worktree, self.spec, "antigravity", "test-model", 10)

    def test_readonly_inventory_cannot_be_implemented(self) -> None:
        with patch.object(shutil, "which", return_value="/fake/agy"):
            with self.assertRaisesRegex(flow.WorkflowError, "somente leitura"):
                flow.run_agent(
                    self.task,
                    self.worktree,
                    {**self.spec, "allowed_paths": []},
                    "antigravity",
                    "test-model",
                    10,
                    implement=True,
                )

    def test_agent_timeout_preserves_diagnostics(self) -> None:
        prefix = self.task / "timeout-test"
        code = "import time; print('started', flush=True); time.sleep(5)"
        with self.assertRaisesRegex(flow.WorkflowError, "logs preservados"):
            flow.agent_command([sys.executable, "-c", code], self.worktree, prefix, 1)
        self.assertIn("started", prefix.with_suffix(".stdout.txt").read_text())

    def test_large_prompt_uses_stdin_not_windows_command_line(self) -> None:
        self.successful_checks()
        packet = 'Evidência com acentos, espaços e símbolos & | "\n' * 3000

        def execute(
            argv: list[str], cwd: Path, prefix: Path, timeout: int, input_text: str | None = None
        ) -> subprocess.CompletedProcess[str]:
            self.assertNotIn("-p", argv)
            self.assertIn("--input-format", argv)
            self.assertEqual(argv[argv.index("--input-format") + 1], "stream-json")
            self.assertEqual(argv[argv.index("--output-format") + 1], "stream-json")
            self.assertLess(len(subprocess.list2cmdline(argv).encode("utf-16-le")), 10000)
            event = json.loads(input_text or "")
            self.assertEqual(event, {"event": "user", "message": {"content": packet}})
            envelope = {
                "event": "result",
                "result": {
                    "status": "SUCCESS",
                    "structured_output": self.report(flow.snapshot(cwd)),
                },
            }
            stdout = json.dumps({"event": "init"}) + "\n" + json.dumps(envelope) + "\n"
            return subprocess.CompletedProcess(argv, 0, stdout, "")

        with (
            patch.object(shutil, "which", return_value="/fake/agy"),
            patch.object(flow, "inventory_brief", return_value=packet),
            patch.object(flow, "agent_command", execute),
        ):
            spec = {**self.spec, "allowed_paths": [], "profile": "s8-inventory"}
            flow.run_agent(self.task, self.worktree, spec, "antigravity", "test-model", 10)
        self.assertEqual(flow.read(self.task / "state.json")["status"], "READY_FOR_HUMAN")
        meta = flow.read(self.task / "review-01.request.json")
        self.assertEqual(meta["transport"], "stdin-jsonl")
        self.assertEqual(meta["prompt_characters"], len(packet))

    def test_real_subprocess_preserves_large_utf8_stdin(self) -> None:
        packet: dict[str, Any] = {"event": "user", "message": {"content": 'á & | "\n' * 10000}}
        code = (
            "import sys,json; value=json.loads(sys.stdin.buffer.read().decode('utf8')); "
            "print(len(value['message']['content']))"
        )
        result = flow.agent_command(
            [sys.executable, "-c", code],
            self.worktree,
            self.task / "stdin-test",
            10,
            input_text=json.dumps(packet, ensure_ascii=False) + "\n",
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(int(result.stdout.strip()), len(packet["message"]["content"]))

    def test_stream_requires_one_complete_result_and_preserves_denials(self) -> None:
        envelope: dict[str, Any] = {
            "event": "result",
            "result": {"status": "SUCCESS", "structured_output": self.report("expected")},
        }
        complete = json.dumps(envelope)
        flow.validate_report(flow.parse_antigravity(complete), "expected")
        for stream in (
            '{"event":"init"}\n{"event":"step_update"}\n',
            complete + "\n" + complete + "\n",
            complete + '\n{"event":"step_update"}\n',
            '{"event":"result","result":{"status":"ERROR"}}',
        ):
            with self.assertRaises(flow.WorkflowError):
                flow.parse_antigravity(stream)
        envelope["result"]["denied_actions"] = [{"action": "command"}]
        with self.assertRaisesRegex(flow.WorkflowError, "ação negada"):
            flow.parse_antigravity('{"event":"init"}\n' + json.dumps(envelope))

    def test_changed_snapshot_marks_finished_review_stale(self) -> None:
        self.successful_checks()
        fingerprint = flow.snapshot(self.worktree)
        flow.save(self.task / "latest-agent.json", {"output_hash": fingerprint})
        flow.transition(self.task, "READY_FOR_HUMAN")
        (self.worktree / "src/allowed.py").write_text("value = 99", encoding="utf-8")
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(flow.main(["--repo", str(self.repo), "status", self.spec["id"]]), 0)
        self.assertIn('"status": "STALE"', output.getvalue())

    def test_lock_rejects_concurrent_execution_and_is_released(self) -> None:
        with flow.lock(self.task):
            with self.assertRaises(flow.WorkflowError):
                with flow.lock(self.task):
                    self.fail("Concurrent lock was accepted")
        self.assertFalse((self.task / ".lock").exists())

    def test_task_id_and_paths_cannot_escape_workspace(self) -> None:
        for task_id in ("../other", "-option", "a/b"):
            with self.assertRaises(flow.WorkflowError):
                flow.task_paths(self.repo, task_id)
        for name in ("../other", "/root", ".git/config", "a\\b"):
            with self.assertRaises(flow.WorkflowError):
                flow.validate_spec({**self.spec, "allowed_paths": [name]})

    def test_timeout_and_invalid_json_stop_main_with_persisted_reason(self) -> None:
        with patch.object(flow, "check_task", side_effect=flow.WorkflowError("Timeout fixture")):
            self.assertEqual(flow.main(["--repo", str(self.repo), "check", self.spec["id"]]), 2)
        self.assertEqual(flow.read(self.task / "state.json")["status"], "BLOCKED")
        (self.task / "task.json").write_text("{invalid", encoding="utf-8")
        self.assertEqual(flow.main(["--repo", str(self.repo), "export", self.spec["id"]]), 2)
        self.assertFalse((self.task / ".lock").exists())


if __name__ == "__main__":
    unittest.main()
