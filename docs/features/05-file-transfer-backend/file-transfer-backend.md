# 无隔离共享文件传输后端服务

- **模块根目录**：`backend/features/file_transfer/`
- **唯一对外出口**：`backend/features/file_transfer/__init__.py`，显式声明 `__all__`，导出 FastAPI 路由 `file_router`、供 Bot 登记产出文件的 `register_local_file`、以及附件元数据模型 `AttachmentMeta`
- **调用的前置模块契约**：无
- **底层设施依赖**：服务端统一共享目录 `/workspace/shared_files/`，支持通过环境变量或测试参数指定路径

## Sub-features
- **多文件上传与跨 Bot 共享**：提供 HTTP 多文件上传接口并拒绝上传文件夹，所有文件统一写入共享目录而不按 Bot 隔离；用户传给某一个 Bot 的文件或任意 Bot 生成的文件，其他 Bot 均可直接凭本地 `path` 读取。
- **图片宽高自动解析**：上传或登记图片时自动解析真实像素 `width` 与 `height`，连同 `path`、下载 `url`、`mime`、`name`、`size` 一并返回，供后续前端消息气泡提前撑开尺寸。
- **安全下载与预览**：提供按文件标识读取共享目录文件的 HTTP 接口，严格拦截包含 `../` 的越权路径访问。

## How to trigger / reach it
- 编写后端接口单测 `tests/features/test_file_transfer.py`：
  1. 通过 HTTP 客户端同时上传一张测试 PNG 图片与一份文本文件，断言落盘成功且准确返回图片的真实宽高数值；
  2. 直接在服务端读取返回的本地 `path` 验证跨会话直读可用，并请求下载 `url` 断言响应字节流一致；
  3. 发起包含路径穿越符号的非法下载请求，断言接口返回拒绝状态码。

## Driving it
- 运行文件上传下载与尺寸解析单测：`pytest tests/features/test_file_transfer.py -v`
- 运行架构门禁检查：`python scripts/lint_arch.py`

## Gotchas
- **磁盘文件名防覆盖**：同名文件重复上传时需在落盘文件名中加入唯一前缀或标识，同时在元数据 `name` 字段保留原始文件名用于展示。
