# 跨 Bot 全局共享短记忆工具

- **模块根目录**：`backend/tools/features/shared_memory/`
- **唯一对外出口**：`backend/tools/features/shared_memory/__init__.py`，显式声明 `__all__`，导出全局记忆查询函数与挂载至 Bot 的记忆读写工具
- **调用的前置模块契约**：`backend/features/bot/__init__.py`，仅在验证脚本中用于挂载工具实测
- **底层设施依赖**：`backend/shared/db/__init__.py`，读写 `shared_memories` 表

## Sub-features
- **工具描述与静默写入准则**：工具 `description` 明确用于读取与记录用户的长期稳定属性、背景与偏好，例如所在城市、专业、饮食忌口、沟通习惯；写入成功后静默完成，不要向用户刻意播报已记住；严禁将带触发时间的待办提醒存入本表。
- **全局同键覆盖消歧**：以语义化 `memory_key` 作为唯一键；当任意 Bot 写入同键新事实时，直接覆盖旧记录并更新 `updated_by` 与 `updated_at`，确保全系统不会残留前后矛盾的旧记忆。
- **120 字符硬上限与并发安全**：单条记忆 `value` 硬性限制在 120 字符以内，底层通过短事务保障多 Bot 并发读写安全。

## How to trigger / reach it
- **确定性数据边界单测**：编写 `tests/tools/test_shared_memory.py`，验证超过 120 字符时工具返回明确错误提示、同 `memory_key` 新值覆盖旧值、以及 8 个协程并发写入零报错。
- **Bot 自主记忆效果观察**：编写脚本 `scripts/verify_03_shared_memory.py`：
  1. 实例化 Bot A 并挂载共享记忆工具，向其输入“我是长沙读计算机的大学生，平时不吃香菜”；
  2. 新开无历史上下文的 Bot B 挂载同一记忆工具，询问“你知道我在哪读书、有什么饮食忌口吗”，打印数据库记录与 Bot B 回复，核对输出语义是否准确。

## Driving it
- 运行数据边界与并发单测：`pytest tests/tools/test_shared_memory.py -v`
- 运行跨会话共享记忆观察脚本：`python scripts/verify_03_shared_memory.py`
- 运行架构门禁检查：`python scripts/lint_arch.py`

## Gotchas
- **超长必须打回重写**：当模型传入超过 120 字符的 `value` 时，工具必须返回错误提示要求模型自行浓缩后再调用，严禁服务端直接截断文本导致语义丢失。
