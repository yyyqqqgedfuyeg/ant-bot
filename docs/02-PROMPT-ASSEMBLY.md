# 系统提示词与挂载工具拼装契约

静态提示词保存在 `backend/roles/` 目录下，工具调用规范直接内聚在 `backend/tools/features/` 各工具注册给 SDK 的 `description` 描述中，动态上下文在创建或唤醒会话时由 `backend/features/bot_lifecycle` 统一拼装注入。

## 1. 静态提示词文件规划

系统默认仅维护一套预置总管角色文件，其余自定义 Bot 直接使用用户创建时填写的用途内容作为角色设定：

```text
backend/roles/
├── supervisor.md        # 系统唯一预置角色提示词：定义总管职责，负责日常接待、任务拆解、委派专长 Bot 并汇总回复用户
├── personal_agent.md    # 全员共享的私人助手准则：明确自身是有温度的贴身 Personal Agent，而非沉默闷头干活的工具人
└── after_init.md        # 新建自定义 Bot 首轮唤醒引导词：驱动新 Bot 主动发出 1 到 3 句短句问候并询问具体需求
```

### 核心人设与主动交互要求
- **私人助手准则 `personal_agent.md`**：所有预置与自定义 Bot 均必须拼入该段提示词。要求 Bot 始终以私人伙伴与助手的口吻同用户交流；遇到需要检索、读写文件、执行命令或委派他人的耗时任务时，绝不能一言不发直接埋头苦干让用户空等，必须先主动调用 `send_to_user` 工具自然回应用户一句告知正在处理，执行完后再调用 `send_to_user` 汇报进展或结果。严禁使用硬编码脚本代替 Bot 发送假回复。
- **自定义 Bot 职责注入**：用户新建 Bot 时填写的名称 `name` 与「用来做什么」即 `purpose_one_liner`，直接拼入该 Bot 的系统提示词作为专属身份与职责说明。
- **新建破冰引导 `after_init.md`**：自定义 Bot 创建落库后立即触发该提示词，要求 Bot 围绕用户刚设定的职责，先真实调用 1 到 3 次 `send_to_user` 工具向用户发送 1 到 3 句简短自然的开场招呼，并主动询问用户当前想解决什么问题或偏好细节。

## 2. 四大挂载工具目录与描述准则

所有挂载到 Bot 的业务工具统一存放在 `backend/tools/features/` 下：

```text
backend/tools/features/
├── shared_memory/       # 模块 03：读写跨 Bot 全局共享短记忆
├── event_inbox/         # 模块 04：按用户时区创建、查询、取消定时与周期事件
├── chat_to_user/        # 模块 09：send_to_user 向用户发送聊天消息，系统唯一触发通知的出口
└── bot_communication/   # 模块 10：delegate_to_bot 跨 Bot 后台委派协作
```

各工具的 `description` 必须向模型交代清楚使用边界：
1. `shared_memory`：静默记录与查询用户的长期稳定背景、习惯与偏好，单条不超过 120 字；写入后不要在聊天中刻意邀功播报；禁止存入带时间的提醒事项。
2. `event_inbox`：凡带有明确触发时间点或周期规律的提醒与自动任务，一律写入事件箱并按用户本地时区换算，严禁写入共享记忆。
3. `chat_to_user`：唯一向用户聊天框发送消息的工具 `send_to_user`。要求像真人在即时通讯软件聊天一样简短自然，拒绝长篇大论；单轮对话可连续调用 1 到 3 次发送多条短气泡。
4. `bot_communication`：将子任务在后台交由其他指定 `bot_id` 执行并获取返回结论；被委派的子 Bot 严禁直接调用 `send_to_user` 打扰用户，只能把结论交回发起方。

## 3. 会话系统提示词动态拼装顺序

由模块 `11` 在初始化或刷新 Bot 会话时按固定顺序拼接：
1. **角色身份段**：若为 `supervisor` 则读取 `backend/roles/supervisor.md`；若为用户新建 Bot 则注入其 `name` 与 `purpose_one_liner`。
2. **私人助手交互准则段**：拼入 `backend/roles/personal_agent.md`。
3. **全局共享记忆段**：注入 `shared_memories` 表当前全量键值列表。
4. **时区与时间参考段**：注入 `user_settings.timezone` 用户当前时区及对应的本地当前时间。
5. **挂载工具集**：保留 `AntigravityBot` 内置工具，并注册 `backend/tools/features/` 下的四大工具。
