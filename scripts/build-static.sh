#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CHANNEL="${VITE_CHANNEL:-${CHANNEL:-web-production}}"
export VITE_CHANNEL="$CHANNEL"

echo "==> validate"
npm run validate

echo "==> clean"
rm -rf dist
mkdir -p dist/boards

echo "==> build kids-world"
npx vite build boards/kids-world --base=./ --emptyOutDir --outDir ../../dist/boards/kids-world

if [ "$CHANNEL" != "web-production" ]; then
  echo "==> build paw-patrol"
  npx vite build boards/paw-patrol --base=./ --emptyOutDir --outDir ../../dist/boards/paw-patrol
fi

echo "==> copy root + shared"
cp index.html dist/
cp -r shared dist/

if [ "$CHANNEL" != "web-production" ]; then
  echo "==> copy spider-verse"
  cp -r boards/spider-verse dist/boards/
  find dist/boards/spider-verse \( -name '*.test.*' -o -name '*.spec.*' -o -name '.DS_Store' \) -delete
fi

if [ -d legal ]; then
  cp -r legal dist/
fi

if [ -d public-verification ]; then
  cp public-verification/MP_verify_*.txt dist/ 2>/dev/null || true
fi

echo "==> clean PNG"
find dist/boards -path '*/assets/*.png' -delete

echo "==> generate site meta"
npm run generate:site-meta

echo "==> check-dist"
npm run check:dist
