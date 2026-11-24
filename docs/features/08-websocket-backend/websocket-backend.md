# WebSocket 实时双向通道与心跳断连服务

- **模块根目录**：`backend/features/websocket_chat/`
- **唯一对外出口**：`backend/features/websocket_chat/__init__.py`，显式声明 `__all__`，导出 `ws_router`、`broadcast_bot_messages`、`broadcast_bot_status`、`set_user_message_handler`
- **调用的前置模块契约**：`backend/features/presence/__init__.py`，联动更新用户活跃状态、时区与心跳检测
- **底层设施依赖**：`backend/shared/db/__init__.py`，负责用户消息幂等落库与按 `seq` 增量读取 `messages`

## Sub-features
- **强制心跳监测与超时主动断连**：每条 WebSocket 连接建立后启动服务端心跳巡检协程；客户端按约定周期发来 `heartbeat` 帧时调用 `presence.record_heartbeat()`，若连续未收到心跳达到阈值触发超时，服务端立即主动关闭该 WebSocket 连接并将用户置为离线非活跃状态。
- **用户消息即时落库与无等待分发**：收到用户发来的图文元数据消息帧后，按 `client_temp_id` 幂等写入 `messages` 表并立即回发包含正式 `id` 与 `seq` 的确认帧；同时立即异步触发 `user_message_handler` 送入目标 Bot，不因目标 Bot 当前正在工作而阻塞等待。
- **状态与消息实时广播**：对外提供 `broadcast_bot_messages` 实时推送新气泡，提供 `broadcast_bot_status` 实时广播任意 Bot 的 `working` 或 `idle` 状态。
- **恢复重连增量补齐**：当客户端网络或前后台恢复重新建立连接并发送携带各会话 `last_synced_seq` 的 `sync` 帧时，服务端仅查询返回 `seq > last_synced_seq` 的缺失消息与当前所有处于 `working` 状态的 Bot 标识。

## How to trigger / reach it
- 编写 WebSocket 集成单测 `tests/features/test_websocket_backend.py`，将测试环境心跳检测周期缩短至百毫秒级：
  1. 建立连接后停止发送客户端心跳帧，断言达到最大丢失次数后服务端主动断开连接且 `presence.is_user_active()` 变为 `False`；
  2. 模拟用户恢复状态后重新建立连接并发送 `presence:active` 与 `sync` 帧，断言活跃态恢复为 `True` 且准确补齐断连期间新增的 `seq` 消息；
  3. 重复发送相同 `client_temp_id` 的用户消息帧，断言数据库仅存一条记录且立即触发消息分发回调。

## Driving it
- 运行心跳超时断连与重连同步单测：`pytest tests/features/test_websocket_backend.py -v`
- 运行架构门禁检查：`python scripts/lint_arch.py`

## Gotchas
- **严禁经 WebSocket 传输文件字节流**：图片与文档一律先走模块 `05` 的 HTTP 接口上传，WebSocket 消息帧仅传递附件路径与宽高元数据。
