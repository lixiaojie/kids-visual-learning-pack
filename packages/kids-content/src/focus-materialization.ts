import type { Locale, Topic, VisualEvidenceBinding, VisualFocus } from "../../../boards/kids-world/src/types/topic";
import { resolveVisualEvidence } from "./evidence";

export type MaterializeVisualEvidenceFocusOptions = {
  locale?: Locale;
  precision?: number;
};

export type MaterializeVisualEvidenceFocusResult = {
  topic: Topic;
  changed: number;
  missingSources: string[];
};

function hasExplicitFocus(binding: VisualEvidenceBinding): boolean {
  return Boolean(binding.focus?.activeRegionIds?.length || binding.focus?.regions?.length);
}

function roundNumber(value: number, precision: number): number {
  const factor = 10 ** precision;
  return Math.round(value * factor) / factor;
}

function roundedFocus(focus: VisualFocus, precision: number): VisualFocus {
  return {
    ...focus,
    regions: focus.regions?.map((region) => ({
      ...region,
      x: roundNumber(region.x, precision),
      y: roundNumber(region.y, precision),
      width: roundNumber(region.width, precision),
      height: roundNumber(region.height, precision),
    })),
  };
}

function topicWithoutBindingFocus(topic: Topic, bindingId: string): Topic {
  const next = structuredClone(topic);
  const binding = next.visualEvidenceBindings?.find((item) => item.id === bindingId);
  if (binding) delete binding.focus;
  return next;
}

export function materializeVisualEvidenceFocus(
  topic: Topic,
  options: MaterializeVisualEvidenceFocusOptions = {},
): MaterializeVisualEvidenceFocusResult {
  const next = structuredClone(topic);
  const precision = options.precision ?? 4;
  const missingSources: string[] = [];
  let changed = 0;

  for (const binding of next.visualEvidenceBindings ?? []) {
    if (hasExplicitFocus(binding)) continue;

    const sourceTopic = topicWithoutBindingFocus(next, binding.id);
    const evidence = resolveVisualEvidence(sourceTopic, {
      source: binding.source,
      locale: options.locale,
    });
    if (!evidence?.focus) {
      missingSources.push(binding.source);
      continue;
    }

    binding.focus = roundedFocus(evidence.focus, precision);
    changed += 1;
  }

  return {
    topic: next,
    changed,
    missingSources,
  };
}
