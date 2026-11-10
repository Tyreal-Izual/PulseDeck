# Dashboard configuration and API / 仪表盘配置与 API

[English quick start](README.md) · [中文快速开始](README.zh-CN.md)

## Startup options / 启动参数

```sh
python3 codex_claude_usage_web.py --help
python3 codex_claude_usage_web.py --sources all --refresh 30 --quiet
python3 codex_claude_usage_web.py --sources claude --default-report claude-usage
python3 codex_claude_usage_web.py --cache-dir .local/cache --check
```

| Option | Meaning / 作用 |
| --- | --- |
| `--sources auto` | Default: detect local Codex/Claude and enable Isambard/Radar; 默认检测本地来源并勾选两项公共来源 |
| `--sources all` | Enable Codex, Claude, Isambard and Radar; 恢复完整总览 |
| `--sources codex,radar` | Enable only the listed sources; 只启用列出的来源 |
| `--default-report` | `all`, `codex-usage`, `claude-usage`, `isambard-status` |
| `--check` | Read-only JSON setup diagnostics, then exit; 只读配置检查 |
| `--cache-dir` | Public-source disk cache directory; 公共来源缓存目录 |
| `--port 8766` | Change the default port 8765; 修改端口 |
| `--refresh 30` | Browser interval (default 15 seconds), local configuration only; 仅本地配置 |
| `--days 60` | Legacy request setting; dashboard local history now uses the Time range selector |
| `--quiet` | Disable per-request access logs; 关闭访问日志 |
| `--max-workers` | Simultaneous HTTP requests, default 4 |
| `--max-collectors` | Simultaneous report collections, default 2 |
| `--cache-seconds` | Whole-report reuse window, default 5 seconds; per-source caches remain independent |

The page URL can override the default view with `?report=claude-usage` after
opening the authenticated startup URL. Disabled sources return `disabled: true` and never run collectors.
Account token-history/profile and Admin API reports remain disabled. Reset Credits alone have a read-only Codex-client exception.
The interface starts in English unless a valid saved language preference exists.
Choose Simplified Chinese from Language on either the dashboard or maintenance
page. Language and time range are stored locally for the current origin; a
different fallback port starts with that origin's saved settings or the defaults.
Source detection runs on server startup; restart after installing a new client.

界面默认英文，可在首页或维护页的 Language 菜单选择简体中文。语言和时间范围保存在
当前本地地址下；端口变化时，会使用新地址已有的设置或默认值。

首次认证后可用 `?report=claude-usage` 指定视图。关闭的来源不会执行采集。
默认自动检测的结果在重启服务时更新；安装或登录新客户端后请重启。

Toolbar: Report (Overview by default), Time range, Language, Isambard Status, Codex Radar, Auto Refresh and Refresh.
The two public sources are checked by default. Switching one off hides its panel and stops new
collection work; Radar's background worker pauses. An already-running fetch may finish.
The switches are shared by this server's tabs, synchronized on refresh, and reset to the startup
selection when the server restarts. Explicit `--sources` selections determine initial checkboxes.

Reset Credits has its own panel immediately above Radar. Radar scores are shown
without expanding a section.

工具栏支持统一时间筛选，默认近 30 天。Reset Credits 独立放在 Radar 上方；Radar 评分直接显示。关闭来源不会删除缓存。

Radar displays only **homepage degradation score cards**, grouped by model. Each
card shows a two-decimal score and a thin bar scaled to **score / 150**. History
charts, model/metric selectors, costs and duration are omitted. Missing scores
are shown as `—`, distinct from `0.00`. Only snapshots from the current degradation assessment can be fallback; older RadarBench scores are excluded.

Radar 仅展示官网当前**降智雷达总分卡片**：按模型分行，分数保留两位小数，细条按分数 ÷ 150
显示。移除历史曲线、模型/指标选择器和费用耗时。缺失分数以 `—` 表示，与 `0.00` 区分。
只使用有效新版快照回退；更新代码后需重启网页服务。

## Refresh behavior / 刷新行为

The browser requests at most two sections concurrently and displays each result
as it arrives. An unavailable source leaves the other sections usable. Existing
results remain visible during refresh. Switching the report or source selection never
renders a late response for the old selection.

| Source | Reuse / 更新策略 |
| --- | --- |
| Codex local | 5-second source cache; unchanged files read no content, appends read only the suffix |
| Reset Credits | Read-only Codex client lookup, cached 5 minutes; no redemption |
| Codex online/profile | Disabled |
| Claude | 5-second source cache; same incremental metadata index |
| Optional Admin API | Disabled: local-only policy |
| Isambard | 30-second source cache over a 5-minute disk cache |
| Radar | Independent 4-hour worker; one homepage request, up to 3 attempts for transient errors |

Manual Refresh bypasses only the Isambard cache, at most once per 30 seconds.
It does not bypass the Reset Credits cache, refresh Radar upstream, or create a
Claude quota snapshot. The selected range filters all local token breakdowns
by local calendar date, including today. Unknown dates are included only in
All local history and are disclosed separately. See [accounting details](docs/local-usage.md).

