# 用户活跃状态维护与时区同步后端服务

- **模块根目录**：`backend/features/presence/`
- **唯一对外出口**：`backend/features/presence/__init__.py`，显式声明 `__all__`，导出 `mark_active`、`mark_inactive`、`record_heartbeat`、`check_heartbeat_timeout`、`is_user_active`、`get_user_timezone`
- **调用的前置模块契约**：无
- **底层设施依赖**：`backend/shared/db/__init__.py`，读写 `user_settings.timezone`

## Sub-features
- **前后台状态即时切换**：收到客户端前台通知时调用 `mark_active` 将活跃态置为 `True` 并清零心跳丢失计数；收到切后台通知或连接断开时调用 `mark_inactive` 立即将活跃态置为 `False`。
- **心跳丢失计数与超时离线判定**：客户端前台连接期间需按固定周期上报心跳并调用 `record_heartbeat`；每次心跳巡检调用 `check_heartbeat_timeout` 累加未收到心跳的次数，一旦连续丢失心跳达到阈值如 3 次，立即将活跃态置为 `False` 并通知上层断开失效连接。
- **本机时区自动同步**：`mark_active` 接收到合法的 IANA 时区字符串且与当前配置不同时，自动写入 `user_settings.timezone`。

## How to trigger / reach it
- 编写单元测试 `tests/features/test_presence.py`：
  1. 校验初始状态下 `is_user_active()` 为 `False`；
  2. 调用 `mark_active` 传入 `"Asia/Tokyo"`，断言 `is_user_active()` 变为 `True` 且数据库 `user_settings.timezone` 已更新；传入非法时区字符串时保持原有效时区不变；
  3. 连续调用 `check_heartbeat_timeout` 模拟连续 3 个周期未收到心跳，断言触发超时判定且 `is_user_active()` 自动回落为 `False`；再次调用 `mark_active` 后恢复为 `True`。

## Driving it
- 运行活跃状态、心跳计数与时区同步单测：`pytest tests/features/test_presence.py -v`
- 运行架构门禁检查：`python scripts/lint_arch.py`

## Gotchas
- **时区合法性前置校验**：写入数据库前必须用 `zoneinfo.ZoneInfo` 验证时区字符串有效，防止脏数据污染 `user_settings` 表。
