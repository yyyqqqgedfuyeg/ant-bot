# 定时事件与积压通知异步轮询网关

- **模块根目录**：`backend/features/polling_gateway/`，随 `backend/main.py` 应用生命周期自动启停
- **唯一对外出口**：`backend/features/polling_gateway/__init__.py`，显式声明 `__all__`，导出 `PollingGateway` 与 `run_single_tick`
- **调用的前置模块契约**：
  - `backend/tools/features/event_inbox/__init__.py`，调用 `claim_due_events`、`mark_event_completed`、`recover_stale_events`
  - `backend/features/bot_lifecycle/__init__.py`，调用 `dispatch_to_bot` 唤醒目标 Bot
  - `backend/features/push_notifications/__init__.py`，调用 `flush_queued_pushes` 补推休息时段积压通知
- **底层设施依赖**：无

## Sub-features
- **到期事件非阻塞扫描与唤醒**：后台守护协程默认每 5 秒执行一次 `run_single_tick`，调用 `claim_due_events` 原子抢占到期事件，并通过后台并发任务调用 `dispatch_to_bot` 唤醒目标 Bot；目标 Bot 执行指令并真实调用 `send_to_user` 发消息后，调用 `mark_event_completed` 标记完成或推进下次周期时间。
- **休息时间结束自动补推**：在每轮 `run_single_tick` 中同步调用 `flush_queued_pushes`；一旦用户本地时间跨出设定的休息免打扰时段，网关自动将夜间或午休积压的 `'queued'` 通知补发出去。
- **异常僵尸任务恢复**：服务启动及周期巡检时调用 `recover_stale_events`，回收因异常中断而长期停留在 `processing` 状态的过期任务。

## How to trigger / reach it
- **异步不阻塞与补推联动单测**：编写 `tests/features/test_polling_gateway.py`，Mock 一个耗时的 `dispatch_to_bot` 并校验 `run_single_tick` 毫秒级返回不阻塞后续扫描，同时验证每轮扫描均会触发 `flush_queued_pushes` 结算积压通知。
- **端到端定时提醒观察**：编写脚本 `scripts/verify_12_polling_gateway.py`，在 `event_inbox` 写入一条立即到期的喝水提醒任务，执行 `run_single_tick` 并等待后台任务完成，打印目标 Bot 调用 `send_to_user` 落库的提醒语句及推送记录状态，核对提醒文案自然得体。

## Driving it
- 运行轮询扫描与补推联动单测：`pytest tests/features/test_polling_gateway.py -v`
- 运行到点唤醒提醒观察脚本：`python scripts/verify_12_polling_gateway.py`
- 运行架构门禁检查：`python scripts/lint_arch.py`

## Gotchas
- **后台任务引用保持与异常捕获**：所有异步派发的唤醒任务必须保存在活跃集合中并在完成回调里移除，同时捕获内部异常，避免单个事件失败拖垮整个轮询协程。
