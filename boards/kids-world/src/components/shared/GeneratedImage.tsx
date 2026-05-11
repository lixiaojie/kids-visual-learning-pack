import { useEffect, useState } from "react";
import { generatedAssets } from "../../lib/asset-map";
import { resolveBoardAssetCandidates } from "../../lib/asset-resolve";

export function GeneratedImage({
  assetId,
  fallbackPath,
  className,
  alt,
}: {
  assetId?: string;
  fallbackPath?: string;
  className: string;
  alt: string;
}) {
  const asset = assetId ? generatedAssets[assetId] : undefined;
  const sources = [asset?.webpPath, asset?.pngPath, fallbackPath]
    .flatMap((path) => resolveBoardAssetCandidates(path))
    .filter(Boolean);
  const [sourceIndex, setSourceIndex] = useState(0);

  useEffect(() => {
    setSourceIndex(0);
  }, [assetId, fallbackPath]);

  const source = sources[sourceIndex];

  if (!source) {
    return null;
  }

  return (
    <img
      alt={alt}
      className={className}
      src={source}
      onError={() => {
        setSourceIndex((current) => (current + 1 < sources.length ? current + 1 : sources.length));
      }}
    />
  );
}
