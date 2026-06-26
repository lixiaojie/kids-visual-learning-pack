import { useEffect, useState } from "react";
import { Image, View } from "@tarojs/components";
import { getGeneratedImageUrl } from "@yutou/kids-content/media";
import "./GeneratedImage.scss";

type Props = {
  assetId?: string;
  alt?: string;
  className?: string;
  load?: boolean;
  lazyLoad?: boolean;
};

export function GeneratedImage({ assetId, alt, className, load = true, lazyLoad = true }: Props) {
  const src = getGeneratedImageUrl(assetId);
  const [imageLoadFailed, setImageLoadFailed] = useState(false);

  useEffect(() => {
    setImageLoadFailed(false);
  }, [src]);

  if (!load || !src || imageLoadFailed) {
    return <View className={`generated-image-placeholder image-load-failed ${className ?? ""}`}>{alt ?? "图片准备中"}</View>;
  }

  return (
    <Image
      className={`generated-image ${className ?? ""}`}
      src={src}
      mode="widthFix"
      lazyLoad={lazyLoad}
      webp
      onError={() => setImageLoadFailed(true)}
    />
  );
}
