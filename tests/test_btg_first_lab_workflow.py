"""Structural contract tests for the secure BTG first-lab Actions runner."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "btg-first-lab-secure.yml"


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_secure_lab_workflow_is_explicit_push_only() -> None:
    text = _workflow_text()
    assert "lab/btg-s1-first-capture" in text
    assert "config/btg-first-lab-request.json" in text
    assert "workflow_dispatch:" not in text
    assert "pull_request:" not in text
    assert "permissions:\n  contents: read" in text
    assert "cancel-in-progress: false" in text


def test_secure_lab_workflow_pins_execution_revision_and_actions() -> None:
    text = _workflow_text()
    assert "refs/remotes/origin/sprint/1-market-observer" in text
    assert 'ref: ${{ steps.request.outputs.code_revision }}' in text
    assert '--code-revision "${{ steps.request.outputs.code_revision }}"' in text
    assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in text
    assert "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065" in text
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in text


def test_secure_lab_workflow_uses_external_secrets_and_encrypted_artifacts_only() -> None:
    text = _workflow_text()
    assert "secrets.BTG_DATASERVICES_API_KEY" in text
    assert "secrets.BTG_EVIDENCE_PASSPHRASE" in text
    assert "--symmetric --cipher-algo AES256" in text
    assert 'encrypted="${archive}.gpg"' in text
    assert 'sha256sum "$encrypted"' in text
    assert "steps.encrypt.outputs.artifact_path" in text
    assert "btg-evidence-root" not in text.split("Upload encrypted evidence only", 1)[1].split(
        "Enforce successful capture", 1
    )[0]


def test_secure_lab_workflow_does_not_expose_financial_execution_surface() -> None:
    text = _workflow_text().lower()
    forbidden = (
        "order_send",
        "order_check",
        "positions_get",
        "account_info",
        "executionorder",
        "orderintent",
        "orderplan",
        "riskauthorization",
    )
    for token in forbidden:
        assert token not in text