网页同时最多加载两个区块，逐块显示结果。刷新间隔控制读取频率，各来源仍使用自己的缓存。
手动刷新仅对 Isambard 绕过缓存，30 秒内最多启动一次；不会绕过 Reset Credits 缓存，也不会强制刷新 Radar 或生成 Claude 限额快照。
`range` 同时筛选总量、模型、项目、会话和图表，包含今天，按本地日历日计算。日期未知的用量仅计入全部历史，并单独提示。参见 [统计说明](docs/local-usage.md)。

## Paths and environment / 路径与环境变量

| Variable | Purpose / 用途 |
| --- | --- |
| `PULSEDECK_RESET_CREDITS_ONLINE` | Defaults to `1`; set `0` to disable Reset Credits lookup |
| `CODEX_HOME` | Codex state directory; default `~/.codex` |
| `CLAUDE_CONFIG_DIR` | Claude state directory; default `~/.claude` |
| `CLAUDE_BIN` | Client discovery and the optional standalone refresher; no automatic auth check |
| `CLAUDE_USAGE_PROJECT_DIR` | Temporary refresher session's project |
| `CLAUDE_USAGE_SNAPSHOT` | Claude limit snapshot; default `~/.claude/usage-dashboard.json` |
| `CLAUDE_USAGE_STALE_SECONDS` | Snapshot stale threshold; default 900 seconds |
| `PULSEDECK_CACHE_DIR` | Public cache directory; overridden by `--cache-dir` |
| `CODEX_USAGE_CACHE_DIR` | Legacy fallback when `PULSEDECK_CACHE_DIR` is unset |
| `CODEX_USAGE_EXPORT_DIR` | CLI export directory; overridden by `export --output-dir` |
| `SSL_CERT_FILE` | CA bundle override for public status/benchmark requests |
| `OPENAI_ADMIN_KEY` | Legacy setting; Admin API collection remains disabled even when set |

Default public cache locations:

- macOS: `~/Library/Caches/pulsedeck`
- Linux: `$XDG_CACHE_HOME/pulsedeck`, or `~/.cache/pulsedeck`
- Windows: `%LOCALAPPDATA%/PulseDeck/cache`

Exports default to `~/Downloads/PulseDeck`:

```sh
python3 codex_usage.py export --report local-usage --format json --output-dir ./exports
```

Earlier repository-local public caches are read as a fallback when the new
default cache file is absent. New writes use the user cache directory; existing
files are not deleted. Custom cache directories do not read legacy caches. A
cache-write failure does not discard a successful live result.
缓存写入失败不会丢弃已抓取的数据。旧仓库缓存仅作为默认路径的回退读取，原文件不会被删除。

## Local HTTP API / 本地接口

| Route | Result |
| --- | --- |
| `GET /`, `GET /index.html` | Authenticated dashboard |
| `GET /isambard-maintenance` | Authenticated maintenance page |
| `GET /healthz` | Health check; no account data or authentication required |
| `GET /api/usage` | Usage JSON |
| `GET /api/codex-radar` | In-memory snapshot only; never triggers a fetch |
| `GET /api/sources` | Current sources, `accountNetworkEnabled: false`, `resetCreditsNetworkEnabled`, and `localDate` |
| `POST /api/sources?isambard=false&radar=true` | Change public-source switches; authenticated, requires `X-Codex-Usage-Action: set-sources` |

Pages and data APIs require the browser session cookie, or
`Authorization: Bearer <token from startup URL>`. Tokens change on restart.
Host validation applies to all routes. A wildcard bind requires an explicit
accepted hostname, for example `--host 0.0.0.0 --allowed-host 192.0.2.10`;
this exposes the server beyond the local machine.

`/api/usage` parameters:

| Parameter | Values / default |
| --- | --- |
| `report` | `all` (default), `codex-usage`, `claude-usage`, `isambard-status`, `resets`, `local-usage`, `online-usage`, `api-usage` |
| `top` | Default 10, maximum 100 |
| `range` | `today`, `7d`, `30d` (default), `all` |
| `range_anchor` | Optional local `YYYY-MM-DD`, defaults to today; future dates rejected |
| `days` | Legacy setting; does not override local `range` |
| `warn_days` | Default 7 |
| `bucket_width` | `1d` (default), `1h`, `1m` |
| `limit` | Optional Admin bucket count; maximum 1440 |
| `group_by` | Optional Admin grouping fields, repeated or comma-separated |
| `no_costs` | `true`, `1`, `yes` skips Admin costs |
| `isambard_force_refresh` | Requires authenticated POST and `X-Codex-Usage-Action: force-refresh` |

Combined `all` / `codex-usage` API responses remain complete snapshots for existing
clients. Progressive rendering is a browser behavior using the individual reports.

See [Claude setup](docs/claude-setup.md), [中文 Claude 设置](docs/claude-setup.zh-CN.md),
[Radar rules](docs/radar.md) and [中文 Radar 规则](docs/radar.zh-CN.md).
