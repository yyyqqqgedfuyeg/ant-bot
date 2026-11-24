# 服务端数据库底座与黑盒架构门禁

- **模块根目录**：`backend/shared/db/` 与 `scripts/lint_arch.py`
- **唯一对外出口**：`backend/shared/db/__init__.py`，显式声明 `__all__`，导出数据库初始化、异步连接获取与短事务上下文管理器
- **调用的前置模块契约**：无
- **底层设施依赖**：SQLite，表结构遵循 `01-DATA-CONTRACT.md`

## Sub-features
- **SQLite 高并发防锁配置**：连接建立时强制开启 `WAL` 模式，设置 `synchronous=NORMAL` 与 `busy_timeout=5000`，并提供短事务写操作封装。
- **全量服务端表初始化**：幂等创建 `bots`、`user_settings`、`messages`、`event_inbox`、`shared_memories`、`device_push_tokens`、`push_records` 共 7 张表及对应索引；初始化 `user_settings` 默认单行配置，包含默认时区、全局模型及休息时间免打扰字段。
- **黑盒架构扫描脚本 `scripts/lint_arch.py`**：通过 AST 扫描整个 `backend/` 目录，拦截任何跨模块导入 `.internal` 路径的行为，并强制校验 `backend/features/*/__init__.py` 与 `backend/tools/features/*/__init__.py` 均显式声明 `__all__`。

## How to trigger / reach it
- 编写单元测试 `tests/shared/test_db_and_arch.py`：
  1. 初始化测试数据库，断言 7 张表及 `user_settings` 默认记录创建成功、`WAL` 模式已生效、且 `shared_memories.value` 超过 120 字符时触发数据库约束异常；
  2. 并发启动多个协程写入测试数据，断言全程无锁库报错；
  3. 构造违规跨模块引用 `internal` 的代码样例运行检查函数，断言脚本准确拦截并返回非零退出码。

## Driving it
- 运行数据库与架构门禁单测：`pytest tests/shared/test_db_and_arch.py -v`
- 运行全局架构扫描：`python scripts/lint_arch.py`

## Gotchas
- **严禁长事务占锁**：事务块内部只能执行纯 SQL 读写并立即提交，禁止在事务内等待大模型响应或发起外部网络请求。
