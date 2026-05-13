import { Text, View } from "@tarojs/components";
import "./InfoList.scss";

type Item = {
  id: string;
  title: string;
  body: string;
};

export function InfoList({ title, items }: { title: string; items: Item[] }) {
  if (items.length === 0) return null;

  return (
    <View className="info-list">
      <Text className="info-list-title">{title}</Text>
      {items.map((item) => (
        <View className="info-item" key={item.id}>
          <Text className="info-item-title">{item.title}</Text>
          <Text className="info-item-body">{item.body}</Text>
        </View>
      ))}
    </View>
  );
}
