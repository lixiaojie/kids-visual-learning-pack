import {
  Anchor,
  Award,
  BadgeHelp,
  Building2,
  CheckCircle2,
  Construction,
  Eye,
  Flame,
  HeartHandshake,
  MapPinned,
  Megaphone,
  Mountain,
  PawPrint,
  Recycle,
  Rocket,
  ShieldCheck,
  Sparkles,
  Star,
  TrafficCone,
  Trees,
  Trophy,
  Users,
  Waves,
  Wheat,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const icons: Record<string, LucideIcon> = {
  Anchor,
  Award,
  BadgeHelp,
  Building2,
  CheckCircle2,
  Construction,
  Eye,
  Flame,
  HeartHandshake,
  MapPinned,
  Megaphone,
  Mountain,
  PawPrint,
  Recycle,
  Rocket,
  ShieldCheck,
  Sparkles,
  Star,
  TrafficCone,
  Trees,
  Trophy,
  Users,
  Waves,
  Wheat,
  MessageCircleQuestion: BadgeHelp,
  TowerControl: Building2,
};

type IconForProps = {
  name: string;
  className?: string;
  size?: number;
};

export function IconFor({ name, className, size = 24 }: IconForProps) {
  const Icon = icons[name] ?? Sparkles;
  return <Icon aria-hidden="true" className={className} size={size} strokeWidth={2.4} />;
}
