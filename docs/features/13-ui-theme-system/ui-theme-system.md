# 前端深浅色主题色板、基础 UI 原语与样式门禁

- **模块根目录**：`mobile/shared/theme/`、`mobile/shared/ui/` 与前端 ESLint 配置
- **唯一对外出口**：
  - `mobile/shared/theme/index.ts`，导出 `ThemeProvider`、`useTheme`、`ThemeTokens`、`ThemeMode` 与 `getElevationShadow`（模式感知阴影辅助）
  - `mobile/shared/ui/index.ts`，导出 `ThemedView`、`ThemedText`、`PressableScale`、`GlassHeader` 与 `SheetModal`
- **调用的前置模块契约**：无，本模块先完成全站语义 Token 映射与基础原语建设，不单独编写临时业务页，实际业务界面统一在模块 `17`–`20` 组装
- **底层设施依赖**：`react-native-mmkv`、`expo-blur`、`expo-haptics`、`react-native-reanimated`、`lucide-react-native`

## 核心架构与选色原则
- **单一真相源（SSOT）**：所有真实色值唯一收敛于 `mobile/shared/theme/internal/tokens.ts`，业务界面与公共原语严禁出现任何字面量色值（Hex / `rgb` / `rgba` / `hsl` / 命名色）与非语义颜色引用。
- **不可变双主题静态注册**：在应用根部一次性静态注册 `light` 与 `dark` 两套结构完全对称的不可变 Token 表，主题切换仅变更当前模式标识与上下文引用；**禁止**运行时重建全局配置，也**禁止**导出或修改全局可变 `colors` 单例。
- **静态声明与动态订阅分离**：样式层组件（`ThemedView`、`ThemedText`、`GlassHeader` 等）通过语义键自动响应主题变化；非样式属性（如 `lucide-react-native` 图标 `color`、`placeholderTextColor`、`StatusBar`、`expo-blur` 的 `tint`、`ActivityIndicator`）统一通过 `useTheme()` 响应式订阅消费。
- **三态模式与系统外观实时联动**：同时支持 `'light'`、`'dark'` 与 `'system'` 三种模式，并监听系统外观变化（`Appearance` / `useColorScheme`）在 `'system'` 模式下实时刷新，无需重启或重载页面。
- **五项深浅色选色原则**：
  1. **明度梯度原则**：深色模式由低明度画布逐级抬升表面明度（画布 → 侧边栏/标准容器 → 抬升容器）；浅色模式通过极低饱和度的微明度差区分画布、基础表面与抬升表面，避免卡片与输入框和画布融为一体；
  2. **饱和度克制原则**：深色模式适度降低品牌色与状态色饱和度并提亮以减少暗底眩光；浅色模式适当压低明度并增强对比度，保证清晰可读；
  3. **中性边界原则**：分割线与容器边框在双模式下均采用低饱和度中性灰与柔和对比度，起到结构分隔作用而不抢占视觉焦点；
  4. **对比度达标原则**：所有正文与交互标签满足无障碍可读对比度标准（WCAG AA），次级说明与禁用态在降低视觉权重的同时保持清晰可辨；
  5. **阴影降权原则**：深色模式可采用较高不透明度阴影表达层级，浅色模式显著降低阴影不透明度并搭配柔和扩散边缘。

## Sub-features
- **六层对称语义化 Token 体系**：在 `mobile/shared/theme/internal/tokens.ts` 中完整定义 `light` 与 `dark` 两套同名语义 Token：
  1. **画布与表面层 (`bg`)**：`bg.canvas`（主聊天画布）、`bg.surface`（标准容器/卡片）、`bg.sidebar`（侧边栏底色）、`bg.elevated`（输入框、抬升卡片与弹出菜单）、`bg.code`（代码块与等宽内容表面）、`bg.pressed`（按压态表面）、`bg.glass`（顶部与底栏毛玻璃叠色）；
  2. **边框与分割线层 (`border`)**：`border.subtle`（弱分割线）、`border.strong`（强轮廓线与输入容器边框）、`border.focus`（聚焦高亮边框）；
  3. **自适应文本层 (`text`)**：`text.primary`（标题与正文）、`text.secondary`（次级说明）、`text.muted`（弱化提示、占位符与禁用态文字）、`text.link`（链接文本）、`text.inverse`（反色文本）；
  4. **恒定前景层 (`bubble` / `status.on*`)**：为实底气泡与品牌/状态实底上的文字及图标设立独立恒定前景 Token，包括 `bubble.self.bg` / `bubble.self.text`（用户右侧实底气泡与恒定浅色字）、`bubble.peer.bg` / `bubble.peer.text`（Bot 左侧表面气泡与自适应字），以及 `status.onAccent`、`status.onWorking`、`status.onWarning`、`status.onDanger`，**严禁**复用自适应 `text.primary` 或 `text.inverse` 替代实底前景；
  5. **品牌与状态层 (`status`)**：按「填充色 + 恒定前景色 + 柔和底色 + 边框色」成组定义主高亮（`accent` / `onAccent` / `accentSoft` / `accentBorder`）、工作中/成功（`working` / `onWorking` / `workingSoft` / `workingBorder`）、警告（`warning` / `onWarning` / `warningSoft` / `warningBorder`）与危险警示（`danger` / `onDanger` / `dangerSoft` / `dangerBorder`）；
  6. **浮层与阴影层 (`bg.overlay` / `shadow`)**：独立定义抽屉与弹窗半透明遮罩 `bg.overlay` 以及阴影基色 `shadow.color`（配合 `getElevationShadow(mode, level)` 输出模式感知阴影参数），禁止复用画布色或文本色替代。
