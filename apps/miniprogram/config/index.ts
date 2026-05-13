import { defineConfig } from "@tarojs/cli";
import path from "node:path";

const root = path.resolve(__dirname, "../../..");

export default defineConfig({
  projectName: "yutou-verse",
  date: "2026-05-13",
  designWidth: 375,
  deviceRatio: {
    375: 2,
    640: 1.17,
    750: 1,
    828: 0.905,
  },
  sourceRoot: "src",
  outputRoot: "dist",
  framework: "react",
  compiler: "webpack5",
  alias: {
    "@yutou/kids-content": path.join(root, "apps/miniprogram/src/lib/kids-content.ts"),
  },
  mini: {
    postcss: {
      pxtransform: {
        enable: true,
        config: {},
      },
    },
  },
});
