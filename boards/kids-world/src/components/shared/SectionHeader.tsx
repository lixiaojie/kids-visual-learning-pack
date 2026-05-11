import type { ReactNode } from "react";

export function SectionHeader({ kicker, title, children }: { kicker?: string; title: string; children?: ReactNode }) {
  return (
    <div className="section-head">
      {kicker && <p className="kicker">{kicker}</p>}
      <h2>{title}</h2>
      {children && <p>{children}</p>}
    </div>
  );
}
