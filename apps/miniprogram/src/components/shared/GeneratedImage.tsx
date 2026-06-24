import { Image, View } from "@tarojs/components";
import { getGeneratedImageUrl } from "@yutou/kids-content/media";
import "./GeneratedImage.scss";

type Props = {
  assetId?: string;
  alt?: string;
  className?: string;
};

export function GeneratedImage({ assetId, alt, className }: Props) {
  const src = getGeneratedImageUrl(assetId);

  if (!src) {
    return <View className={`generated-image-placeholder ${className ?? ""}`}>{alt ?? "图片准备中"}</View>;
  }

  return <Image className={`generated-image ${className ?? ""}`} src={src} mode="widthFix" />;
}
