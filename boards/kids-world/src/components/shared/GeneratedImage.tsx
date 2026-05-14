import { useEffect, useState } from "react";
import { getGeneratedImageUrl } from "@yutou/kids-content";
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
  const generatedPath = getGeneratedImageUrl(assetId, "");
  const sources = [generatedPath, fallbackPath]
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
