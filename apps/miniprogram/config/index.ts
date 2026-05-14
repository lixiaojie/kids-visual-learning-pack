import { defineConfig } from "@tarojs/cli";
import path from "node:path";

const root = path.resolve(__dirname, "../../..");
const kidsContentSource = path.join(root, "packages/kids-content/src");

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
    "@yutou/kids-content": path.join(root, "packages/kids-content/src/index.ts"),
  },
  mini: {
    webpackChain(chain) {
      chain.module
        .rule("kids-content-ts")
        .test(/\.(ts|tsx)$/)
        .include.add(kidsContentSource)
        .end()
        .use("babel-loader")
        .loader("babel-loader")
        .options({
          presets: [
            [
              "taro",
              {
                framework: "react",
                ts: true,
              },
            ],
          ],
        });
    },
    postcss: {
      pxtransform: {
        enable: true,
        config: {},
      },
    },
  },
});
