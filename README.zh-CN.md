# PulseDeck

> 0.2 当前策略：Codex/Claude 仅读取本地文件和已有额度快照；停用 app-server、内部接口、Admin API 和客户端登录检查。Isambard/Radar 公共数据仍正常更新。云端适配代码仅保留供以后开发，当前不会执行。

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

## 第一版的范围

Codex 仅展示本地使用历史、模型和会话统计，当前关闭所有账号网络查询。
Claude 的本地使用历史可以直接读取；5 小时/7 天额度需要兼容客户端产生 statusLine 快照。
Claude Desktop 可能只更新本地历史，所以不能把没有快照误认为还有 100% 额度。
Isambard 显示公共状态和维护计划，个人作业留待后续接入。
Radar 显示社区降智评测分数和原始测试时间，更新失败会保留旧数据并提示。

程序只显示用量元数据；本地 token 统计不等于账单，也不代表其他电脑上的全部用量。

缓存、运行状态和日志保存在 `%LOCALAPPDATA%\PulseDeck`，不会同步到 GitHub。
桌面版在独立窗口中复用现有界面，使用系统的 Microsoft Edge WebView2 Runtime。
源码构建可运行 Build-Desktop.ps1，结果位于 dist/PulseDeck.exe；详见 [桌面版说明](docs/desktop.md)。

详见 [完整说明](README.md) 和 [开发说明](docs/pulsedeck.md)。
