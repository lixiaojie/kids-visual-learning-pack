import type { TopicInteractionGraph } from "./interaction-graph";
import { hasVisualFocusDifference } from "./focus";

export type InteractionGraphIssue = {
  severity: "error" | "warning";
  path: string;
  message: string;
};

export type InteractionGraphValidationReport = {
  slug: string;
  errors: InteractionGraphIssue[];
  warnings: InteractionGraphIssue[];
  pass: boolean;
};

function issue(severity: "error" | "warning", path: string, message: string): InteractionGraphIssue {
  return { severity, path, message };
}

export function validateInteractionGraph(graph: TopicInteractionGraph): InteractionGraphValidationReport {
  const issues: InteractionGraphIssue[] = [];

  for (const stage of graph.stages) {
    const stagePath = `${graph.slug}.${stage.id}`;
    if (!stage.subflows.length) {
      issues.push(issue("warning", stagePath, "stage has no subflow containers"));
      continue;
    }

    if (!stage.defaultSubflowId) {
      issues.push(issue("error", stagePath, "stage is missing defaultSubflowId"));
    }

    for (const subflow of stage.subflows) {
      const subflowPath = `${stagePath}.${subflow.id}`;
      if (subflow.visualPolicy !== "text-only" && !subflow.visual) {
        issues.push(issue("warning", subflowPath, "subflow has no visual binding"));
      }

      const seen = new Map<string, string>();
      for (const node of subflow.nodes) {
        const nodePath = `${subflowPath}.${node.id}`;
        if (!node.visual) {
          issues.push(issue("warning", nodePath, "clickable secondary node has no visual binding"));
          continue;
        }
        if (node.visual.focusMode === "none" || node.visual.activeRegionIds.length === 0) {
          issues.push(issue("warning", nodePath, "clickable secondary node has no active visual focus"));
        }

        const visualKey = `${node.visual.visualSlotId}:${node.visual.assetId}`;
        const previousNodeId = seen.get(visualKey);
        if (previousNodeId) {
          const previous = subflow.nodes.find((candidate) => candidate.id === previousNodeId);
          if (previous?.visual && !hasVisualFocusDifference(previous.visual, node.visual)) {
            issues.push(issue("warning", nodePath, `visual repeats ${previousNodeId} without focus difference`));
          }
        }
        seen.set(visualKey, node.id);
      }
    }
  }

  const errors = issues.filter((item) => item.severity === "error");
  const warnings = issues.filter((item) => item.severity === "warning");
  return {
    slug: graph.slug,
    errors,
    warnings,
    pass: errors.length === 0,
  };
}
