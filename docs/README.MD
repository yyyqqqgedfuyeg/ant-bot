# Always-On Personal Bot 开发总索引

所有模块严格按照序号递增顺序依次开发，从 `01` 推进至 `20`。后端模块优先完成，前端模块随后推进，前后端职责彻底分离，不存在循环依赖或超前引用。每份文档面向独立的 AI 开发会话，聚焦业务边界、公开契约与可落地的验收方式。

## 0. 新开 AI 会话读取与开发协议

1. **必读全局底座**：
   - 所有会话必读：`00-ARCHITECTURE.md`
   - 涉及服务端数据库或手机本地存储的会话必读：`01-DATA-CONTRACT.md`
   - 涉及后端 Bot 工具或生命周期编排的会话必读：`02-PROMPT-ASSEMBLY.md`
2. **必读当前目标**：每次仅读取当前开发的单篇 `features/{NN}-{slug}/{slug}.md` 文档。
3. **跨模块只读白名单**：
   - 仅允许读取目标文档头部「调用的前置模块契约」列出的 `__init__.py` 或 `index.ts`，以及 `00-ARCHITECTURE.md` 声明的共享基础层公开出口；
   - 若「调用的前置模块契约」标记为 `无`，代表该模块为叶子节点，严禁读取其他任何业务或工具模块；
   - 严禁打开、搜索或引用任何非当前模块的 `internal/` 目录。
4. **收尾验收门禁**：
   - 内部实现全部放入 `internal/`，唯一公开出口收敛至 `__init__.py` 或 `index.ts`；
   - 确定性数据、接口与规则逻辑通过 `pytest` 或 `jest` 校验；涉及大模型自然语言回复或工具调用决策的场景，统一编写并运行独立观察脚本，核对实际输出语义是否符合预期；
   - 凡涉及前端界面开发并对接后端接口的模块，必须同时启动真实后端服务与前端 Expo Web，使用 Playwright CLI 执行端到端 E2E 测试，若环境未安装 Playwright CLI 需先安装；
   - 后端必过 `python scripts/lint_arch.py`，前端必过 `npm run lint` 与 `npx tsc --noEmit`。
5. **分支与合并规范**：
   - 新建模块开发时，必须基于 `main` 分支拉取并新建独立开发分支；
   - 开发与上述门禁验收完成后，提交 Commit 并创建 Pull Request 至 `main`，待 GitHub Actions 检查全部通过且无冲突文件后再执行合并。

---

## 模块开发顺序总表

### 第一阶段：后端数据库底座与基础引擎
1. [01-db-and-arch-gate](./features/01-db-and-arch-gate/db-and-arch-gate.md) — 服务端 SQLite WAL 数据库底座与黑盒架构门禁脚本
2. [02-base-bot](./features/02-base-bot/base-bot.md) — 基础 Antigravity Bot 封装，支持多会话隔离、运行中即时插话与自动压缩

### 第二阶段：后端挂载工具与基础通信服务
3. [03-shared-memory](./features/03-shared-memory/shared-memory.md) — 跨 Bot 共享短记忆工具，位于 `backend/tools/features/shared_memory/`
4. [04-event-inbox](./features/04-event-inbox/event-inbox.md) — 定时与周期事件箱工具及抢占接口，位于 `backend/tools/features/event_inbox/`
5. [05-file-transfer-backend](./features/05-file-transfer-backend/file-transfer-backend.md) — 无隔离共享工作区文件上传、图片尺寸提取与下载后端服务
6. [06-presence-backend](./features/06-presence-backend/presence-backend.md) — 用户活跃状态维护、心跳丢失计数判定与时区同步后端服务
7. [07-push-backend](./features/07-push-backend/push-backend.md) — 离线通知推送、休息时间免打扰积压与到点补推后端服务
8. [08-websocket-backend](./features/08-websocket-backend/websocket-backend.md) — WebSocket 双向实时通道、心跳超时强制断连与断线增量同步服务

### 第三阶段：后端核心交互工具、生命周期编排与轮询网关
9. [09-chat-to-user](./features/09-chat-to-user/chat-to-user.md) — 对用户发消息工具，位于 `backend/tools/features/chat_to_user/`，唯一触发通知入口
10. [10-bot-communication](./features/10-bot-communication/bot-communication.md) — 跨 Bot 后台任务委派工具，位于 `backend/tools/features/bot_communication/`
11. [11-bot-lifecycle-and-api](./features/11-bot-lifecycle-and-api/bot-lifecycle-and-api.md) — Bot 生命周期编排、私人助手提示词拼装、创建主动问候与全量后端接口总入口
12. [12-polling-gateway](./features/12-polling-gateway/polling-gateway.md) — 定时事件异步轮询唤醒与休息时段积压通知补推网关

### 第四阶段：前端主题底座、离线缓存与网络设备桥接
13. [13-ui-theme-system](./features/13-ui-theme-system/ui-theme-system.md) — Expo 深浅色语义化主题色板、基础 UI 原语与 ESLint 门禁
14. [14-mobile-local-cache](./features/14-mobile-local-cache/mobile-local-cache.md) — 手机端 SQLite 与 MMKV 本地缓存、乐观消息原地替换与草稿存储
15. [15-mobile-network-sync](./features/15-mobile-network-sync/mobile-network-sync.md) — 前端 WebSocket 心跳保活与恢复重连、REST 客户端与附件上传下载封装
16. [16-mobile-presence-and-push](./features/16-mobile-presence-and-push/mobile-presence-and-push.md) — 前端前后台状态上报、恢复活跃自动重连、时区同步与推送通知路由桥接

### 第五阶段：前端业务组件与全量界面组装
17. [17-bot-avatar](./features/17-bot-avatar/bot-avatar.md) — 原生 SVG 轻量头像渲染组件与可视化分类定制面板组件
18. [18-imessage-chat-ui](./features/18-imessage-chat-ui/imessage-chat-ui.md) — 仿 iMessage 聊天流组件，支持连发分组、随时立即插话发送与键盘联动
19. [19-sidebar-and-status](./features/19-sidebar-and-status/sidebar-and-status.md) — 手势侧边栏抽屉组件与 Bot 后台工作中呼吸绿点动效
20. [20-frontend-screens](./features/20-frontend-screens/frontend-screens.md) — 移动端 6 大核心界面完整布局、图标规范、免打扰时段设置与路由跳转组装
