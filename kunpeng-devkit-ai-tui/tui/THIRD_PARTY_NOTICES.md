# 第三方声明

Kunpeng DevKit AI TUI 包含以下运行时软件。应用本身仍为专有软件；以下声明不会改变应用的许可证。

| 组件 | 版本 | 许可证 | 来源 |
|---|---:|---|---|
| Bun runtime | 1.3.14 | MIT | https://github.com/oven-sh/bun |
| OpenTUI Core and native platform core | 0.5.1 | MIT and bundled upstream notices | https://github.com/anomalyco/opentui |
| OpenTUI React | 0.5.1 | MIT | https://github.com/anomalyco/opentui |
| React and React Reconciler | 19.2.0 / 0.33.0 | MIT | https://github.com/facebook/react |
| React DevTools Core | 7.0.1 | MIT | https://github.com/facebook/react |
| web-tree-sitter | 0.25.10 | MIT | https://github.com/tree-sitter/tree-sitter |
| ws | 8.18.3 | MIT | https://github.com/websockets/ws |
| marked | 17.0.1 | MIT | https://github.com/markedjs/marked |
| diff | 9.0.0 | BSD-3-Clause | https://github.com/kpdecker/jsdiff |
| string-width / strip-ansi | 7.2.0 / 7.1.2 | MIT | https://github.com/sindresorhus |

每个发布归档都包含 `licenses/index.json`，以及从已安装生产依赖中收集的完整许可证、声明和专利
文件。其中包括版本锁定的 Bun 运行时声明，以及 OpenTUI 原生 LCMS2、libwebp、stb、Wuffs 和
libwebp 专利文件。该索引会在打包过程中生成并校验；本摘要不能替代这些原始文本。
