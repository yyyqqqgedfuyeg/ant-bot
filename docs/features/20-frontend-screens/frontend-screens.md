# 移动端全量 6 大界面开发、图标规范与路由跳转组装

- **模块根目录**：`mobile/app/`
- **唯一对外出口**：Expo Router 全量路由页面，包含 `app/_layout.tsx`、`app/index.tsx`、`app/chat/[botId].tsx`、`app/bot/create.tsx`、`app/bot/[botId]/profile.tsx`、`app/bot/avatar-studio.tsx` 与 `app/settings.tsx`
- **调用的前置模块契约**：
  - `mobile/shared/theme/index.ts`
  - `mobile/shared/ui/index.ts`
  - `mobile/features/local_cache/index.ts`
  - `mobile/features/network_sync/index.ts`
  - `mobile/features/device_sync/index.ts`
  - `mobile/features/bot_avatar/index.ts`
  - `mobile/features/imessage_chat_ui/index.ts`
  - `mobile/features/sidebar/index.ts`
- **底层设施依赖**：`expo-router`、`lucide-react-native`

---

## Sub-features：6 大核心界面布局、图标与点击跳转规范

所有图标统一从 `lucide-react-native` 引入，所有颜色统一消费 `mobile/shared/theme` 语义 Token。

| 界面编号 | 界面名称 | 路由路径 | 页面形态 |
| :--- | :--- | :--- | :--- |
| **界面 1** | 主聊天界面 | `app/index.tsx` 与 `app/chat/[botId].tsx` | 应用主画布 |
| **界面 2** | 全局侧边栏抽屉壳 | `app/_layout.tsx` | 根布局手势抽屉 |
| **界面 3** | 新建 Bot 弹窗页 | `app/bot/create.tsx` | 底部卡片弹窗 Modal |
| **界面 4** | Bot 资料与编辑页 | `app/bot/[botId]/profile.tsx` | 二级详情页面 |
| **界面 5** | 头像工坊弹窗页 | `app/bot/avatar-studio.tsx` | 弹窗页面 Modal |
| **界面 6** | 系统设置页 | `app/settings.tsx` | 二级设置页面 |

---

### 界面 1：主聊天界面 `app/index.tsx` 与 `app/chat/[botId].tsx`
- **界面包含元素与图标**：
  - 顶部毛玻璃导航栏 `GlassHeader`：
    - 左侧放置展开侧边栏按钮，使用 `PanelLeft` 图标；若其他 Bot 存在未读消息则在图标右上角展示小红点；
    - 中间上方并排展示当前 Bot 小头像 `BotAvatar`、Bot 名称以及 `ChevronRight` 向右微箭头图标；中间下方挂载模型热切胶囊 `ModelSwitcherPill`，内部带 `ChevronDown` 图标；
    - 右侧仅在网络断连或重连期间展示状态提示，离线使用 `WifiOff` 图标，重连中使用 `RefreshCw` 图标，正常连接时留空。
  - 中部消息流与底部输入栏：直接挂载模块 `18` 的 `ChatScreenView`，包含连续分组气泡、全屏图片预览 `X` 关闭按钮、长按 `Copy` 复制与 `CornerUpLeft` 引用菜单、附件 `Plus` 选择菜单与蓝底 `ArrowUp` 立即发送按钮。
- **点击跳转关系**：
  - `app/index.tsx` 冷启动时读取本地 `getLastActiveBotId` 默认定位到 `'supervisor'`，直接进入对应 `/chat/[botId]` 并清空该会话未读计数；
  - 点击左上角 `PanelLeft` 按钮或从屏幕左边缘右滑 → 展开 **界面 2 侧边栏抽屉**；
  - 点击顶部中间「头像与 Bot 名称」区域，或点击消息流中 Bot 气泡贴底头像 → 跳转 **`/bot/[botId]/profile` 界面 4 Bot 资料与编辑页**。

---

### 界面 2：全局侧边栏抽屉壳 `app/_layout.tsx`
- **根层全局初始化**：在根布局外层依次包裹 `ThemeProvider`、`NetworkSyncProvider` 与 `SidebarProvider`；启动时执行 `initLocalCache` 与 `syncBotsFromServer`；挂载 `usePresenceMonitor` 自动执行前后台上报、心跳保活与切回前台断线自动重连；挂载 `usePushNotifications` 监听用户点击系统推送通知后直接导航至对应 `/chat/[botId]`。
- **点击跳转关系**：
  - 点击侧边栏顶部右侧带 `Plus` 图标的新建按钮 → 收起抽屉并打开 **`/bot/create` 界面 3 新建 Bot 弹窗页**；
  - 点击中部列表任意 Bot 会话行 → 收起抽屉、更新 `setLastActiveBotId` 并切换至 **`/chat/[botId]` 界面 1 主聊天界面**；
  - 点击底部右侧带 `Settings` 齿轮图标的设置按钮 → 收起抽屉并跳转 **`/settings` 界面 6 系统设置页**。

