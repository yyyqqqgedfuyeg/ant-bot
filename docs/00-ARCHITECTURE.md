# 系统架构边界与黑盒铁律

## 1. 核心术语与职责边界
- **统一实体概念**：系统内所有独立智能体均称为 Bot，包含系统预置不可删除的总管 `supervisor` 与用户自行创建的自定义 Bot。每个 Bot 对应一个独立的 Antigravity 会话。
- **工具挂载统一**：所有预置与新建 Bot 均保留底层 SDK 内置工具，并统一挂载 `backend/tools/features/` 下的四大业务工具。严禁使用预设脚本伪造回复，所有发往用户的消息均必须由 Bot 真实调用工具产生。
- **原生托管边界**：Bot 思维链、工具执行过程日志、上下文历史与自动压缩均由 `google-antigravity` SDK 原生负责，业务数据库严禁重复建表。

## 2. 双端黑盒目录规范

### Python 后端业务服务目录
```text
backend/features/{domain}/
├── __init__.py          # 唯一对外公开契约口，控制在 50 行内，必须显式声明 __all__
└── internal/            # 黑盒内部实现，跨模块严禁导入，严禁其他会话读取
```

### Python 后端挂载至 Bot 的工具目录
```text
backend/tools/features/{tool_name}/
├── __init__.py          # 唯一对外公开契约口，控制在 50 行内，必须显式声明 __all__
└── internal/            # 工具内部数据读写与逻辑实现，跨模块严禁导入与读取
```

### Expo 前端模块与共享目录
```text
mobile/features/{domain}/   以及 mobile/shared/{domain}/
├── index.ts             # 唯一对外公开契约口，控制在 50 行内，仅导出公共组件、Hooks 与类型
└── internal/            # 黑盒私有子组件、动画逻辑与内部状态，跨模块严禁导入与读取
```

`mobile/app/` 目录仅存放 Expo Router 页面路由文件，负责组合 `mobile/shared/*/index.ts` 与 `mobile/features/*/index.ts` 公开能力，不编写底层数据与网络逻辑。

## 3. 新开 AI 会话只读白名单铁律
1. 开发当前模块时，仅允许读写当前模块所属目录及对应的测试与验证脚本文件。
2. 需要调用前置模块时，仅允许读取前置模块公开的 `__init__.py` 或 `index.ts`。
3. 严禁打开、全文检索或扫描任何非当前模块的 `internal/` 目录。
4. 若目标文档头部「调用的前置模块契约」写明为 `无`，代表该模块是无前置依赖的叶子节点，严禁读取其他任何业务与工具模块。

## 4. 机器强制门禁
- **Python 架构检查脚本 `scripts/lint_arch.py`**：
  - 由模块 `01` 创建，静态扫描整个 `backend/` 目录；
  - 拦截任何跨模块导入 `backend.features.*.internal.*`、`backend.tools.features.*.internal.*` 或 `backend.shared.*.internal.*` 的行为；
  - 校验 `backend/features/*/__init__.py` 与 `backend/tools/features/*/__init__.py` 均显式声明 `__all__`；
  - 违规时输出明确报错：`[ARCH][ERROR] 禁止跨模块导入 internal，请改从对应模块的 __init__.py 导入公开契约。`
- **Expo ESLint 门禁**：
  - 由模块 `13` 配置，拦截任何跨模块引用 `**/internal/**` 路径；
  - 拦截除 `mobile/shared/theme/internal/tokens.ts` 以外所有前端文件中的硬编码颜色字面量，违规时报错：`[THEME][ERROR] 禁止硬编码色值，请从 mobile/shared/theme 导入语义化 Theme Token。`
  - 拦截普通 `FlatList` 导入，强制统一使用 `@shopify/flash-list`。

## 5. 共享基础层出口
- `backend/shared/db/__init__.py`：SQLite WAL 连接管理、服务端表结构初始化与短事务封装，由模块 `01` 实现。
- `mobile/shared/theme/index.ts`：深浅色语义化色板、`ThemeProvider` 与 `useTheme`，由模块 `13` 实现。
- `mobile/shared/ui/index.ts`：自动适配深浅色与触感反馈的公共基础 UI 原语，由模块 `13` 实现。
