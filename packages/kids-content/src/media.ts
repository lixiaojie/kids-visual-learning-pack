import { generatedAssets } from "./assets";

const defaultCdnBase = "https://kids.yutou-verse.cn/boards/kids-world";

function normalizeBase(base: string) {
  return base.replace(/\/+$/, "");
}

export function getCdnAssetUrl(assetPath: string | undefined, cdnBase = defaultCdnBase): string | undefined {
  if (!assetPath) return undefined;
  const normalizedPath = assetPath.startsWith("/") ? assetPath : `/${assetPath}`;
  return `${normalizeBase(cdnBase)}${normalizedPath}`;
}

export function getGeneratedImageUrl(assetId: string | undefined, cdnBase = defaultCdnBase): string | undefined {
  if (!assetId) return undefined;
  const asset = generatedAssets[assetId];
  return getCdnAssetUrl(asset?.webpPath, cdnBase);
}
