# 可展开收缩侧边栏抽屉与工作中绿点状态组件

- **模块根目录**：`mobile/features/sidebar/`
- **唯一对外出口**：`mobile/features/sidebar/index.ts`，导出 `SidebarProvider`、`SidebarDrawer` 与 `useSidebarController`
- **调用的前置模块契约**：
  - `mobile/shared/theme/index.ts`，消费 `bg.sidebar`、`bg.overlay`、`status.working`、`status.accent` 等语义 Token
  - `mobile/shared/ui/index.ts`，使用 `ThemedView`、`ThemedText` 与 `PressableScale`
  - `mobile/features/local_cache/index.ts`，读取 `useLocalBots` 会话列表、最新消息摘要、时间与未读计数
  - `mobile/features/network_sync/index.ts`，订阅 `useBotWorkingStatuses` 忙闲状态流与 `useConnectionStatus` 连接状态
  - `mobile/features/bot_avatar/index.ts`，渲染每行会话的 `BotAvatar`
- **底层设施依赖**：`@shopify/flash-list`、`react-native-reanimated`、`react-native-gesture-handler`、`lucide-react-native`

## Sub-features
- **手势与按钮双控丝滑抽屉**：支持从屏幕左边缘向右滑动跟手拉出侧边栏、点击右侧半透明遮罩或向左滑动收起，同时通过 `useSidebarController` 提供打开、关闭与切换方法供顶部导航栏按钮调用。
- **侧边栏分区布局与图标**：
  - 顶部栏：左侧展示标题「Bots」，右侧放置新建胶囊按钮，使用 `Plus` 加号图标，点击自动收起抽屉并执行新建跳转回调；
  - 中部会话列表：使用 `FlashList` 渲染全部 Bot，每行左侧展示 `BotAvatar`，预置总管名称旁附带小号 `ShieldCheck` 盾牌图标，右侧显示最新消息时间，下方单行展示最新消息摘要，摘要右侧展示蓝底未读数字角标；点击任意会话行立即收起抽屉并执行切换会话回调；
  - 工作中呼吸绿点：实时消费 `useBotWorkingStatuses`，只要某个 Bot 在服务端处于 `working` 状态，无论是正在前台回复用户还是在后台处理委派任务，其头像右下角均展示带呼吸缩放动效的 `status.working` 绿色小圆点，转为 `idle` 后自动熄灭；
  - 底部固定栏：左侧显示连接状态，已连接显示绿色小圆点配文字「在线」，断连或重连中显示 `WifiOff` 图标配文字「离线」；右侧放置设置按钮，使用 `Settings` 齿轮图标，点击收起抽屉并执行跳转系统设置回调。

## How to trigger / reach it
- 编写组件单元测试 `mobile/features/sidebar/__tests__/sidebar.test.tsx`：
  1. 传入两个测试 Bot，其中第一个处于 `working` 状态，第二个处于 `idle` 状态且包含 2 条未读消息，断言仅第一个头像渲染工作绿点节点 `bot-working-dot-bot_1`，第二个准确显示未读角标 `2`；
  2. 分别触发点击会话行、顶部新建按钮 `sidebar-create-bot-btn` 与底部设置按钮 `sidebar-settings-btn`，断言对应导航回调全部准确执行。

## Driving it
- 运行侧边栏与呼吸绿点单测：`npx jest mobile/features/sidebar/__tests__/sidebar.test.tsx`
- 运行全局静态检查：`npm run lint && npx tsc --noEmit`
- 与真实后端 WebSocket 状态流联调的浏览器端到端验证统一在模块 `20` 接入根路由后通过 Playwright CLI 执行，本模块不单独搭建临时测试页。

## Gotchas
- **严禁前端自行推算工作态**：呼吸绿点的亮灭必须完全依据后端经 WebSocket 推送的 `bot_status` 状态流，禁止根据本地发送或收到某条气泡自行开关绿点。
