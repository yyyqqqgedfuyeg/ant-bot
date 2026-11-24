# 跨 Bot 后台任务委派工具

- **模块根目录**：`backend/tools/features/bot_communication/`
- **唯一对外出口**：`backend/tools/features/bot_communication/__init__.py`，显式声明 `__all__`，导出 `create_delegation_tool`
- **调用的前置模块契约**：
  - `backend/features/bot/__init__.py`，仅在验证脚本中创建多 Bot 实例实测
  - `backend/features/websocket_chat/__init__.py`，调用 `broadcast_bot_status` 实时广播子 Bot 忙闲态
  - `backend/tools/features/chat_to_user/__init__.py`，开启子 Bot 委派期直连屏蔽上下文
- **底层设施依赖**：无

## Sub-features
- **后台跨 Bot 委派协作**：挂载至 Bot 的工具名称为 `delegate_to_bot`，支持总管或任意 Bot 指定目标 `target_bot_id` 与具体任务内容发起后台调用，等待目标子 Bot 处理完毕后拿到返回文本结论。
- **子 Bot 工作状态透传**：目标子 Bot 开始处理委派任务时立即广播 `working` 状态，任务结束时广播 `idle` 状态，使手机侧边栏中正在后台协同干活的子 Bot 头像同样亮起呼吸绿点。
- **越级发消息拦截与防死循环**：委派执行全程包裹 `chat_to_user` 屏蔽上下文，确保子 Bot 不会直接向用户发气泡或触发推送通知；同时维护调用链栈，限制最大委派深度不超过 3 层并拦截环状互调。

## How to trigger / reach it
- **环路与深度拦截单测**：编写 `tests/tools/test_bot_comm_guard.py`，模拟 A 委派 B 再回头委派 A 的循环调用及超深度调用，断言立即被拦截返回错误提示，且子 Bot 状态正确复位为 `idle`。
- **双 Bot 真实委派观察**：编写脚本 `scripts/verify_10_bot_comm.py`，创建总管 Bot 与专长子 Bot，向总管提出需要专长协助的请求，打印控制台事件流，核对总管先调用 `send_to_user` 回应用户、随后委派专长子 Bot、子 Bot 状态变更为 `working` 且未向用户发消息、最后总管汇总结果调用 `send_to_user` 答复用户。

## Driving it
- 运行调用链防护单测：`pytest tests/tools/test_bot_comm_guard.py -v`
- 运行双 Bot 后台委派观察脚本：`python scripts/verify_10_bot_comm.py`
- 运行架构门禁检查：`python scripts/lint_arch.py`

## Gotchas
- **异常兜底复位状态**：子 Bot 执行过程无论正常返回还是抛出异常，都必须在 `finally` 逻辑中广播 `idle` 状态，防止前端侧边栏工作绿点卡死常亮。
