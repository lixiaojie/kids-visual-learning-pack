import { Text, View } from "@tarojs/components";
import "./InfoList.scss";

type Item = {
  id: string;
  title: string;
  body: string;
};

export function InfoList({
  title,
  items,
  activeId,
  evidencePrefix,
  onSelect,
}: {
  title: string;
  items: Item[];
  activeId?: string;
  evidencePrefix?: string;
  onSelect?: (id: string) => void;
}) {
  if (items.length === 0) return null;

  return (
    <View className="info-list">
      <Text className="info-list-title">{title}</Text>
      {items.map((item) => (
        <View
          className={`info-item ${activeId === item.id ? "active" : ""}`}
          key={item.id}
          onClick={() => onSelect?.(item.id)}
          data-evidence-source={evidencePrefix ? `${evidencePrefix}.${item.id}` : undefined}
        >
          <Text className="info-item-title">{item.title}</Text>
          <Text className="info-item-body">{item.body}</Text>
        </View>
      ))}
    </View>
  );
}
