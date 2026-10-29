# Deployment

## CI

`.github/workflows/ci.yml` runs ruff and pytest on pushes and pull requests.

## Kalshi collection

Repository variable `DATA_BACKUP_BUCKET` and secret `AWS_ROLE_ARN` are set for AWS OIDC.

`.github/workflows/kalshi-collect.yml` is intended to run on main every six hours or by manual dispatch. Runs serialize without cancellation and time out after 30 minutes.

Set repository variable `DATA_BACKUP_BUCKET` and secret `AWS_ROLE_ARN` for GitHub OIDC; AWS region is `us-west-2`. Storage prefix: `s3://$DATA_BACKUP_BUCKET/cs2-model/kalshi/`.

Each runner should download only `manifest.json`; a missing manifest should fail unless manual dispatch allows a full pull. Collection skips histories listed in the manifest and uploads new trade/candle files, books, catalogs and manifest. Upload should preserve partial progress; sync never deletes remote objects.

## Site feed

`refresh-db.yml` crawls incrementally, rebuilds SQLite and uploads a versioned ratings snapshot hourly. `feed.yml` loads it without a DB, refreshes schedule/prices and publishes every 10 minutes. cron-job.org dispatches both on main; GitHub schedules (`41 * * * *`, `7 * * * *`) are hourly backups. Both allow manual dispatch, serialize without cancellation and use OIDC in us-west-2.

S3 keys under `cs2-model/`: `feed/{state.pkl.gz,predictions.json,cs2.json.gz,upcoming/}`, `liquipedia/` and `kalshi/`. `cs2-model/feed/candidates.json` is private, read by Prometheus’s execution Lambda and uploaded after each public feed. Seed the raw caches in S3 once before refresh; Kalshi books are excluded from runner downloads. Actions caches accelerate raw restores; S3 tops them up. Feed logs use conditional ETag writes; concurrent changes skip saving. Snapshot download failure requires refresh-db first.

Set `PROMETHEUS_DISPATCH_TOKEN` to dispatch `thaiv28/Prometheus`'s `games.yml`; absent tokens skip dispatch and dispatch failures do not fail publication. Workflows have not run on GitHub; runner times remain unmeasured.

## Seeding and local copies

From the repository root, with a completed local backfill and AWS credentials:

```bash
export DATA_BACKUP_BUCKET=shared-artifacts-bucket-name
uv run promcs kalshi manifest
scripts/kalshi_data.sh push
```

The manifest command rebuilds from local histories. `scripts/kalshi_data.sh pull` downloads the archive; `push` uploads it. Neither deletes objects.

## Cost

Estimate: about four runs per day × two minutes ≈ 240 Actions minutes/month; measure after first runs.
