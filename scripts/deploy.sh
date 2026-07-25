#!/usr/bin/env bash
# Deploy kids-visual-learning-pack to production server.
#
# What it does:
#   1. Builds kids-world and paw-patrol via Vite.
#   2. Rsyncs five parts to /var/www/kids-visual-learning-pack/.
#   3. Explicitly excludes test/spec/system files from the upload.
#
# nginx alias and URL routing (/kids/, /kids/boards/...) are managed
# separately on the server and NOT touched by this script.

set -euo pipefail

HOST="${DEPLOY_HOST:-root@118.145.242.99}"
DEST="${DEPLOY_DEST:-/var/www/kids-visual-learning-pack}"

EXCLUDE=(
  --exclude='.DS_Store'
  --exclude='Thumbs.db'
  --exclude='*.test.*'
  --exclude='*.spec.*'
  --exclude='node_modules'
  --exclude='dist'
  --exclude='.git'
  --exclude='tmp'
)

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> building kids-world"
npm run build:kids-world

echo "==> building paw-patrol"
npm run build:paw

echo "==> uploading root entry"
rsync -av "${EXCLUDE[@]}" index.html "$HOST:$DEST/"

echo "==> uploading shared/ and docs/"
rsync -av --delete "${EXCLUDE[@]}" shared docs "$HOST:$DEST/"

echo "==> uploading kids-world (built dist)"
rsync -av --delete dist/kids-world/ "$HOST:$DEST/boards/kids-world/"

echo "==> uploading spider-verse (static)"
rsync -av --delete "${EXCLUDE[@]}" boards/spider-verse/ "$HOST:$DEST/boards/spider-verse/"

echo "==> uploading paw-patrol (built dist)"
rsync -av --delete dist/paw-patrol/ "$HOST:$DEST/boards/paw-patrol/"

echo
echo "✓ deployed"
echo "  https://118.145.242.99/kids/"
echo "  https://118.145.242.99/kids/boards/kids-world/"
echo "  https://118.145.242.99/kids/boards/spider-verse/"
echo "  https://118.145.242.99/kids/boards/paw-patrol/"
