# 离线通知推送与休息时间免打扰后端服务

- **模块根目录**：`backend/features/push_notifications/`
- **唯一对外出口**：`backend/features/push_notifications/__init__.py`，显式声明 `__all__`，导出设备注册路由 `push_router`、`notify_on_bot_message`、`flush_queued_pushes`
- **调用的前置模块契约**：`backend/features/presence/__init__.py`，调用 `is_user_active` 判断用户当前是否在线
- **底层设施依赖**：`backend/shared/db/__init__.py`，读写 `device_push_tokens`、`push_records` 与 `user_settings` 表

## Sub-features
- **唯一触发入口与在线免推**：全系统仅有 `send_to_user` 工具会调用 `notify_on_bot_message`；若 `is_user_active()` 为 `True` 代表用户正在前台查看应用，直接跳过系统推送。
- **休息时间免打扰积压机制**：当用户离线需要推送时，按 `user_settings.timezone` 计算用户当前本地时间，并与 `user_settings` 中的 `quiet_hours_enabled`、`quiet_hours_start`、`quiet_hours_end` 比对：
  - 若未开启免打扰或当前处于非休息时段，立即向 Expo Push 接口发送通知，携带目标 `bot_id` 路由参数，并在 `push_records` 记录为 `'sent'`；
  - 若当前处于用户设定的休息时段，绝不发出声音或系统通知，将该条推送写入 `push_records` 标记为 `'queued'` 静默积压。
- **非休息时段统一补推**：提供 `flush_queued_pushes` 供后台轮询网关定期调用；当检测到本地时间已离开休息时段且存在 `'queued'` 积压记录时，若用户仍离线则按每个 Bot 合并积压摘要集中补推并更新为 `'sent'`，若用户此刻已在线则直接标记为 `'skipped_online'` 避免重复打扰。

## How to trigger / reach it
- 编写单元测试 `tests/features/test_push_backend.py`，Mock 外部 Expo Push HTTP 接口并注入测试时钟：
  1. 用户在线时调用 `notify_on_bot_message`，断言外部推送请求次数为 `0`；
  2. 用户离线且开启 `23:00` 至 `08:00` 休息免打扰，模拟凌晨 `01:30` 连续触发 2 条消息，断言外部推送请求次数为 `0` 且 `push_records` 存在 2 条 `'queued'` 记录；
  3. 将测试时钟推进至早上 `08:05` 调用 `flush_queued_pushes`，断言积压记录合并发出 1 次系统推送请求，且状态全部更新为 `'sent'`。

## Driving it
- 运行离线推送与休息时段积压补推单测：`pytest tests/features/test_push_backend.py -v`
- 运行架构门禁检查：`python scripts/lint_arch.py`

## Gotchas
- **跨零点时间段判断**：休息时间普遍跨越午夜零点，例如 `23:00` 到次日 `08:00`，也可能是同日午休如 `12:30` 到 `14:00`，时间区间比对必须同时正确覆盖跨天与同天两种情况。