---

### 界面 3：新建 Bot 弹窗页 `app/bot/create.tsx`
- **界面包含元素与图标**：
  - 顶部栏：左侧放置关闭按钮使用 `X` 图标，中间显示标题「新建 Bot」。
  - 头像设定区：居中展示大尺寸 `BotAvatar`，头像右下角叠加编辑小圆标使用 `Pencil` 图标，头像旁提供快捷随机按钮使用 `Dice5` 图标。
  - 表单填写区：
    - 「Bot 名称」单行输入框，必填；
    - 「用来做什么」多行输入框，必填，用户输入的内容将在创建后直接传入后端作为该新建 Bot 的专属角色系统提示词；
    - 「默认模型」选择行，左侧使用 `Cpu` 图标，右侧显示当前选中模型名称与 `ChevronRight` 图标，默认继承全局默认模型。
  - 底部操作区：全宽主按钮「创建并开始聊天」，左侧使用 `MessageSquarePlus` 图标，名称或用途未填时置灰禁用。
- **点击跳转关系**：
  - 点击左上角 `X` 图标 → 关闭弹窗返回原页面；
  - 点击大头像或 `Pencil` 图标 → 打开 **`/bot/avatar-studio` 界面 5 头像工坊弹窗页**，完成后回填新头像配置；
  - 点击底部「创建并开始聊天」→ 调用 `createBotApi` 创建成功后立即关闭弹窗并跳转 **`/chat/[newBotId]` 界面 1 主聊天界面**，用户在聊天页内直接接收新 Bot 自动调用 1 到 3 次 `send_to_user` 发来的自然开场问候与需求追问。

---

### 界面 4：Bot 资料与编辑页 `app/bot/[botId]/profile.tsx`
- **界面包含元素与图标**：
  - 顶部毛玻璃导航栏：左侧返回按钮使用 `ChevronLeft` 图标，中间标题「Bot 资料」，右侧保存按钮使用 `Check` 图标并在表单发生修改后高亮。
  - 头像展示区：居中展示大号 `BotAvatar`，下方放置「更换头像」胶囊按钮，使用 `Palette` 图标。
  - 资料编辑卡片：提供可编辑的「Bot 名称」输入框、「用来做什么」用途多行输入框、以及带 `Cpu` 与 `ChevronRight` 图标的「默认模型」选择行。
  - 待触发定时任务卡片：卡片标题左侧使用 `CalendarClock` 图标，调用 `fetchBotEventsApi` 只读展示该 Bot 名下所有待触发的单次与周期提醒及其下次执行时间；列表为空时展示「暂无待触发提醒」提示。
  - 底部危险操作区：
    - 当 `is_preset` 为 `0` 即用户自定义 Bot 时，展示红色「删除此 Bot」按钮，左侧使用 `Trash2` 垃圾桶图标；
    - 当 `is_preset` 为 `1` 即系统预置总管时，不展示删除按钮，仅展示带 `ShieldCheck` 图标的灰字提示「系统预置总管不可删除」。
- **点击跳转关系**：
  - 点击左上角 `ChevronLeft` 图标 → 返回 **界面 1 主聊天界面**；
  - 点击「更换头像」按钮 → 打开 **`/bot/avatar-studio` 界面 5 头像工坊弹窗页**，保存后刷新当前页头像预览；
  - 点击右上角 `Check` 图标 → 调用 `updateBotApi` 保存修改并返回；
  - 点击「删除此 Bot」并经二次确认弹窗确认 → 调用 `deleteBotApi` 删除服务端与本地数据，自动跳转回 `/chat/supervisor`。

---

### 界面 5：头像工坊弹窗页 `app/bot/avatar-studio.tsx`
- **界面包含元素与图标**：
  - 顶部导航栏：左侧取消按钮使用 `X` 图标，中间标题「定制头像」，右侧完成按钮使用 `Check` 图标。
  - 主体定制区：直接挂载模块 `17` 的 `AvatarStudioEditor`，包含右上角 `Dice5` 随机摇骰子按钮，以及 `Palette` 背景、`Shapes` 主体、`Smile` 表情、`Sparkles` 配饰四个分类面板。
