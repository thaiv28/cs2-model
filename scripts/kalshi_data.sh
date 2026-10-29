#!/usr/bin/env bash
set -euo pipefail

: "${DATA_BACKUP_BUCKET:?Set DATA_BACKUP_BUCKET to the shared artifacts bucket}"

case "${1:-}" in
  pull)
    aws s3 sync "s3://$DATA_BACKUP_BUCKET/cs2-model/kalshi" data/kalshi
    ;;
  push)
    aws s3 sync data/kalshi "s3://$DATA_BACKUP_BUCKET/cs2-model/kalshi"
    ;;
  *)
    echo "Usage: scripts/kalshi_data.sh pull|push" >&2
    exit 1
    ;;
esac
