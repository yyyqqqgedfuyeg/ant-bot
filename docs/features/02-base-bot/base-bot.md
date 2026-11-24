# 基础 Antigravity Bot 引擎封装

- **模块根目录**：`backend/features/bot/`
- **唯一对外出口**：`backend/features/bot/__init__.py`，显式声明 `__all__`，导出 `AntigravityBot` 类及状态回调与工具类型定义
- **调用的前置模块契约**：无
- **底层设施依赖**：Python `google-antigravity` SDK

## Sub-features
- **标准化引擎与内置能力保留**：封装 `AntigravityBot` 类，默认使用 `model="gemini-4-Hydrogen"`、`thinking_level="low"`、`approval_mode="turbo"`，完整保留 `read`、`write`、`bash` 等内置工具，并提供动态修改模型与运行参数的方法。
- **自定义工具注册**：支持实例化时批量挂载工具列表，同时提供 `register_tool` 方法挂载 `backend/tools/features/` 下的扩展工具。
- **多会话隔离与自动压缩**：支持创建、查找与重命名多个相互隔离的会话，各会话独立维护上下文历史，达到阈值时自动触发原生上下文压缩。
- **运行中即时消息送达**：当某个会话正在执行耗时任务处于 `working` 状态时，用户新发来的消息支持立即送入该活跃会话实时感知与响应，严禁采用串行队列把用户新消息堵在门外等上一轮干完才投递。
- **忙闲状态回调透出**：支持绑定状态监听函数，会话开始推理或调用工具时回调 `working`，当前执行完全结束时回调 `idle`。

## How to trigger / reach it
- 编写观察验证脚本 `scripts/verify_02_base_bot.py`：
  1. 实例化 `AntigravityBot` 并挂载一个返回随机口令的对暗号工具，绑定状态打印回调；
  2. 开启会话 A，首轮提问触发暗号工具，次轮追问刚才做过什么，控制台打印两轮回复与 `working` 到 `idle` 的状态变化；
  3. 让会话 A 执行一项耗时数秒的操作，执行中途立即追加发送一条新指令，观察 Bot 能否在运行过程中及时接收并回应新消息而非傻等队列；
  4. 开启隔离会话 B 验证无法读取会话 A 的历史，并测试会话重命名与动态切换模型参数。

## Driving it
- 运行多会话与即时插话观察脚本：`python scripts/verify_02_base_bot.py`
- 运行架构门禁检查：`python scripts/lint_arch.py`

## Gotchas
- **工具挂载时机**：所有自定义工具应在会话正式接收消息前挂载完毕，避免运行中途修改工具列表造成多会话状态异常。
