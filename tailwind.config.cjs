/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./boards/paw-patrol/index.html",
    "./boards/paw-patrol/src/**/*.{ts,tsx}",
    "./boards/kids-world/index.html",
    "./boards/kids-world/src/**/*.{ts,tsx}",
    "./apps/miniprogram/src/**/*.{ts,tsx,scss}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
