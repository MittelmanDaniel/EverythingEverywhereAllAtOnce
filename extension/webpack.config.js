const path = require("path");
const CopyPlugin = require("copy-webpack-plugin");

module.exports = {
  devtool: "cheap-source-map",
  entry: {
    popup: "./src/popup/popup.ts",
    "service-worker": "./src/background/service-worker.ts",
  },
  output: {
    path: path.resolve(__dirname, "dist"),
    filename: "[name].js",
    clean: true,
  },
  resolve: {
    extensions: [".ts", ".js"],
  },
  module: {
    rules: [
      { test: /\.ts$/, use: "ts-loader", exclude: /node_modules/ },
      { test: /\.css$/, use: ["style-loader", "css-loader"] },
    ],
  },
  plugins: [
    new CopyPlugin({
      patterns: [
        { from: "manifest.json", to: "manifest.json" },
        { from: "src/popup/popup.html", to: "popup.html" },
        { from: "icons", to: "icons", noErrorOnMissing: true },
      ],
    }),
  ],
};
