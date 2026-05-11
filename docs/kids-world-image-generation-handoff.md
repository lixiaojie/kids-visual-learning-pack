# 芋头世界图片生成交接说明

本轮不在 Codex 内继续消耗额度生成全量图片。项目已经准备好批量生图清单、导入脚本和前端容错逻辑：图片文件未落地时继续显示 CSS 占位图；PNG 或 WebP 文件按清单放入后会自动显示。

## 1. 已生成的交接文件

- `boards/kids-world/src/data/image-generation-manifest.json`
  - 43 个 V2.1 资产的完整 manifest。
  - 每个资产包含 `assetId`、`filename`、`pngPath`、`webpPath`、最终源码路径、部署路径、推荐尺寸和完整 prompt。
- `tmp/imagegen/kids-world-v2.1-prompts.jsonl`
  - 可直接用于批量生图工具的 JSONL。
  - 输出文件名使用 manifest 中的 PNG 文件名。
- `scripts/import-kids-world-generated-images.mjs`
  - 将批量工具输出的扁平 PNG 目录复制到 `boards/kids-world/public/assets/**` 的最终目录。

## 2. 生成 PNG

如果使用 Codex imagegen CLI，可参考：

```bash
python3 ~/.codex/skills/.system/imagegen/scripts/image_gen.py generate-batch \
  --input tmp/imagegen/kids-world-v2.1-prompts.jsonl \
  --out-dir output/imagegen/kids-world-v2.1-png \
  --concurrency 3 \
  --quality medium \
  --output-format png
```

如果使用其他批量生图工具，也只需要保证输出 PNG 文件名与 JSONL/manifest 的 `filename` 一致。

## 3. 导入 PNG

```bash
npm run images:import-generated-png -- output/imagegen/kids-world-v2.1-png
```

导入后文件会落到：

```text
boards/kids-world/public/assets/<world-or-shared-folder>/<asset-name>.png
```

此时本地开发页面会优先尝试 WebP，找不到时回退到 PNG，因此可以先看到生成图，不必马上压缩。

## 4. 压缩 WebP

另一个模型或本地脚本需要为每个 PNG 生成同名 WebP：

```text
boards/kids-world/public/assets/.../example-v02.png
boards/kids-world/public/assets/.../example-v02.webp
```

建议初期部署控制 WebP 体积，保留 PNG 原图用于回溯和二次处理。

## 5. 验收

WebP 补齐后运行：

```bash
npm run check:images
npm run build
```

`npm run build` 会先检查 PNG/WebP 配对，再从部署产物 `dist/boards/**/assets/` 中删除 PNG，只保留 WebP，适合 Vercel 免费服务的初期部署。
