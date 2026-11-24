# 前端实时通信、心跳重连与接口客户端

- **模块根目录**：`mobile/features/network_sync/`
- **唯一对外出口**：`mobile/features/network_sync/index.ts`，导出 `NetworkSyncProvider`、`useConnectionStatus`、`useBotWorkingStatuses`、`reconnectSocket`、`sendPresenceFrame`、`sendHeartbeatFrame`、`sendUserMessage`、`syncBotsFromServer`、`createBotApi`、`updateBotApi`、`deleteBotApi`、`fetchBotEventsApi`、`fetchUserSettingsApi`、`updateUserSettingsApi`、`testServerHealthApi`、`pickAndUploadAttachments`、`downloadAndCacheAttachment`
- **调用的前置模块契约**：`mobile/features/local_cache/index.ts`，将同步到的 Bot 列表、增量消息、发送回执与下载文件路径实时写入本地缓存
- **底层设施依赖**：WebSocket、`fetch`、`expo-image-picker`、`expo-document-picker`、`expo-file-system`

## Sub-features
- **连接管理、心跳断连感知与恢复重连**：维护 WebSocket 连接状态 `'connected'`、`'connecting'` 或 `'disconnected'`；前台期间配合设备模块定时发出 `heartbeat` 帧；若因切后台停止心跳或网络异常被服务端达到超时次数主动断开，连接状态转为 `'disconnected'`；当收到 `reconnectSocket()` 调用或网络恢复且处于前台时，立即重新建立连接，自动读取各会话本地 `last_synced_seq` 发送 `sync` 帧补齐缺失消息与最新工作状态。
- **无等待立即发送与多附件上传**：`pickAndUploadAttachments` 支持多选图片、拍照或挑选文档并经后端 `/api/files/upload` 获取包含图片宽高的附件元数据；`sendUserMessage` 不受目标 Bot 当前是否处于 `working` 状态限制，任何时刻点击发送均立即写入本地乐观消息并通过 WebSocket 实时发出，绝不在前端排队阻塞。
- **全量业务与免打扰设置接口封装**：封装 Bot 列表同步、新建、编辑、删除、查询指定 Bot 待触发事件、读写 `/api/settings` 全局模型与休息免打扰时段配置，以及 `/api/health` 服务器连通性测试。

## How to trigger / reach it
- 编写单元测试 `mobile/features/network_sync/__tests__/network_sync.test.ts`，通过 Mock WebSocket 与 Mock `fetch` 验证：
  1. 当某个 Bot 处于 `working` 状态时连续调用 `sendUserMessage`，断言消息立即发出且收到服务端 `ack` 后原地更新为 `'sent'`；
  2. 模拟服务端因心跳超时主动关闭连接后状态变为 `'disconnected'`，随后调用 `reconnectSocket()`，断言成功重连并自动携带最新 `last_synced_seq` 发送增量同步请求；
  3. 验证 `fetchUserSettingsApi` 与 `updateUserSettingsApi` 正确读写全局默认模型与休息时间免打扰参数。

## Driving it
- 运行网络同步、心跳重连与接口单测：`npx jest mobile/features/network_sync/__tests__/network_sync.test.ts`
- 运行全局静态检查：`npm run lint && npx tsc --noEmit`

## Gotchas
- **附件上传先于消息帧发出**：带有图片或文件附件的消息必须先走 HTTP 上传拿到服务端共享路径与图片尺寸元数据，再随 WebSocket 消息帧发出。
