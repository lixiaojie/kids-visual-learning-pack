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
  const supportingText = items.find((item) => item.id === activeId) ?? items[0];

  return (
    <View className="info-list">
      <Text className="info-list-title">{title}</Text>
      <View className="info-list-track">
        {items.map((item, index) => (
          <View
            className={`info-item ${activeId === item.id ? "active" : ""}`}
            key={item.id}
            onClick={() => onSelect?.(item.id)}
            data-evidence-source={evidencePrefix ? `${evidencePrefix}.${item.id}` : undefined}
          >
            <Text className="info-item-index">{index + 1}</Text>
            <View className="info-item-label">{item.title}</View>
          </View>
        ))}
      </View>
      {supportingText ? (
        <View className="info-support-text">
          <Text className="info-support-title">{supportingText.title}</Text>
          <Text className="info-support-body">{supportingText.body}</Text>
        </View>
      ) : null}
    </View>
  );
}
