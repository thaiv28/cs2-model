# Deployment

## CI

`.github/workflows/ci.yml` runs ruff and pytest on pushes and pull requests.

## Kalshi collection

The GitHub repo, variable `DATA_BACKUP_BUCKET` and secret `AWS_ROLE_ARN` are not set up yet.

`.github/workflows/kalshi-collect.yml` is intended to run on main every six hours or by manual dispatch. Runs serialize without cancellation and time out after 30 minutes.

Set repository variable `DATA_BACKUP_BUCKET` and secret `AWS_ROLE_ARN` for GitHub OIDC; AWS region is `us-west-2`. Storage prefix: `s3://$DATA_BACKUP_BUCKET/cs2-model/kalshi/`.

Each runner should download only `manifest.json`; a missing manifest should fail unless manual dispatch allows a full pull. Collection skips histories listed in the manifest and uploads new trade/candle files, books, catalogs and manifest. Upload should preserve partial progress; sync never deletes remote objects.

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
