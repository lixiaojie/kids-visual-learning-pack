import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  base: "./",
  resolve: {
    alias: [
      {
        find: /^@yutou\/kids-content$/,
        replacement: path.resolve(rootDir, "packages/kids-content/src/index.ts"),
      },
      {
        find: /^@yutou\/kids-content\/(.*)$/,
        replacement: path.resolve(rootDir, "packages/kids-content/src/$1"),
      },
    ],
  },
});
