import { defineConfig } from "@tarojs/cli";

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
  mini: {
    postcss: {
      pxtransform: {
        enable: true,
        config: {},
      },
    },
  },
});
