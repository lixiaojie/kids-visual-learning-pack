#!/usr/bin/env bash
# Build script for Vercel (or any static host).
#
# Produces a self-contained dist/ directory that mirrors the URL layout:
#   dist/
#   ├── index.html            ← 项目根入口
#   ├── shared/               ← 共享样式
#   └── boards/
#       ├── kids-world/       ← 最高层探索地图
#       ├── spider-verse/     ← 纯静态（排除 test/spec）
#       └── paw-patrol/       ← vite build 产物

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> checking local PNG/WebP asset pairs"
node scripts/check-image-assets.mjs

echo "==> cleaning dist/"
rm -rf dist
mkdir -p dist/boards

echo "==> building paw-patrol via vite"
npx vite build boards/paw-patrol --base=./ --emptyOutDir --outDir ../../dist/boards/paw-patrol

echo "==> building kids-world via vite"
npx vite build boards/kids-world --base=./ --emptyOutDir --outDir ../../dist/boards/kids-world

echo "==> copying root entry (index.html)"
cp index.html dist/

echo "==> copying shared/"
cp -r shared dist/

echo "==> copying spider-verse (excluding test/spec)"
cp -r boards/spider-verse dist/boards/
find dist/boards/spider-verse \
  \( -name '*.test.*' -o -name '*.spec.*' -o -name '.DS_Store' \) \
  -delete

echo "==> removing source PNG assets from deployment (deploy WebP versions)"
find dist/boards -path '*/assets/*.png' -delete

echo "==> build done. dist/ layout:"
find dist -maxdepth 3 -type d | sort
