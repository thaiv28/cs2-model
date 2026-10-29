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


def test_site_workflow_guards():
    for name, cron, timeout in (
        ("refresh-db", "41 * * * *", 45),
        ("feed", "7 * * * *", 15),
    ):
        text = (WORKFLOW.parent / f"{name}.yml").read_text()
        assert f'cron: "{cron}"' in text
        assert "workflow_dispatch:" in text
        assert "if: github.ref == 'refs/heads/main'" in text
        assert "contents: read" in text
        assert "id-token: write" in text
        assert f"group: {name}" in text
        assert "cancel-in-progress: false" in text
        assert f"timeout-minutes: {timeout}" in text
        assert "role-to-assume: ${{ secrets.AWS_ROLE_ARN }}" in text
        assert "aws-region: us-west-2" in text
        assert "uv sync --frozen --no-dev" in text
        assert "--delete" not in text


def test_refresh_storage_and_incremental_crawl():
    text = (WORKFLOW.parent / "refresh-db.yml").read_text()
    assert "actions/cache/restore@v4" in text
    assert "actions/cache/save@v4" in text
    assert "key: raw-${{ github.run_id }}" in text
    assert "restore-keys: raw-" in text
    assert "steps.crawl.outputs.changed == 'true'" in text
    assert "steps.raw.outputs.cache-matched-key" in text
    assert "find data/liquipedia data/kalshi -newer /tmp/raw-marker" in text
    assert "uv run promcs liquipedia crawl" in text
    assert "--full" not in text
    assert "s3://$BUCKET/cs2-model/liquipedia" in text
    assert "s3://$BUCKET/cs2-model/kalshi" in text
    assert '--exclude "books/*"' in text
    assert "--size-only" in text
    assert "bash scripts/setup_db.sh" in text
    assert "uv run promcs feed-state" in text
    assert "s3://$BUCKET/cs2-model/feed/state.pkl.gz" in text


def test_feed_storage_and_dispatch():
    text = (WORKFLOW.parent / "feed.yml").read_text()
    assert "s3://$BUCKET/cs2-model/feed/state.pkl.gz" in text
    assert "run refresh-db first" in text
    assert "bash scripts/feed_data.sh restore" in text
    assert "bash scripts/feed_data.sh save" in text
    assert text.count("s3://$BUCKET/cs2-model/feed/upcoming") == 2
    assert (
        "uv run promcs export --state data/feed/state.pkl.gz --out data/feed/cs2.json"
        in text
    )
    assert (
        'aws s3 cp data/feed/candidates.json "s3://$BUCKET/cs2-model/feed/candidates.json" --content-type application/json --only-show-errors'
        in text
    )
    assert "gzip -9 -c" in text
    assert "s3://$BUCKET/cs2-model/feed/cs2.json.gz" in text
    assert "--content-type application/json" in text
    assert "gh workflow run games.yml -R thaiv28/Prometheus --ref main" in text
    assert "if: env.HAS_DISPATCH == 'true'" in text
    assert "HAS_DISPATCH: ${{ secrets.PROMETHEUS_DISPATCH_TOKEN != '' }}" in text
    assert "GH_TOKEN: ${{ secrets.PROMETHEUS_DISPATCH_TOKEN }}" in text
    assert "continue-on-error: true" in text
    assert "setup_db.sh" not in text
    assert "PROMCS_DATA" not in text


def test_feed_data_bash_syntax():
    import subprocess

    subprocess.run(
        ["bash", "-n", str(WORKFLOW.parents[2] / "scripts/feed_data.sh")], check=True
    )


def refresh_steps():
    text = (WORKFLOW.parent / "refresh-db.yml").read_text()
    return text.split("      - ")[1:]


def test_refresh_database_input_cache():
    steps = refresh_steps()
    inputs = next(step for step in steps if "id: inputs\n" in step)
    assert "hashFiles('scripts/**', 'promcs/**', 'uv.lock')" in inputs
    assert (
        "find data/liquipedia data/kalshi -type f -not -path '*/books/*' "
        "-print0 | LC_ALL=C sort -z | xargs -0 sha256sum" in inputs
    )
    assert "printf '%s\\n' \"$CODE_HASH\"" in inputs
    assert "sha256sum" in inputs
    caches = [step for step in steps if "key: db-" in step]
    assert len(caches) == 2
    for step in caches:
        assert "path: db\n" in step
        assert "key: db-${{ steps.inputs.outputs.hash }}" in step
        assert "restore-keys:" not in step
    assert "actions/cache/restore@v4" in caches[0]
    assert "actions/cache/save@v4" in caches[1]


def test_refresh_rebuild_requires_cache_and_published_state():
    steps = refresh_steps()
    skip = next(step for step in steps if "id: skip\n" in step)
    assert "steps.database.outputs.cache-hit" in skip
    assert "--key cs2-model/feed/state.pkl.gz --query Metadata.inputs" in skip
    assert 'if [ "$DB_HIT" = true ] && [ "$published" = "$INPUTS" ]; then' in skip
    assert "Unchanged inputs; skipped rebuild" in skip
    for command in (
        "bash scripts/setup_db.sh",
        "uv run promcs feed-state",
        "actions/cache/save@v4\n",
        "uv run promcs blend-artifact",
    ):
        matching = [
            step for step in steps if command in step and "key: raw-" not in step
        ]
        assert len(matching) == 1
        assert "if: steps.skip.outputs.unchanged != 'true'" in matching[0]
    state = next(step for step in steps if "uv run promcs feed-state" in step)
    assert '--metadata inputs="$INPUTS"' in state
    artifact = next(step for step in steps if "uv run promcs blend-artifact" in step)
    assert "--out data/feed/blend_artifact.json" in artifact
    assert (
        'aws s3 cp data/feed/blend_artifact.json "s3://$BUCKET/cs2-model/feed/blend_artifact.json" --content-type application/json --only-show-errors'
        in artifact
    )
    assert "Artifact snapshots:" in artifact
    assert "DB build:" in skip
    assert "Raw cache:" in skip
    assert "DB cache:" in skip


def test_refresh_seed_guards_and_raw_save_order():
    steps = refresh_steps()
    download = next(step for step in steps if "name: Seed cold raw cache" in step)
    assert "if: steps.raw.outputs.cache-matched-key == ''" in download
    assert "continue-on-error: true" in download
    assert (
        'aws s3 cp "s3://$BUCKET/cs2-model/seed/raw.tar.zst" - | tar -I zstd -xf -'
        in download
    )
    crawl = next(step for step in steps if "id: crawl\n" in step)
    raw_save = next(step for step in steps if "id: raw-save\n" in step)
    weekly = next(step for step in steps if "name: Refresh weekly seed" in step)
    build = next(step for step in steps if "bash scripts/setup_db.sh" in step)
    assert steps.index(download) < steps.index(crawl) < steps.index(raw_save)
    assert steps.index(raw_save) < steps.index(build)
    assert "if: steps.crawl.outputs.changed == 'true'" in raw_save
    assert "if: steps.raw-save.outcome == 'success'" in weekly
    assert "continue-on-error: true" in weekly
    assert "--key cs2-model/seed/raw.tar.zst --query LastModified" in weekly
    assert '[ -z "$modified" ]' in weekly
    assert "-gt 604800" in weekly
    assert "tar -I 'zstd -T0 -3' -cf - --exclude='*/books/*'" in weekly
    assert "--expected-size 3000000000 --only-show-errors" in weekly
