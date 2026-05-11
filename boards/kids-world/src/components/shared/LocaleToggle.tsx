import { Languages } from "lucide-react";
import type { Locale } from "../../types/topic";

export function LocaleToggle({ locale, onChange }: { locale: Locale; onChange: (locale: Locale) => void }) {
  return (
    <div className="locale-toggle" aria-label="Language switch">
      <Languages size={18} />
      <button className={locale === "zh-CN" ? "active" : ""} type="button" onClick={() => onChange("zh-CN")}>
        中文
      </button>
      <button className={locale === "en-US" ? "active" : ""} type="button" onClick={() => onChange("en-US")}>
        English
      </button>
    </div>
  );
}