- **点击跳转关系**：
  - 点击左上角 `X` 图标 → 丢弃本次修改并返回界面 3 或界面 4；
  - 点击右上角 `Check` 图标 → 将最新定制的 `AvatarConfig` 回传给来源页面并关闭当前弹窗。

---

### 界面 6：系统设置页 `app/settings.tsx`
- **界面包含元素与图标**：
  - 顶部毛玻璃导航栏：左侧返回按钮使用 `ChevronLeft` 图标，中间标题「系统设置」。
  - 分组卡片一 外观与全局模型：
    - 外观模式三段选择器：包含带 `Monitor` 图标的「跟随系统」、带 `Sun` 图标的「浅色」、带 `Moon` 图标的「深色」，点击调用 `useTheme` 即时零闪烁切换；
    - 全局默认模型选择行：左侧使用 `Cpu` 图标，右侧显示当前全局模型名称与 `ChevronRight` 图标，修改后调用 `updateUserSettingsApi` 保存。
  - 分组卡片二 休息时间免打扰：
    - 免打扰总开关行：左侧使用 `MoonStar` 图标配标题「休息时间免打扰」，右侧为开关控件；下方附简短说明「开启后，休息时段内的消息通知将静音积压，待休息结束后统一推送」；
    - 休息起止时间设置行：开启免打扰后展示「开始时间」与「结束时间」两行时间选择器，左侧使用 `Clock` 图标，默认值为 `23:00` 至 `08:00`，修改开关或时间后立即调用 `updateUserSettingsApi` 同步至后端。
  - 分组卡片三 服务器连接：
    - 服务器地址输入行：左侧使用 `Server` 图标，编辑保存至本地 `setServerEndpoint`；
    - 连通性检测按钮：右侧或下方放置「测试连接」按钮，使用 `Activity` 图标，点击调用 `testServerHealthApi`，连通成功展示绿色 `CheckCircle2` 图标与「连接正常」，失败展示红色 `XCircle` 图标与「连接失败」。
  - 分组卡片四 存储、权限与时区：
    - 附件缓存清理行：左侧使用 `HardDrive` 图标并显示已缓存附件大小，右侧放置带 `Trash2` 图标的「清理附件缓存」按钮，点击调用 `clearAttachmentCache`；
    - 系统推送权限行：左侧使用 `Bell` 图标并展示当前授权状态，未授权时点击触发 `requestPushPermission`；
    - 本机同步时区只读行：左侧使用 `Globe` 图标，右侧展示当前自动同步的 IANA 时区名称。
- **点击跳转关系**：
  - 点击左上角 `ChevronLeft` 图标 → 返回 **界面 1 主聊天界面**。

---

## How to trigger / reach it
- 本模块完成前端全量界面与真实后端 HTTP 及 WebSocket 接口对接，必须使用 Playwright CLI 执行真实联调 E2E 测试，若环境未安装 Playwright CLI 需先安装就绪；
- 同时启动真实后端服务 `uvicorn backend.main:app` 与前端 Expo Web 服务 `npx expo start --web`，编写并运行端到端测试 `mobile/e2e/screens_flow.spec.ts`：
  1. 访问首页断言通过后端接口拉取会话并自动进入 `supervisor` 主聊天页，点击左上角 `PanelLeft` 展开侧边栏抽屉；
  2. 点击侧边栏新建按钮打开界面 3，点击头像打开界面 5 随机生成头像并点确认返回，输入 Bot 名称与「用来做什么」提交调用后端创建接口，断言自动跳转至新 Bot 聊天页并通过 WebSocket 收到新 Bot 主动问候气泡；
  3. 在聊天页发送文字与测试图片附件调用后端上传及 WebSocket 通道，验证工作期可立即连续插话发送且侧边栏对应 Bot 亮起工作绿点；
  4. 点击聊天页顶部名称进入界面 4 调用后端接口修改资料、切换模型并查看待触发提醒；再经侧边栏进入界面 6 系统设置页，切换深浅色模式、开启休息时间免打扰并修改起止时刻保存至后端、点击服务器测试连接，断言全部真实接口联调与路由跳转顺畅且控制台零报错。

## Driving it
- 运行全局静态门禁：`npm run lint && npx tsc --noEmit`
- 使用 Playwright CLI 运行前后端联调 E2E 测试：`npx playwright test mobile/e2e/screens_flow.spec.ts`

## Gotchas
- **路由页面严禁越界操作底层**：`mobile/app/` 下所有页面只能组合 `shared` 与 `features` 导出的公开组件与接口方法，严禁直接读写 SQLite、直接创建原生 WebSocket 或写入任何硬编码色值。
