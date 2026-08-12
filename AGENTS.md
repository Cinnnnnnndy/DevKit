【确定的实现技术栈】
- TypeScript 5.9
- React 19
- @opentui/core 0.5.1
- @opentui/react 0.5.1
- Bun 构建

设计时需要同时考虑：
1. 产品体验是否成立
2. React + OpenTUI 是否能实现
3. 组件是否适合沉淀为可复用基础组件
4. 宽屏、窄屏、SSH 和低能力终端是否可用

在设计页面前，先区分：
- 应沉淀为全局基础能力的内容
- 应沉淀为通用组件的内容
- 仅属于当前业务页面的内容

推荐的交付文件
UI 每个功能最好不要只交一张 JPG。建议固定输出：
design/<feature>/
├── spec.md                 # 完整设计合同
├── frame-wide-160x50.txt   # 宽屏字符帧
├── frame-narrow-58x32.txt  # 窄屏字符帧
├── states.md               # 状态矩阵
├── interactions.md         # 键盘/鼠标表
├── data-example.json       # 完整示例数据
└── reference.png           # 视觉参考
