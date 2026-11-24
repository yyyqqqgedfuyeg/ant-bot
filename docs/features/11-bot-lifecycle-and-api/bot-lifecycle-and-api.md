# Bot 生命周期编排与全量后端接口总入口

- **模块根目录**：`backend/features/bot_lifecycle/` 与服务启动入口 `backend/main.py`
- **唯一对外出口**：`backend/features/bot_lifecycle/__init__.py`，显式声明 `__all__`，导出 `bot_api_router`、`init_preset_bots`、`dispatch_to_bot`、`get_or_create_bot_runtime`
- **调用的前置模块契约**：
  - `backend/features/bot/__init__.py`
  - `backend/tools/features/shared_memory/__init__.py`
  - `backend/tools/features/event_inbox/__init__.py`
  - `backend/features/file_transfer/__init__.py`
  - `backend/features/push_notifications/__init__.py`
  - `backend/features/websocket_chat/__init__.py`
  - `backend/tools/features/chat_to_user/__init__.py`
  - `backend/tools/features/bot_communication/__init__.py`
- **底层设施依赖**：`backend/shared/db/__init__.py` 与 `backend/roles/` 静态提示词文件

## Sub-features
- **提示词动态拼装与私人助手人设注入**：默认仅预置 `backend/roles/supervisor.md` 作为总管角色提示词；用户新建自定义 Bot 时，直接将用户填写的「用来做什么」即 `purpose_one_liner` 与名称拼入系统提示词作为角色定义。所有 Bot 统一拼入 `backend/roles/personal_agent.md` 私人助手沟通准则、最新 `shared_memories` 全量记忆与用户本地时区，并挂载四大业务工具。
- **新建 Bot 主动短句问候**：自定义 Bot 写入 `bots` 表后，后台异步向其会话投递 `backend/roles/after_init.md` 引导指令，驱动新 Bot 结合自身用途先调用 1 到 3 次 `send_to_user` 发出自然短句同用户打招呼，并主动询问想要解决什么具体问题。
- **用户消息无队列立即送达**：将 `dispatch_to_bot` 注册给 WebSocket 入站消息处理器；当目标 Bot 正在执行任务时用户再次发来新消息，直接调用 `AntigravityBot` 即时送达接口注入当前活跃会话，不排队列等待上一轮任务结束。
- **全量业务与设置 REST 接口**：提供 Bot 列表查询、新建自定义 Bot、修改 Bot 资料与单 Bot 模型热切换、查询该 Bot 待触发定时事件、删除非预置 Bot、查询与修改全局配置接口 `/api/settings` 涵盖全局默认模型及休息时间免打扰开关与起止时刻，以及 `/api/health` 连通性检测；在 `backend/main.py` 汇总挂载所有 HTTP 与 WebSocket 路由。

## How to trigger / reach it
- **确定性管理接口单测**：编写 `tests/features/test_bot_lifecycle_api.py`，测试启动后预置 `supervisor` 自动存在且禁止删除、新建与编辑自定义 Bot 字段落库、通过 `/api/settings` 更新休息免打扰起止时间与全局默认模型生效、以及 `/api/health` 正常返回。
- **新建主动问候与中途插话观察**：编写脚本 `scripts/verify_11_bot_lifecycle.py`，调用新建接口创建一个用途为“辅助制定英语口语练习计划”的自定义 Bot，等待数秒打印其在 `messages` 表产生的消息，观察是否真实调用 1 到 3 次 `send_to_user` 发出自然招呼并追问具体需求；随后发一条耗时任务并在中途立即追加新消息，观察即时响应效果。

## Driving it
- 运行管理与设置接口单测：`pytest tests/features/test_bot_lifecycle_api.py -v`
- 运行新建破冰问候与插话观察脚本：`python scripts/verify_11_bot_lifecycle.py`
- 运行架构门禁检查：`python scripts/lint_arch.py`

## Gotchas
- **新建接口立即响应**：HTTP 创建接口落库后须立刻返回新 Bot 信息供前端直接进入聊天页，`after_init.md` 唤醒打招呼必须在后台异步执行，禁止阻塞创建请求。
