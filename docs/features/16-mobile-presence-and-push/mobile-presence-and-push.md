# 前端前后台活跃上报、恢复重连与推送桥接

- **模块根目录**：`mobile/features/device_sync/`
- **唯一对外出口**：`mobile/features/device_sync/index.ts`，导出 `usePresenceMonitor`、`getDeviceTimezone`、`usePushNotifications`、`requestPushPermission`、`getPushPermissionStatus`
- **调用的前置模块契约**：`mobile/features/network_sync/index.ts`，调用 `reconnectSocket`、`sendPresenceFrame`、`sendHeartbeatFrame` 并读取服务器地址注册推送设备
- **底层设施依赖**：React Native `AppState`、`expo-localization`、`expo-notifications`

## Sub-features
- **前后台监听、心跳驱动与恢复自动重连**：`usePresenceMonitor` 监听系统 `AppState` 状态流转：
  - 应用处于前台 `'active'` 时：若当前 WebSocket 已断开则立即调用 `reconnectSocket()` 重新建连，随后发送携带本机 IANA 时区的 `presence:active` 帧，并启动固定周期定时器持续调用 `sendHeartbeatFrame()` 维持在线心跳；
  - 应用切入 `'inactive'` 或 `'background'` 时：立即清除心跳定时器并发送 `presence:inactive` 帧；若后台停留较久，服务端在累计丢失心跳达到次数阈值后会自动断开连接，待用户重新回到前台时由上述恢复逻辑无缝重连补齐。
- **推送权限与设备 Token 上报**：提供查询与申请系统通知权限方法，授权通过后提取 `expo_push_token` 调用后端设备注册接口完成绑定。
- **通知点击直达目标会话**：`usePushNotifications` 监听用户点击系统通知栏消息事件，从通知数据中提取 `bot_id` 并执行传入的跳转回调，直接打开对应 Bot 的聊天页。

## How to trigger / reach it
- 编写单元测试 `mobile/features/device_sync/__tests__/device_sync.test.ts`：
  1. 挂载 `usePresenceMonitor` 处于前台状态，断言立即发出携带当前时区的 `presence:active` 帧并按周期持续发出 `heartbeat` 帧；
  2. 模拟 `AppState` 切至后台，断言立即停止心跳定时器并发出 `presence:inactive` 帧；再模拟连接已断开后切回前台 `'active'`，断言立即触发 `reconnectSocket()` 并恢复发送活跃帧与心跳；
  3. 模拟点击一条包含 `bot_id: "bot_demo"` 的系统通知，断言导航回调收到 `"bot_demo"` 参数。

## Driving it
- 运行前后台重连联动与通知路由单测：`npx jest mobile/features/device_sync/__tests__/device_sync.test.ts`
- 运行全局静态检查：`npm run lint && npx tsc --noEmit`

## Gotchas
- **非真机环境推送降级处理**：在 Web 浏览器或缺少推送证书的开发环境中调用推送注册时须捕获环境不支持异常并静默降级，不得阻断应用主界面渲染。
