"""Offline checks for the scheduled collector's storage safeguards."""

from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/kalshi-collect.yml"


def test_kalshi_schedule_and_permissions():
    text = WORKFLOW.read_text()
    assert 'cron: "23 */6 * * *"' in text
    assert "workflow_dispatch:" in text
    assert "id-token: write" in text
    assert "if: github.ref == 'refs/heads/main'" in text


def test_kalshi_manifest_guard_and_upload():
    text = WORKFLOW.read_text()
    assert (
        'if [ ! -f data/kalshi/manifest.json ] && [ "$ALLOW_FULL" != "true" ]; then'
        in text
    )
    assert "github.event_name == 'workflow_dispatch' && inputs.allow_full" in text
    assert "Missing manifest.json: seed S3 first" in text
    assert "exit 1" in text
    assert "if: always() && steps.collect.outcome != 'skipped'" in text
    assert "aws s3 cp" in text
    assert "aws s3 sync data/kalshi" in text
    assert "aws s3 sync s3://" not in text
    assert "--delete" not in text
