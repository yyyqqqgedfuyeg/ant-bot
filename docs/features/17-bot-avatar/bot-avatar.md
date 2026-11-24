# Bot 轻量 SVG 头像与可视化定制面板组件

- **模块根目录**：`mobile/features/bot_avatar/`
- **唯一对外出口**：`mobile/features/bot_avatar/index.ts`，导出 `BotAvatar`、`AvatarStudioEditor`、`generateRandomAvatarConfig`、`DEFAULT_SUPERVISOR_AVATAR` 与 `AvatarConfig` 类型
- **调用的前置模块契约**：
  - `mobile/shared/theme/index.ts`，面板背景、分类选中高亮与边框统一消费深浅色 Token
  - `mobile/shared/ui/index.ts`，使用 `ThemedView`、`ThemedText` 与 `PressableScale`
- **底层设施依赖**：`react-native-svg`、`lucide-react-native`

## Sub-features
- **全场景原生 SVG 头像组件 `BotAvatar`**：接收 `avatar_config_json` 与尺寸参数，基于 `react-native-svg` 纯原生绘制背景色或渐变、机器人轮廓、眼睛表情与头顶配饰，供侧边栏列表、聊天顶部栏、气泡贴底小头像及资料页大图复用。
- **可视化分类定制面板 `AvatarStudioEditor`**：
  - 上半区：居中渲染大尺寸实时预览头像，右上角放置圆形随机生成按钮，使用 `Dice5` 摇骰子图标，点击触发轻触感反馈并调用 `generateRandomAvatarConfig` 刷新当前预览；
  - 下半区：顶部提供 4 个横向分类切换标签页，分别为背景标签使用 `Palette` 图标、主体轮廓标签使用 `Shapes` 图标、眼睛表情标签使用 `Smile` 图标、配饰标签使用 `Sparkles` 图标；下方对应网格点选卡片，当前选中项展示 `status.accent` 主题色高亮边框。

## How to trigger / reach it
- 编写组件单元测试 `mobile/features/bot_avatar/__tests__/bot_avatar.test.tsx`：
  1. 校验 `generateRandomAvatarConfig` 与 `DEFAULT_SUPERVISOR_AVATAR` 产出合法配置结构，传入 `BotAvatar` 正常渲染 SVG 节点无异常；
  2. 渲染 `AvatarStudioEditor`，依次触发右上角随机按钮 `avatar-randomize-btn` 与 4 个分类下的选项点击，断言 `onChange` 准确传出更新后的头像配置。

## Driving it
- 运行头像渲染与定制面板单测：`npx jest mobile/features/bot_avatar/__tests__/bot_avatar.test.tsx`
- 运行全局静态检查：`npm run lint && npx tsc --noEmit`

## Gotchas
- **严禁内嵌 WebView 渲染头像**：会话列表与消息流同时存在大量头像节点，必须纯原生 `react-native-svg` 实现并配合 `React.memo` 缓存渲染。
