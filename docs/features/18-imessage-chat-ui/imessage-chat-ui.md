# 仿 iMessage 高性能聊天流与输入栏组件

- **模块根目录**：`mobile/features/imessage_chat_ui/`
- **唯一对外出口**：`mobile/features/imessage_chat_ui/index.ts`，导出 `ChatScreenView` 与 `ModelSwitcherPill`
- **调用的前置模块契约**：
  - `mobile/shared/theme/index.ts`，消费气泡、画布、分割线与警示色等全部语义 Token
  - `mobile/shared/ui/index.ts`，使用 `ThemedView`、`ThemedText`、`PressableScale` 与 `SheetModal`
  - `mobile/features/local_cache/index.ts`，读取本地历史消息、自动存取输入草稿、清空未读计数
  - `mobile/features/network_sync/index.ts`，立即发送用户消息、多选上传附件、下载缓存附件、热切换当前 Bot 模型
  - `mobile/features/bot_avatar/index.ts`，渲染连续气泡末尾贴底小头像
- **底层设施依赖**：`@shopify/flash-list`、`react-native-reanimated`、`react-native-keyboard-controller`、`lucide-react-native`

## Sub-features
- **顶部模型切换胶囊 `ModelSwitcherPill`**：显示当前 Bot 模型简称及右侧 `ChevronDown` 下拉小箭头图标；点击弹出底部 `SheetModal` 模型列表，当前生效模型右侧显示 `Check` 对勾图标，点选新模型立即调用 `updateBotApi` 切换。
- **仿 iMessage 分组气泡列表**：
  - 采用 `FlashList` 高性能列表：用户气泡靠右展示为蓝底白字 `bubble.self`，Bot 气泡靠左展示为灰底 `bubble.peer`；Bot 连续发出多条短气泡时自动收紧上下间距，仅在连续组最后一条气泡底部显示尾巴与左下角贴底 `BotAvatar`，点击该头像触发查看 Bot 资料回调；
  - 附件与异常态呈现：图片消息根据元数据宽高提前占位，点击图片弹出全屏灯箱预览层，灯箱右上角提供 `X` 关闭图标；文档附件渲染为文件卡片，左侧使用 `FileText` 图标搭配文件名与大小；发送失败的气泡旁显示红色 `AlertCircle` 感叹号图标，点击即可重发；
  - 长按气泡触感菜单：长按任意气泡触发触感震动并弹出操作浮层，提供带 `Copy` 图标的复制文本项与带 `CornerUpLeft` 图标的引用回复项。
- **随时可插话的键盘联动底部输入栏**：
  - 待发预览条：已选待发图片或文档、以及长按选中的引用消息展示在输入框正上方，每个附件缩略项右上角带 `XCircle` 移除图标，引用条右侧带 `X` 取消引用图标；
  - 输入与立即发送区：左侧放置圆形附件按钮，使用 `Plus` 加号图标，点击弹出菜单包含 `Image` 相册多选、`Camera` 拍照、`Paperclip` 选择文件三项；中间为自适应多行输入框并实时同步本地草稿；右侧为圆形发送按钮，使用蓝底白字 `ArrowUp` 向上箭头图标；
  - **禁止因 Bot 工作中锁定发送**：即使当前 Bot 正在后台推理或调用工具处于 `working` 状态，输入框与发送按钮也必须保持完全可用，支持用户随时立即补充或插话发送，仅在无文字且无附件时置灰禁用。

## How to trigger / reach it
- 编写组件单元测试 `mobile/features/imessage_chat_ui/__tests__/imessage_chat_ui.test.tsx`：
  1. 渲染包含用户消息与 Bot 连续 3 条短句回复的消息流，断言仅第 3 条连续 Bot 气泡旁出现贴底头像，且图片气泡按元数据宽高比渲染；
  2. 将当前 Bot 状态设为 `working`，在输入框键入文字并点击发送按钮 `composer-send-btn`，断言按钮未被禁用且立即调用 `sendUserMessage` 发出消息、清空输入框文本。

## Driving it
- 运行聊天流与插话发送单测：`npx jest mobile/features/imessage_chat_ui/__tests__/imessage_chat_ui.test.tsx`
- 运行全局静态检查：`npm run lint && npx tsc --noEmit`
- 与真实后端接口联调的浏览器端到端验证统一在模块 `20` 接入路由页面后通过 Playwright CLI 执行，本模块不单独搭建临时测试页。

## Gotchas
- **严禁使用普通 `FlatList` 与老式键盘避让**：消息列表项必须使用 `React.memo` 封装，键盘弹出与手势下拉收起统一由 `react-native-keyboard-controller` 在 UI 线程驱动。
