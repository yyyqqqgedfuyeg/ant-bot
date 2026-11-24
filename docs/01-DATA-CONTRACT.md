# 数据库与本地存储契约

Bot 推理步骤、工具调用日志与会话历史由 `google-antigravity` SDK 原生管理，本数据库严禁重复建表。服务端 SQLite 启动时必须开启 `WAL` 日志模式，设置 `synchronous=NORMAL` 与 `busy_timeout=5000`，所有写入均须在短事务中快速完成。

---

## 一、服务端 SQLite 表结构

全部服务端表由模块 `01` 在 `backend/shared/db` 中统一建表与维护。

### 1. `bots` 表
- `id`: TEXT 主键，唯一 `bot_id`，系统预置总管固定为 `'supervisor'`，自定义 Bot 使用 UUID
- `name`: TEXT 非空，Bot 显示名称
- `purpose_one_liner`: TEXT 非空，用户在创建或编辑时填写的用途说明，直接注入自定义 Bot 的系统提示词
- `avatar_config_json`: TEXT 非空，头像定制参数 JSON 字符串
- `default_model`: TEXT 非空，该 Bot 当前使用的模型标识，如 `'gemini-4-Hydrogen'`
- `is_preset`: INTEGER 非空，默认 `0`；`1` 代表系统预置不可删除，`0` 代表用户自定义可删除
- `created_at`: DATETIME 非空，UTC ISO8601 时间
- `updated_at`: DATETIME 非空，UTC ISO8601 时间

### 2. `user_settings` 表
- `id`: INTEGER 主键，固定单行记录，取值恒为 `1`
- `timezone`: TEXT 非空，默认 `'Asia/Shanghai'`，用户手机进入前台时自动同步本机 IANA 时区，定时任务与休息时间均以此为准
- `global_default_model`: TEXT 非空，默认 `'gemini-4-Hydrogen'`，新建 Bot 默认继承的模型标识
- `quiet_hours_enabled`: INTEGER 非空，默认 `0`；`1` 表示开启休息时间免打扰，`0` 表示关闭
- `quiet_hours_start`: TEXT 非空，默认 `'23:00'`，本地 24 小时制 `HH:MM` 格式的休息开始时间
- `quiet_hours_end`: TEXT 非空，默认 `'08:00'`，本地 24 小时制 `HH:MM` 格式的休息结束时间，支持跨零点区间
- `updated_at`: DATETIME 非空，UTC ISO8601 时间

### 3. `messages` 表
- `id`: TEXT 主键，服务端消息 UUID
- `client_temp_id`: TEXT 唯一键，可为空，前端乐观发送生成的临时标识，用于去重与回执原地替换
- `bot_id`: TEXT 非空，所属 `bots.id`
- `sender_type`: TEXT 非空，仅允许 `'user'` 或 `'bot'`
- `content`: TEXT 可为空，消息文本正文
- `attachments_json`: TEXT 可为空，附件元数据数组 JSON，每项包含 `path`、`url`、`mime`、`width`、`height`、`name`、`size`
- `reply_to_msg_id`: TEXT 可为空，长按引用回复指向的目标消息 `id`
- `model_used`: TEXT 可为空，生成该条回复实际采用的大模型标识
- `seq`: INTEGER 非空，严格单调递增序号，用于多条短气泡保序与断线重连增量补拉
- `created_at`: DATETIME 非空，UTC ISO8601 时间
- 联合索引：`idx_messages_bot_seq` 建立在 `bot_id` 与 `seq` 升序字段上

### 4. `event_inbox` 表
- `id`: TEXT 主键，事件 UUID
- `target_bot_id`: TEXT 非空，到点需要唤醒的目标 `bots.id`
- `prompt`: TEXT 非空，到点后投递给目标 Bot 的执行指令
- `schedule_type`: TEXT 非空，仅允许 `'once'` 单次任务或 `'cron'` 周期任务
- `cron_expr`: TEXT 可为空，仅周期任务填写标准 5 段式 Cron 表达式
- `user_timezone`: TEXT 非空，创建任务时锁定的用户 IANA 时区
- `next_run_at_utc`: DATETIME 非空，换算后的精确 UTC 触发时间
- `status`: TEXT 非空，仅允许 `'pending'`、`'processing'`、`'done'`、`'cancelled'`
- `claimed_at_utc`: DATETIME 可为空，被轮询网关抢占的时间戳，用于超时恢复
- `created_at`: DATETIME 非空
- `updated_at`: DATETIME 非空
- 联合索引：`idx_event_inbox_due` 建立在 `status` 与 `next_run_at_utc` 上；`idx_event_inbox_bot` 建立在 `target_bot_id` 与 `status` 上

### 5. `shared_memories` 表
- `id`: TEXT 主键，记忆 UUID
- `memory_key`: TEXT 非空且全局唯一，语义化记忆键名，如 `'university'`、`'diet_restriction'`，新写入同键事实自动覆盖旧矛盾值
- `value`: TEXT 非空，单条事实内容，数据库层硬性限制长度不超过 120 个字符
- `updated_by`: TEXT 非空，最后更新该条记忆的 `bot_id`
- `updated_at`: DATETIME 非空

### 6. `device_push_tokens` 与 `push_records` 表
- `device_push_tokens` 表：
  - `device_id`: TEXT 主键
  - `expo_push_token`: TEXT 非空
  - `platform`: TEXT 非空，取值为 `'ios'`、`'android'` 或 `'web'`
  - `updated_at`: DATETIME 非空
- `push_records` 表：
  - `id`: TEXT 主键
  - `bot_id`: TEXT 非空
  - `bot_name`: TEXT 非空，推送通知标题使用的 Bot 名称
  - `message_ids_json`: TEXT 非空，本条通知关联的消息 `id` 列表 JSON
  - `preview_text`: TEXT 非空，通知摘要正文
  - `status`: TEXT 非空，取值为 `'queued'` 休息时段积压待推、`'sent'` 已推送、`'skipped_online'` 用户已上线免推、`'failed'` 推送失败
  - `created_at`: DATETIME 非空
  - `sent_at`: DATETIME 可为空，实际发出或结算的 UTC 时间
  - 索引：`idx_push_records_status` 建立在 `status` 与 `created_at` 上

---

## 二、手机端本地存储结构

全部手机端存储由模块 `14` 在 `mobile/features/local_cache` 中统一维护。

### 1. 本地 SQLite 库
- `local_bots` 表：镜像服务端 `bots` 字段，额外维护 `last_message_preview`、`last_message_at`、`unread_count` 与 `last_synced_seq`
- `local_messages` 表：镜像服务端 `messages` 字段，额外维护发送状态 `local_status` 取值 `'sending'`、`'sent'` 或 `'failed'`，以及已下载到本地沙盒的附件路径映射 `local_attachment_uris_json`

### 2. 本地高速键值库 MMKV
- `theme_mode`: 取值为 `'system'`、`'light'` 或 `'dark'`，由模块 `13` 同步读写
- `draft:{botId}`: 对应各 Bot 聊天输入框尚未发出的文本草稿
- `server_endpoint`: 后端 HTTP 与 WebSocket 服务根地址
- `last_active_bot_id`: 上次打开的会话 `bot_id`，默认值为 `'supervisor'`
