# PulseDeck

> 0.4.6 当前策略：Token 历史和额度窗口继续仅读取本地；仅 Reset Credits 通过已登录的 Codex 客户端做只读账户查询，每 5 分钟最多一次，不消耗重置券。其他账户统计、Admin API 和旧内部 HTTP 接口仍停用，Isambard/Radar 公共数据正常更新。

集中查看 Codex、Claude Code 用量、Isambard 服务状态和 Radar 模型评测的本地面板。

## Windows 使用

- 双击 **PulseDeck.exe**：直接打开独立窗口，不需要终端或另开浏览器，也不需要单独安装 Python。
- 再次双击会回到已有窗口；关闭窗口时停止桌面版自己的采集。
- **Start-PulseDeck.cmd** 优先打开项目中的 EXE；没有 EXE 时使用原来的浏览器入口。
- **Stop-PulseDeck.cmd** 可关闭桌面版，或停止浏览器版后台。
- 双击 **Check-PulseDeck.cmd**：检查数据目录和运行环境。
- 双击 **Setup-Claude-Capture.cmd**：安装 Claude Code 额度采集桥接；已有自定义 statusLine 时会保留，不会覆盖。

从源码使用浏览器入口需要 Python 3.10+。启动器支持已安装的 Python，也支持这台电脑上 Codex 自带的 Python。
也可通过 `PULSEDECK_PYTHON` 指定解释器。不需要安装 pip 包或 Node.js。

## 用量统计

- 今天／近 7 天／近 30 天／全部历史：总量、模型、项目、会话和趋势使用同一范围，按本地时区计算。
- Codex 合并逐请求用量与累计快照，按当时的模型归属；Claude 合并流式重复消息。
- 日期未知的历史量会明确提示，不会被算进今天；模型排行的占比以所选范围总量为分母。
- 未变化的日志不重复读正文，新增日志只读追加部分；索引只保存在内存中。
- 首页直接显示 5 小时／7 天剩余额度、重置倒计时和两张用量概览；详细记录与 Radar 按需展开。
- 额度仅读取 Codex 日志和 Claude 本地快照，倒计时每秒更新；缺失或过期的数据会明确标注。

Reset Credits 位于 Codex 额度卡片内，显示服务端可用次数和到期明细；主刷新按钮不会绕过五分钟缓存。若要关闭该项联网，启动前设置 `PULSEDECK_RESET_CREDITS_ONLINE=0`。

统计边界见 [本地统计说明](docs/local-usage.md)。

## 数据范围

Codex 仅展示本地使用历史、模型和会话统计，仅 Reset Credits 允许只读账户查询。
Claude 的本地使用历史可以直接读取；5 小时/7 天额度需要兼容客户端产生 statusLine 快照。
Claude Desktop 可能只更新本地历史，所以不能把没有快照误认为还有 100% 额度。
Isambard 显示公共状态和维护计划，个人作业留待后续接入。
Radar 显示社区降智评测分数和原始测试时间，更新失败会保留旧数据并提示。

程序只显示用量元数据；本地 token 统计不等于账单，也不代表其他电脑上的全部用量。

缓存、运行状态和日志保存在 `%LOCALAPPDATA%\PulseDeck`，不会同步到 GitHub。
桌面版在独立窗口中复用现有界面，使用系统的 Microsoft Edge WebView2 Runtime。
源码构建可运行 Build-Desktop.ps1，结果位于 dist/PulseDeck.exe；详见 [桌面版说明](docs/desktop.md)。

详见 [完整说明](README.md) 和 [开发说明](docs/pulsedeck.md)。
