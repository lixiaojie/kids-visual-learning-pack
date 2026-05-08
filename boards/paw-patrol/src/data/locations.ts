import type { Location } from "../types";

export const locations: Location[] = [
  {
    id: "lookout",
    name: "任务总部",
    description: "接收任务、集合出动的地方。",
    commonProblems: ["收到求助", "分析问题", "分配队员"],
    recommendedCharacterIds: ["ryder"],
    icon: "TowerControl",
  },
  {
    id: "town-road",
    name: "城镇路口",
    description: "车辆和行人都很多，需要规则。",
    commonProblems: ["交通混乱", "车辆故障"],
    recommendedCharacterIds: ["chase", "rocky"],
    icon: "TrafficCone",
  },
  {
    id: "town-park",
    name: "城镇公园",
    description: "树木、长椅和小动物很多。",
    commonProblems: ["小动物走丢", "高处救援"],
    recommendedCharacterIds: ["marshall", "skye"],
    icon: "Trees",
  },
  {
    id: "harbor",
    name: "海边港口",
    description: "水面任务要注意安全。",
    commonProblems: ["落水", "小船故障"],
    recommendedCharacterIds: ["zuma", "rocky"],
    icon: "Anchor",
  },
  {
    id: "mountain-road",
    name: "山区道路",
    description: "石头和斜坡会挡住路。",
    commonProblems: ["道路堵塞", "滑落被困"],
    recommendedCharacterIds: ["rubble", "skye"],
    icon: "Mountain",
  },
  {
    id: "farm",
    name: "森林农场",
    description: "动物和机器都需要照看。",
    commonProblems: ["机器坏了", "围栏坏了"],
    recommendedCharacterIds: ["rocky", "rubble", "chase"],
    icon: "Wheat",
  },
];
