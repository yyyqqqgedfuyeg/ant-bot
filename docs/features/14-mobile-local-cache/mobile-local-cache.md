# 手机端离线本地缓存底座

- **模块根目录**：`mobile/features/local_cache/`
- **唯一对外出口**：`mobile/features/local_cache/index.ts`，导出 `initLocalCache`、`useLocalBots`、`useLocalMessages`、`upsertBots`、`removeLocalBot`、`insertOptimisticMessage`、`replaceOptimisticMessage`、`markMessageFailed`、`upsertMessages`、`clearUnreadCount`、`saveDraft`、`getDraft`、`getServerEndpoint`、`setServerEndpoint`、`getLastActiveBotId`、`setLastActiveBotId`、`getCacheStats`、`clearAttachmentCache`
- **调用的前置模块契约**：无
- **底层设施依赖**：`expo-sqlite`、`react-native-mmkv`、`expo-file-system`，存储结构遵循 `01-DATA-CONTRACT.md`

## Sub-features
- **本地优先存储镜像**：基于本地 SQLite 维护 `local_bots` 与 `local_messages` 两张表，应用冷启动与切换会话时直接从本地库毫秒级读取列表、头像配置与历史气泡，无需等待网络返回。
- **乐观消息原地替换去重**：用户点击发送时先调用 `insertOptimisticMessage` 生成带 `client_temp_id` 且状态为 `'sending'` 的本地消息立即上屏；收到服务端确认帧后调用 `replaceOptimisticMessage` 原地写入正式 `id`、`seq` 并将状态改为 `'sent'`，避免画面出现重复气泡。
- **草稿、配置与附件缓存管理**：使用 MMKV 实时持久化各会话输入框未发出的文本草稿 `draft:{botId}`、服务器地址与上次活跃的 `bot_id`；支持统计本地已下载附件占用的磁盘空间并提供一键清理附件文件功能，清理后保留全部文字记录。

## How to trigger / reach it
- 编写单元测试 `mobile/features/local_cache/__tests__/local_cache.test.ts`：
  1. 验证多次调用 `upsertMessages` 写入相同 `id` 消息时的幂等去重表现，确认对应 Bot 的最新摘要与 `last_synced_seq` 自动推进；
  2. 验证插入 `'sending'` 乐观消息后再执行 `replaceOptimisticMessage`，断言记录总数保持为 1 且状态变为 `'sent'`；
  3. 验证不同 `botId` 草稿读写互不串扰，以及执行 `clearAttachmentCache` 后附件占用体积归零。

## Driving it
- 运行本地缓存与去重单测：`npx jest mobile/features/local_cache/__tests__/local_cache.test.ts`
- 运行全局静态检查：`npm run lint && npx tsc --noEmit`

## Gotchas
- **列表稳定排序**：已有正式 `seq` 的消息严格按 `seq` 升序排列，尚未拿到 `seq` 的本地 `'sending'` 或 `'failed'` 消息按本地发送时间排在末尾，防止收到回执瞬间气泡位置跳变。
