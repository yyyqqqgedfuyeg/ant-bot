# 对用户发送消息工具

- **模块根目录**：`backend/tools/features/chat_to_user/`
- **唯一对外出口**：`backend/tools/features/chat_to_user/__init__.py`，显式声明 `__all__`，导出 `create_send_to_user_tool` 与子 Bot 委派屏蔽上下文管理器
- **调用的前置模块契约**：
  - `backend/features/bot/__init__.py`，仅在验证脚本中用于挂载工具实测
  - `backend/features/push_notifications/__init__.py`，调用 `notify_on_bot_message`
  - `backend/features/websocket_chat/__init__.py`，调用 `broadcast_bot_messages`
- **底层设施依赖**：`backend/shared/db/__init__.py`，按递增 `seq` 写入 `messages` 表

## Sub-features
- **真实工具驱动与短句沟通准则**：挂载至 Bot 的工具名称为 `send_to_user`，严禁编写任何预设文案脚本在后台冒充 Bot 自动假回复用户，所有呈现给用户的气泡均必须由 Bot 真实调用该工具发出。工具 `description` 要求模型像真人发即时消息一样自然简短，拒绝长篇大论，单轮可连续调用 1 到 3 次发送多条短句。
- **全系统唯一推送触发出口**：每次调用 `send_to_user` 将消息分配递增 `seq` 落盘至 `messages` 表后，一方面通过 `broadcast_bot_messages` 实时广播给在线 WebSocket 客户端，另一方面调用 `notify_on_bot_message` 进入离线与免打扰推送判定；除本工具外，系统任何其他地方均不触发通知推送。
- **被委派子 Bot 直连拦截**：提供委派期屏蔽上下文；当某个子 Bot 正在后台执行其他 Bot 委派的任务时，禁止其调用 `send_to_user` 直接向用户发消息或发通知，工具直接返回提示要求其将结果整理后交回上游调用方。

## How to trigger / reach it
- **确定性落库与拦截单测**：编写 `tests/tools/test_chat_to_user.py`，验证连续多次调用 `send_to_user` 时 `seq` 严格递增且均触发 `notify_on_bot_message`，并验证处于委派屏蔽上下文中调用该工具时被成功拦截且不写入 `messages` 表。
- **Bot 真实短句沟通观察**：编写脚本 `scripts/verify_09_chat_to_user.py`，实例化注入私人助手准则并挂载 `send_to_user` 的 Bot，交办一项需要先读取本地文件再总结的任务，打印 `messages` 表全部生成记录，观察 Bot 是否先主动调用 `send_to_user` 自然回应一句再去执行读取，完成后再发 1 到 3 条短句汇报结果。

## Driving it
- 运行消息投递与委派拦截单测：`pytest tests/tools/test_chat_to_user.py -v`
- 运行真实工具调用沟通观察脚本：`python scripts/verify_09_chat_to_user.py`
- 运行架构门禁检查：`python scripts/lint_arch.py`

## Gotchas
- **严禁把模型裸返回值当聊天消息入库**：Bot 对用户的可见表达统一收敛在 `send_to_user` 工具调用上，后台内部思考或面向调用方的返回文本不得直接写入用户聊天表。
