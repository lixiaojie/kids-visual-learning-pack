import { Text, View } from "@tarojs/components";
import "./index.scss";

const points = [
  "小程序首版不登录，不收集儿童姓名、头像、位置或通讯录。",
  "学习内容来自芋头宇宙原创知识 topic，首版不展示第三方 IP 衍生看板。",
  "图片通过 EdgeOne CDN 加载，学习进度如后续保存，只保存在本地设备。",
  "这里适合孩子和家长共读：看图、观察、讲出来。",
];

export default function AboutPage() {
  return (
    <View className="about-page">
      <Text className="about-title">家长说明与隐私政策</Text>
      {points.map((point) => (
        <Text className="about-point" key={point}>
          {point}
        </Text>
      ))}
      <Text className="about-footer">如后续加入云同步、账号或统计能力，会先更新隐私说明并重新评估提审风险。</Text>
    </View>
  );
}
