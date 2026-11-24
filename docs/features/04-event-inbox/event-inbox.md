# 定时与周期事件收件箱工具

- **模块根目录**：`backend/tools/features/event_inbox/`
- **唯一对外出口**：`backend/tools/features/event_inbox/__init__.py`，显式声明 `__all__`，导出供 Bot 挂载的事件管理工具及供轮询网关调用的 `list_bot_pending_events`、`claim_due_events`、`mark_event_completed`、`recover_stale_events`
- **调用的前置模块契约**：`backend/features/bot/__init__.py`，仅在验证脚本中用于挂载工具实测
- **底层设施依赖**：`backend/shared/db/__init__.py`，操作 `event_inbox` 表并读取 `user_settings.timezone`

## Sub-features
- **时间与周期指令强路由**：工具 `description` 明确规定，凡包含未来触发时间点或周期规律的提醒与自动任务，支持 `once` 单次与 `cron` 周期两种类型，一律调用本工具写入事件箱，严禁写入 `shared_memories`。
- **对齐用户本机时区换算**：读取 `user_settings.timezone` 解析目标时间与 Cron 表达式，精准换算为 `next_run_at_utc` 落盘，彻底消除服务器本地时区干扰。
- **原子抢占与恢复接口**：对外提供单条 SQL 原子抢占到期事件的 `claim_due_events`、结算完成并自动推进周期任务下次触发时间的 `mark_event_completed`、以及重置异常卡死任务的 `recover_stale_events`。

## How to trigger / reach it
- **确定性时区与并发抢占单测**：编写 `tests/tools/test_event_inbox.py`，分别设置不同用户时区校验 `next_run_at_utc` 换算结果、验证多协程并发调用 `claim_due_events` 不会重复抢占同一事件、以及超时僵尸任务恢复逻辑。
- **Bot 自然语言提单观察**：编写脚本 `scripts/verify_04_event_inbox.py`，实例化挂载事件箱工具的 Bot，输入“每周五晚上九点提醒我上号打游戏”，打印 `event_inbox` 表新增记录与回复内容，观察 Cron 表达式与触发时间是否符合语义。

## Driving it
- 运行时区换算与原子抢占单测：`pytest tests/tools/test_event_inbox.py -v`
- 运行自然语言创建事件观察脚本：`python scripts/verify_04_event_inbox.py`
- 运行架构门禁检查：`python scripts/lint_arch.py`

## Gotchas
- **禁止硬编码时区偏移**：必须基于标准库 `zoneinfo` 与 `croniter` 动态换算 UTC 触发点，兼容夏令时与用户跨时区行程变化。