- **冷启动零闪烁主题初始化与切换**：`ThemeProvider` 启动时从 MMKV 同步读取 `theme_mode`，首帧即同步渲染目标色板、根画布底色与系统状态栏样式（Web 端同步根节点主题标识与 `colorScheme`），切换 `'system'` / `'light'` / `'dark'` 时全程无白屏或旧色闪烁。
- **五大公共基础 UI 原语与全元素覆盖**：在 `mobile/shared/ui/` 中封装 `ThemedView`、`ThemedText`、带按压缩放与触感反馈的 `PressableScale`、自适应毛玻璃导航栏 `GlassHeader` 以及支持手势下滑收起的底部弹窗 `SheetModal`，并满足以下全元素覆盖约束：
  - **图标全覆盖**：所有 `lucide-react-native` 图标（导航、操作按钮、表单前后缀、状态图标及图标底托）统一绑定语义 Token，明确区分普通态、激活态与禁用态；
  - **全形态文字覆盖**：页面标题、区块标题、正文、辅助说明、输入框占位符、链接、行内代码、代码块语法、徽章与聊天气泡文字均纳入主题体系；
  - **全组件五态覆盖**：按钮、标签、徽章、输入框、选择器、开关、列表项、分割线、提示条、弹出菜单与模态框均成对定义普通态、悬停态（Web）、按压态、选中态与禁用态。
- **ESLint 样式与黑盒门禁**：接入静态检查与 CI 流水线，拦截除 `tokens.ts` 外所有前端文件中的字面量颜色（Hex、`rgb()`、`rgba()`、`hsl()`、命名色）及非语义颜色引用并输出 `[THEME][ERROR]`，同时拦截跨模块导入 `**/internal/**` 以及普通 `FlatList` 组件导入。

## How to trigger / reach it
- 编写单元测试 `mobile/shared/__tests__/theme_and_lint.test.ts`：
  1. 递归校验 `light` 与 `dark` 两套 `ThemeTokens` 键结构完全对称无遗漏，验证所有实底前景与正文对比度及阴影降权参数符合双模式规范，并测试切换 `'system'` / `'light'` / `'dark'` 时 MMKV 同步持久化与系统外观变更实时响应；
  2. 将包含硬编码 `#FFFFFF` / `rgba(0,0,0,0.5)` / 命名色 `'white'`、跨模块 `internal` 导入及 `FlatList` 导入的测试代码片段送入 ESLint 校验，断言全部门禁规则均准确报错拦截。
- **双向实时切换验收**（集成至模块 `20` 后执行）：在不刷新/不重启应用的前提下，于设置页反复切换「深色 ↔ 浅色 ↔ 跟随系统」，逐项核验全站图标、全形态文字（含占位符与代码块）、组件交互五态、分割线层级、卡片阴影与弹窗遮罩是否即时同步且无残留旧色。

## Driving it
- 运行主题与门禁单测：`npx jest mobile/shared/__tests__/theme_and_lint.test.ts`
- 运行全局静态检查：`npm run lint && npx tsc --noEmit`

## Gotchas
- **阴影与半透明遮罩禁止写死**：弹窗遮罩或卡片阴影严禁直接书写 `rgba` 或 `#000` 字面量，必须统一消费 `bg.overlay`、`shadow.color` 与 `getElevationShadow`。
- **实底按钮与右侧气泡禁止复用自适应主文字色**：实底填充（如 `bubble.self.bg`、`status.accent`、`status.danger`）上的文字与图标必须使用独立恒定前景 Token（如 `bubble.self.text`、`status.onAccent`），防止浅/深切换时前景与底色同化不可见。
- **严禁导出可变全局颜色单例**：禁止在模块顶层缓存 `export let colors = ...` 并在切换主题时原地修改字段，否则组件重渲染前会出现样式错乱或局部不刷新。
- **浅色模式禁止画布与卡片同纯白无层级**：浅色下 `bg.canvas`、`bg.surface` 与 `bg.elevated` 须保持极低饱和度的微明度差并搭配中性 `border.subtle`，避免界面边界糊成一片。
