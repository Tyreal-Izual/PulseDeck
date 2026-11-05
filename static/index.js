__RADAR_SCRIPT__
__REFRESH_SCRIPT__
    const dashboardConfig = __DASHBOARD_CONFIG__;
    const state = {
      timer: null,
      loading: false,
      sourceRevision: 0,
      refreshController: null,
      updatingSources: false,
      pendingRefresh: false,
      pendingForceRefresh: false,
      lastPayload: null,
      initialPanelPositionPending: window.location.hash === "#codex-radar",
      lang: localStorage.getItem("pulsedeckLanguage") || ((navigator.language || "").toLowerCase().startsWith("zh") ? "zh" : "en")
    };

    const $ = (id) => document.getElementById(id);

    const TEXT = {
      en: {
        moduleUsage: "Usage", moduleStatus: "Service status", moduleScores: "Model scores",
        appTitle: "PulseDeck",
        subtitle: "Local usage, service status, and model intelligence.",
        sourceDisabled: "Not enabled",
        setupSources: "No local sources detected. Sign in to Codex or Claude Code, then restart the dashboard. Use --check for setup diagnostics.",
        loadingSources: "Loading sources",
        statusStarting: "Starting",
        statusWaiting: "Waiting for the first refresh.",
        report: "Report",
        reportAll: "Workspace overview",
        backToLimits: "Back to quota",
        reportCodex: "Codex Usage",
        reportClaude: "Claude Code Usage",
        reportIsambard: "Isambard Service Status",
        language: "Language",
        autoRefresh: "Auto Refresh",
        refresh: "Refresh",
        refreshing: "Refreshing",
        refreshingDetail: "Reading local usage and public status snapshots.",
        upToDate: "Up to Date",
        loadedWithNotes: "Loaded With Notes",
        lastRefresh: "Last Refresh",
        refreshFailed: "Refresh Failed",
        refreshFailedDetail: "See the message below the controls.",
        metric: "Metric",
        value: "Value",
        emptySection: "No data found for this section.",
        noDailyRows: "No daily usage rows found.",
        now: "now",
        lessThanMinute: "<1 min",
        day: "day",
        daysUnit: "days",
        hr: "hr",
        min: "min",
        left: "left",
        sessions: "Sessions",
        output: "Output",
        totalTokensWindow: "Total Tokens in This Window",
        busiestDay: "Busiest Day",
        less: "Less",
        more: "More",
        totalTokens: "Total Tokens",
        resetCredits: "Codex Reset Credits",
        resetSubtitle: "Available earned resets",
        retrieved: "Retrieved",
        updated: "Updated",
        availableResets: "Available Resets",
        creditsReturned: "Credits Returned",
        totalEarnedCount: "Total Earned Count",
        status: "Status",
        expiresLocally: "Expires Locally",
        timeRemaining: "Time Remaining",
        grantedLocally: "Granted Locally",
        localTokenTotals: "Codex Local Token Totals",
        localTokenSubtitle: "Final counters from local session files",
        sqliteModelCounters: "Codex Models",
        sqliteSubtitle: "Local thread database",
        dailyLocalUsage: "Codex Daily Local Usage",
        dayWindow: "Day Window",
        topSessions: "Codex Top Sessions",
        topSessionsSubtitle: "Largest local session counters",
        field: "Field",
        total: "Total",
        model: "Model",
        models: "Models",
        threads: "Threads",
        tokensUsed: "Tokens Used",
        share: "Share",
        date: "Date",
        project: "Project",
        sessionFile: "Session File",
        onlineRateLimits: "Codex Online Rate Limits",
        onlineSubtitle: "Read-only account quota data",
        primaryWindow: "Primary Window",
        weeklyWindow: "Weekly Window",
        primaryHint: "Available before the primary limit is reached",
        weeklyHint: "Available before the weekly limit is reached",
        plan: "Plan",
        limitReached: "Limit Reached",
        resetsIn: "Resets In",
        creditsBalance: "Credits Balance",
        hasCredits: "Has Credits",
        profileStatistics: "Codex Profile Statistics",
        profileSubtitle: "Redacted profile data",
        lifetimeTokens: "Lifetime Tokens",
        peakDailyTokens: "Peak Daily Tokens",
        mostUsedReasoningEffort: "Most-Used Reasoning Effort",
        reasoningEffortShare: "Reasoning Effort Share",
        adminApiStatus: "Admin API Status",
        adminApiSubtitle: "Uses OPENAI_ADMIN_KEY when set",
        completionsUsage: "Completions Usage",
        adminApi: "OpenAI Admin API",
        costs: "Costs",
        days: "Days",
        bucketWidth: "Bucket Width",
        usageStatus: "Usage Status",
        costsStatus: "Costs Status",
        error: "Error",
        bucketStart: "Bucket Start",
        group: "Group",
        input: "Input",
        requests: "Requests",
        amount: "Amount",
        currency: "Currency",
        lineItem: "Line Item",
        inputTokens: "Input Tokens",
        cachedInputTokens: "Cached Input Tokens",
        outputTokens: "Output Tokens",
        reasoningOutputTokens: "Reasoning Output Tokens",
        claudeRateLimits: "Claude Code Rate Limits",
        claudeRateSubtitle: "Claude Code subscription usage snapshot",
        claudeFiveHour: "5-Hour Window",
        claudeWeekly: "7-Day Window",
        claudeFiveHourHint: "Available before the Claude 5-hour limit is reached",
        claudeWeeklyHint: "Available before the Claude weekly limit is reached",
        claudeSnapshotAge: "Snapshot Age",
        claudeLogin: "CLI Login",
        claudeLoginHealthy: "Logged in",
        claudeLoginRequired: "Re-login required",
        claudeLoginWarningTitle: "Claude Code CLI login has expired",
        claudeLoginWarningHint: "Run this command in Terminal, then wait for the next background refresh:",
        claudeSnapshotState: "Snapshot State",
        claudeFresh: "Fresh",
        claudeStale: "Stale",
        claudeCapture: "Usage Capture",
        claudeNotInstalled: "Not Installed",
        claudeStatusLine: "statusLine",
        claudeUsageCommand: "Background /usage",
        claudeSetupTitle: "Claude rate-limit capture is not ready",
        claudeSetupHint: "On Windows, double-click Setup-Claude-Capture.cmd in the project folder, then complete a response in a compatible Claude Code client.",
        claudeWaitingTitle: "Quota capture configured · waiting for data",
        claudeWaitingHint: "Local token history is available. Quotas appear after a compatible Claude Code client supplies a snapshot; Claude Desktop may not invoke the capture. Missing values are not zero usage.",
        claudeLocalTokens: "Claude Code Local Token Totals",
        claudeLocalSubtitle: "Deduplicated assistant usage records from local JSONL files",
        cacheCreationTokens: "Cache Creation Tokens",
        cacheReadTokens: "Cache Read Tokens",
        uniqueRequests: "Unique Requests",
        duplicateRowsSkipped: "Duplicate Rows Skipped",
        claudeModels: "Claude Code Models",
        claudeModelsSubtitle: "Token totals grouped by model",
        viewClaudeDetails: "View full Claude Code details →",
        viewCodexDetails: "View full Codex details →",
        claudeProjects: "Claude Code Projects",
        claudeProjectsSubtitle: "Highest local token totals by project",
        claudeDailyUsage: "Claude Code Daily Usage",
        claudeTopSessions: "Claude Code Top Sessions",
        claudeTopSessionsSubtitle: "Largest deduplicated local session totals",
        isambardStatus: "Isambard Service Status",
        isambardSubtitle: "Public service-status and planned-maintenance pages",
        serviceStatus: "Current Service Status",
        plannedMaintenance: "Planned Maintenance",
        fetchedAt: "Source Fetched",
        dataSource: "Data Source",
        liveFetch: "Live Fetch",
        cachedData: "Cached Result",
        cacheAge: "Cache Age",
        maintenanceWindow: "Maintenance Window",
        maintenanceWindows: "Maintenance Windows",
        viewMaintenance: "View full schedule →",
        operational: "Operational",
        degraded: "Warning",
        outage: "Outage",
        unknown: "Unknown"
      },
      zh: {
        moduleUsage: "用量", moduleStatus: "服务状态", moduleScores: "模型评测",
        appTitle: "PulseDeck",
        subtitle: "AI 用量仅从本机读取，不查询账号接口；Isambard 与 Radar 继续使用公开数据。",
        sourceDisabled: "未启用",
        setupSources: "未检测到本地数据源。请登录 Codex 或 Claude Code 后重启面板，可使用 --check 检查配置。",
        loadingSources: "正在加载数据源",
        statusStarting: "正在启动",
        statusWaiting: "等待第一次刷新。",
        report: "报告",
        reportAll: "工作台总览",
        backToLimits: "返回额度",
        reportCodex: "Codex 用量",
        reportClaude: "Claude Code 用量",
        reportIsambard: "Isambard 服务状态",
        language: "语言",
        autoRefresh: "自动刷新",
        refresh: "刷新",
        refreshing: "刷新中",
        refreshingDetail: "正在读取本地用量和公共状态快照。",
        upToDate: "已更新",
        loadedWithNotes: "已加载，有提示",
        lastRefresh: "上次刷新",
        refreshFailed: "刷新失败",
        refreshFailedDetail: "请查看控件下方的提示信息。",
        metric: "指标",
        value: "值",
        emptySection: "这个区域没有找到数据。",
        noDailyRows: "没有找到每日用量数据。",
        now: "现在",
        lessThanMinute: "少于 1 分钟",
        day: "天",
        daysUnit: "天",
        hr: "小时",
        min: "分钟",
        left: "剩余",
        sessions: "会话",
        output: "输出",
        totalTokensWindow: "此时间窗口内的总 token",
        busiestDay: "最高用量日",
        less: "少",
        more: "多",
        totalTokens: "总 token",
        resetCredits: "Codex 重置额度",
        resetSubtitle: "可用的累积重置额度",
        retrieved: "获取时间",
        updated: "更新时间",
        availableResets: "可用重置次数",
        creditsReturned: "返回额度数",
        totalEarnedCount: "累计获得数",
        status: "状态",
        expiresLocally: "本地过期时间",
        timeRemaining: "剩余时间",
        grantedLocally: "本地授予时间",
        localTokenTotals: "Codex 本地 token 总量",
        localTokenSubtitle: "来自本地 session 文件的最终计数",
        sqliteModelCounters: "Codex 模型用量",
        sqliteSubtitle: "本地 thread 数据库",
        dailyLocalUsage: "Codex 每日本地用量",
        dayWindow: "天窗口",
        topSessions: "Codex 最高用量 session",
        topSessionsSubtitle: "本地 token 计数最大的 session",
        field: "字段",
        total: "总计",
        model: "模型",
        models: "模型",
        threads: "线程",
        tokensUsed: "已用 token",
        share: "占比",
        date: "日期",
        project: "项目",
        sessionFile: "Session 文件",
        onlineRateLimits: "Codex 在线速率限制",
        onlineSubtitle: "只读账号额度信息",
        primaryWindow: "Primary 窗口",
        weeklyWindow: "Weekly 窗口",
        primaryHint: "距离 primary 限制前仍可使用的比例",
        weeklyHint: "距离 weekly 限制前仍可使用的比例",
        plan: "套餐",
        limitReached: "是否达到限制",
        resetsIn: "重置倒计时",
        creditsBalance: "额度余额",
        hasCredits: "是否有额度",
        profileStatistics: "Codex 资料统计",
        profileSubtitle: "已脱敏的资料数据",
        lifetimeTokens: "生命周期 token",
        peakDailyTokens: "单日峰值 token",
        mostUsedReasoningEffort: "最常用推理强度",
        reasoningEffortShare: "推理强度占比",
        adminApiStatus: "Admin API 状态",
        adminApiSubtitle: "设置 OPENAI_ADMIN_KEY 后使用",
        completionsUsage: "Completions 用量",
        adminApi: "OpenAI Admin API",
        costs: "成本",
        days: "天数",
        bucketWidth: "桶宽",
        usageStatus: "用量状态",
        costsStatus: "成本状态",
        error: "错误",
        bucketStart: "桶开始",
        group: "分组",
        input: "输入",
        requests: "请求数",
        amount: "金额",
        currency: "货币",
        lineItem: "项目",
        inputTokens: "输入 token",
        cachedInputTokens: "缓存输入 token",
        outputTokens: "输出 token",
        reasoningOutputTokens: "推理输出 token",
        claudeRateLimits: "Claude Code 用量限制",
        claudeRateSubtitle: "Claude Code 订阅用量快照",
        claudeFiveHour: "5 小时窗口",
        claudeWeekly: "7 天窗口",
        claudeFiveHourHint: "距离 Claude 5 小时限制前仍可使用的比例",
        claudeWeeklyHint: "距离 Claude Weekly 限制前仍可使用的比例",
        claudeSnapshotAge: "快照时长",
        claudeLogin: "CLI 登录",
        claudeLoginHealthy: "已登录",
        claudeLoginRequired: "需要重新验证",
        claudeLoginWarningTitle: "Claude Code CLI 登录已失效",
        claudeLoginWarningHint: "请在 Terminal 运行以下命令，完成验证后等待下一次后台刷新：",
        claudeSnapshotState: "快照状态",
        claudeFresh: "新鲜",
        claudeStale: "已过期",
        claudeCapture: "用量采集",
        claudeNotInstalled: "未安装",
        claudeStatusLine: "statusLine",
        claudeUsageCommand: "后台 /usage",
        claudeSetupTitle: "Claude 限额采集尚未就绪",
        claudeSetupHint: "Windows 用户可双击项目中的 Setup-Claude-Capture.cmd，然后在兼容的 Claude Code 客户端中完成一次回复。",
        claudeWaitingTitle: "额度采集已配置 · 等待数据",
        claudeWaitingHint: "本地 token 历史可正常查看。额度需要兼容的 Claude Code 客户端生成快照；Claude Desktop 可能不会触发采集。暂无数据不代表用量为零。",
        claudeLocalTokens: "Claude Code 本地 token 总量",
        claudeLocalSubtitle: "从本地 JSONL 去重得到的 assistant 用量记录",
        cacheCreationTokens: "缓存创建 token",
        cacheReadTokens: "缓存读取 token",
        uniqueRequests: "唯一请求数",
        duplicateRowsSkipped: "跳过的重复记录",
        claudeModels: "Claude Code 模型用量",
        claudeModelsSubtitle: "按模型汇总的 token",
        viewClaudeDetails: "查看完整 Claude Code 详情 →",
        viewCodexDetails: "查看完整 Codex 详情 →",
        claudeProjects: "Claude Code 项目用量",
        claudeProjectsSubtitle: "本地 token 用量最高的项目",
        claudeDailyUsage: "Claude Code 每日用量",
        claudeTopSessions: "Claude Code 最高用量会话",
        claudeTopSessionsSubtitle: "去重后的最大本地会话用量",
        isambardStatus: "Isambard 服务状态",
        isambardSubtitle: "公开服务状态和计划维护页面",
        serviceStatus: "当前服务状态",
        plannedMaintenance: "计划维护",
        fetchedAt: "源数据抓取时间",
        dataSource: "数据来源",
        liveFetch: "实时抓取",
        cachedData: "缓存结果",
        cacheAge: "缓存时长",
        maintenanceWindow: "个维护窗口",
        maintenanceWindows: "个维护窗口",
        viewMaintenance: "查看完整维护计划 →",
        operational: "正常",
        degraded: "警告",
        outage: "中断",
        unknown: "未知"
      }
    };

__USAGE_SCRIPT__

    function t(key) {
      return TEXT[state.lang]?.[key] || TEXT.en[key] || key;
    }

    function applyLanguage() {
      document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
      document.title = t("appTitle");
      document.querySelectorAll("[data-i18n]").forEach((node) => {
        if (node.id === "status-title" || node.id === "status-detail") {
          return;
        }
        node.textContent = t(node.dataset.i18n);
      });
      $("language").value = state.lang;
    }

    function esc(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    function get(obj, path, fallback = undefined) {
      let cur = obj;
      for (const key of path) {
        if (cur == null || typeof cur !== "object" || !(key in cur)) {
          return fallback;
        }
        cur = cur[key];
      }
      return cur;
    }

    function asNumber(value) {
      const number = Number(value);
      return Number.isFinite(number) ? number : null;
    }

    function fmtNumber(value) {
      const number = asNumber(value);
      if (number === null) {
        return value === undefined || value === null || value === "" ? "-" : String(value);
      }
      return Math.round(number).toLocaleString();
    }

    function trackedNumber(key, value, display) {
      if (value == null || value === "" || typeof value === "boolean" || asNumber(value) === null) return "-";
      const text = display ?? fmtNumber(value);
      return `<span class="tracked-value" data-change-key="${esc(key)}" data-change-value="${esc(text)}">${esc(text)}</span>`;
    }

    function trackedModelNumber(provider, model, field, value, display) {
      return trackedNumber(JSON.stringify([provider, "model", model, field]), value, display);
    }

    const valueChangeTimes = new Map();
    function displayedTrackedValues() {
      return new Map(Array.from($("sections").querySelectorAll('[data-change-key]'),
        node => [node.dataset.changeKey, node.dataset.changeValue]));
    }

    function highlightChangedValues(previous, enabled) {
      if (!enabled) valueChangeTimes.clear();
      const now = performance.now();
      const seen = new Set();
      $("sections").querySelectorAll('[data-change-key]').forEach(node => {
        const {changeKey: key, changeValue: value} = node.dataset;
        seen.add(key);
        if (enabled && previous.has(key) && previous.get(key) !== value) {
          valueChangeTimes.set(key, {value, started: now});
        }
        const change = valueChangeTimes.get(key);
        if (!change || change.value !== value || now - change.started >= 4000) return;
        node.classList.add('value-changed');
        // Continue an existing highlight across fast refreshes without pulsing again.
        const elapsed = now - change.started;
        node.style.animationDelay = `-${elapsed}ms, -${elapsed}ms`;
      });
      for (const [key, change] of valueChangeTimes) {
        if (!seen.has(key) || now - change.started >= 4000) valueChangeTimes.delete(key);
      }
    }

    function fmtPercent(value) {
      const number = asNumber(value);
      return number === null ? "-" : `${number.toFixed(1)}%`;
    }

    function fmtDurationSeconds(value) {
      const seconds = asNumber(value);
      if (seconds === null) {
        return "-";
      }
      if (seconds <= 0) {
        return t("now");
      }
      const totalMinutes = Math.floor(seconds / 60);
      if (totalMinutes < 1) {
        return t("lessThanMinute");
      }
      const days = Math.floor(totalMinutes / 1440);
      const hours = Math.floor((totalMinutes % 1440) / 60);
      const minutes = totalMinutes % 60;
      if (days > 0) {
        const dayUnit = state.lang === "zh" ? t("day") : days === 1 ? t("day") : t("daysUnit");
        return `${days} ${dayUnit} ${hours} ${t("hr")} ${minutes} ${t("min")}`;
      }
      if (hours > 0) {
        return `${hours} ${t("hr")} ${minutes} ${t("min")}`;
      }
      return `${minutes} ${t("min")}`;
    }

    function fmtAgeSince(unixMilliseconds) {
      const timestamp = asNumber(unixMilliseconds);
      if (timestamp === null) {
        return "-";
      }
      return fmtDurationSeconds(Math.max(0, (Date.now() - timestamp) / 1000));
    }

    function setStatus(title, detail) {
      $("status-title").textContent = title;
      $("status-detail").textContent = detail;
    }

    function showNotice(lines) {
      const notice = $("notice");
      const clean = (lines || []).filter(Boolean);
      notice.textContent = clean.join("\n");
      notice.classList.toggle("show", clean.length > 0);
    }

    function summarizeError(value) {
      if (value == null || value === "") {
        return "";
      }
      if (typeof value === "string") {
        return value;
      }
      if (typeof value !== "object") {
        return String(value);
      }
      if (value.message) {
        return summarizeError(value.message);
      }
      if (value.error) {
        return summarizeError(value.error);
      }
      if (value.reason) {
        return summarizeError(value.reason);
      }
      if (value.body_excerpt) {
        return summarizeError(value.body_excerpt);
      }
      try {
        return JSON.stringify(value);
      } catch {
        return String(value);
      }
    }

    function pill(value, tone = "") {
      return `<span class="pill ${tone}">${esc(value)}</span>`;
    }

    function table(headers, rows, numericIndexes = [], className = "") {
      if (!rows || rows.length === 0) {
        return `<div class="empty">${esc(t("emptySection"))}</div>`;
      }
      const numeric = new Set(numericIndexes);
      const head = headers.map((h, i) => `<th${numeric.has(i) ? " class=\"num\"" : ""}>${esc(h)}</th>`).join("");
      const body = rows.map((row) => {
        return `<tr>${row.map((cell, i) => {
          const cls = numeric.has(i) ? " class=\"num\"" : "";
          return `<td${cls}>${cell}</td>`;
        }).join("")}</tr>`;
      }).join("");
      const cls = className ? ` class="${esc(className)}"` : "";
      return `<div class="table-wrap"><table${cls}><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
    }

    function kvGrid(rows) {
      if (!rows || rows.length === 0) {
        return `<div class="empty">${esc(t("emptySection"))}</div>`;
      }
      return `
        <div class="kv-grid">
          ${rows.map((row) => `
            <div class="kv-item">
              <span class="kv-label">${row[0]}</span>
              <span class="kv-value">${row[1]}</span>
            </div>`).join("")}
        </div>`;
    }

    function compactFacts(rows) {
      if (!rows || rows.length === 0) {
        return "";
      }
      return `
        <div class="compact-facts">
          ${rows.map((row) => `
            <span class="compact-fact">
              <span>${row[0]}</span>
              <strong>${row[1]}</strong>
            </span>`).join("")}
        </div>`;
    }

    function panel(title, subtitle, body, wide = false, id = title, headerExtras = []) {
      const extras = Array.isArray(headerExtras) ? headerExtras : [];
      const renderHeaderExtras = (items, className) => items.length
        ? `<span class="${className}">${items.map((item) => `
            <span class="panel-heading-extra${item.tone ? ` panel-heading-extra--${esc(item.tone)}` : ""}">
              <span>${esc(item.label || "")}</span>
              <strong>${item.valueHtml || esc(item.value ?? "-")}</strong>
            </span>`).join("")}</span>`
        : "";
      const leadingExtras = renderHeaderExtras(
        extras.filter((item) => item.position !== "end"),
        "panel-heading-extras"
      );
      const trailingExtras = renderHeaderExtras(
        extras.filter((item) => item.position === "end"),
        "panel-heading-end-extras"
      );
      const html = `
        <section class="panel${wide ? " panel--wide" : ""}" data-panel-id="${esc(id)}">
          <h2>
            <span class="panel-heading-main">
              <span class="panel-heading-title">${esc(title)}</span>
              ${leadingExtras}
            </span>
            ${trailingExtras}
            <span class="panel-heading-subtitle">${esc(subtitle || "")}</span>
          </h2>
          <div class="panel-body">${body}</div>
        </section>`;
      return { html, title: id, wide: Boolean(wide) };
    }

    // Greedy row packing that preserves order: wide panels take a full row,
    // compact panels pair up two-per-row. No dense reflow, so reading order
    // stays intact and there are no floating gaps.
    function packSections(panels) {
      const rows = [];
      let hold = null;
      const flush = (items, wide) => {
        const cls = wide ? "section-row section-row--wide" : "section-row";
        rows.push(`<div class="${cls}">${items.map((p) => p.html).join("")}</div>`);
      };
      for (const p of panels) {
        if (!p) {
          continue;
        }
        if (p.wide) {
          if (hold) {
            flush([hold], false);
            hold = null;
          }
          flush([p], true);
        } else if (hold) {
          flush([hold, p], false);
          hold = null;
        } else {
          hold = p;
        }
      }
      if (hold) {
        flush([hold], false);
      }
      return rows.join("");
    }

    function limitLeft(usedValue) {
      if (usedValue == null || usedValue === "" || typeof usedValue === "boolean") return null;
      const used = asNumber(usedValue);
      return used === null ? null : Math.max(0, Math.min(100, 100 - used));
    }

    function leftBar(label, usedValue, hint, footer = "", changeKey = "") {
      const left = limitLeft(usedValue);
      const percent = left === null ? 0 : left;
      const tone = left !== null && left <= 10 ? "bad" : left !== null && left <= 25 ? "warn" : "";
      const numberHtml = left === null ? "-" : changeKey
        ? trackedNumber(changeKey, left, `${left.toFixed(1)}%`) : esc(`${left.toFixed(1)}%`);
      const valueHtml = left === null ? "-" : state.lang === "zh" ? `${esc(t("left"))} ${numberHtml}` : `${numberHtml} ${esc(t("left"))}`;
      return `
        <div class="barbox">
          <div class="barhead"><span>${esc(label)}</span><span>${valueHtml}</span></div>
          <div class="track"><div class="fill ${tone}" style="width: ${percent}%"></div></div>
          <div class="bar-meta">
            <span class="subtle">${esc(hint || "")}</span>
            ${footer ? `<span class="bar-reset">${esc(footer)}</span>` : ""}
          </div>
        </div>`;
    }

    function hasRateLimitWindow(window) {
      return Boolean(window) && typeof window === "object" && Object.values(window).some((value) => value !== null && value !== undefined);
    }

    function visibleRateLimitWindows(rateLimit) {
      const primary = get(rateLimit, ["primary_window"]);
      const weekly = get(rateLimit, ["secondary_window"]);
      const hasPrimary = hasRateLimitWindow(primary);
      const hasWeekly = hasRateLimitWindow(weekly);

      // When Codex temporarily has only a weekly limit, /wham/usage returns it
      // in primary_window and omits secondary_window. Present that one window
      // as weekly, while retaining the normal mapping when both are available.
      if (hasPrimary && !hasWeekly) {
        return { primary: null, weekly: primary };
      }
      return {
        primary: hasPrimary ? primary : null,
        weekly: hasWeekly ? weekly : null
      };
    }

    function parseLocalDate(value) {
      const match = String(value || "").match(/^(\d{4})-(\d{2})-(\d{2})$/);
      if (!match) {
        return null;
      }
      return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
    }

    function dateKey(date) {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const day = String(date.getDate()).padStart(2, "0");
      return `${year}-${month}-${day}`;
    }

    function addDays(date, days) {
      const next = new Date(date);
      next.setDate(next.getDate() + days);
      return next;
    }

    const MODEL_COLORS = [
      "#55d486",
      "#46d3b8",
      "#69a7ff",
      "#c58cff",
      "#f0b45c",
      "#ff7a90",
      "#8bd36f",
      "#55c7f0",
      "#d4d46a",
      "#f08be8"
    ];

    function modelColor(index) {
      return MODEL_COLORS[index % MODEL_COLORS.length];
    }

    function sqliteModelKey(model, index) {
      const color = modelColor(index);
      return `
        <span class="model-key" title="${esc(model || "-")}">
          <span class="model-dot" style="--dot-color: ${color}"></span>
          <span class="model-key-text">${esc(model || "-")}</span>
        </span>`;
    }

    function splitSections(data, report) {
      return {
        resets: ["all", "codex-usage"].includes(report) ? data?.reset_credits : (report === "resets" ? data : null),
        local: ["all", "codex-usage"].includes(report) ? data?.local_usage : (report === "local-usage" ? data : null),
        online: ["all", "codex-usage"].includes(report) ? data?.online_usage : (report === "online-usage" ? data : null),
        claude: report === "all" ? data?.claude_usage : (report === "claude-usage" ? data : null),
        api: report === "all" ? data?.api_usage : (report === "codex-usage" ? data?.api_usage : (report === "api-usage" ? data : null)),
        isambard: report === "all" ? data?.isambard_status : (report === "isambard-status" ? data : null)
      };
    }

    function usageFieldLabel(field) {
      return {
        input_tokens: t("inputTokens"),
        cached_input_tokens: t("cachedInputTokens"),
        cache_write_input_tokens: t("cacheWriteTokens"),
        output_tokens: t("outputTokens"),
        reasoning_output_tokens: t("reasoningOutputTokens"),
        cache_creation_input_tokens: t("cacheCreationTokens"),
        cache_read_input_tokens: t("cacheReadTokens"),
        total_tokens: t("totalTokens")
      }[field] || field.replaceAll("_", " ");
    }

    function renderResets(resets) {
      if (!resets) {
        return [];
      }
      const rows = (Array.isArray(resets.credits) ? resets.credits : []).map((credit, index) => {
        const tone = credit.status === "available" ? "" : credit.status === "expired" ? "bad" : "warn";
        return [
          esc(index + 1),
          pill(credit.status || "unknown", tone),
          esc(credit.expires_at_local || "-"),
          esc(credit.time_remaining || "-"),
          esc(credit.granted_at_local || "-")
        ];
      });
      const credits = table(["#", t("status"), t("expiresLocally"), t("timeRemaining"), t("grantedLocally")], rows, [], "reset-credits-table");
      const headerExtras = [
        { label: t("availableResets"), valueHtml: trackedNumber("codex.resets.available", resets.available_count) },
        { label: t("creditsReturned"), valueHtml: trackedNumber("codex.resets.returned", resets.credits_returned) },
        { label: t("totalEarnedCount"), valueHtml: trackedNumber("codex.resets.earned", resets.total_earned_count) }
      ];
      if (asNumber(resets.retrieved_at_unix_ms) !== null) {
        headerExtras.unshift({ label: t("retrieved"), value: fmtAgeSince(resets.retrieved_at_unix_ms) });
      }
      return [panel(t("resetCredits"), t("resetSubtitle"), credits, true, "codex-resets", headerExtras)];
    }

    function renderLocal(local, overview = false) {
      return local?.usage ? renderUsage(local.usage, "codex", overview) : [];
    }

    function renderOnline(online) {
      if (!online) {
        return [];
      }
      const rate = get(online, ["endpoints", "rate_limit_status", "data"], {});
      const profile = get(online, ["endpoints", "profile", "data"], {});
      const rateLimit = get(rate, ["rate_limit"], {});
      const windows = visibleRateLimitWindows(rateLimit);
      const limitReached = get(rateLimit, ["limit_reached"], "-");
      const headerExtras = [
        { label: t("plan"), value: rate.plan_type || "-" },
        {
          label: t("limitReached"),
          value: limitReached,
          tone: limitReached === true ? "bad" : limitReached === false ? "good" : ""
        },
        { label: t("updated"), value: fmtAgeSince(online.retrieved_at_unix_ms) },
        { label: t("creditsBalance"), valueHtml: trackedNumber("codex.credits.balance", get(rate, ["credits", "balance"])), position: "end" },
        { label: t("hasCredits"), value: get(rate, ["credits", "has_credits"], "-"), position: "end" }
      ];
      const stats = profile.stats || {};
      const profileRows = [
        [esc(t("lifetimeTokens")), esc(fmtNumber(stats.lifetime_tokens))],
        [esc(t("peakDailyTokens")), esc(fmtNumber(stats.peak_daily_tokens))],
        [esc(t("mostUsedReasoningEffort")), esc(stats.most_used_reasoning_effort || "-")],
        [esc(t("reasoningEffortShare")), esc(fmtPercent(stats.most_used_reasoning_effort_percentage))]
      ];
      const primaryReset = `${t("resetsIn")} ${fmtDurationSeconds(windows.primary ? windows.primary.reset_after_seconds : undefined)}`;
      const weeklyReset = `${t("resetsIn")} ${fmtDurationSeconds(windows.weekly ? windows.weekly.reset_after_seconds : undefined)}`;
      const bars = `<div class="bars">${leftBar(t("primaryWindow"), windows.primary ? windows.primary.used_percent : undefined, t("primaryHint"), primaryReset, "codex.primary.remaining")}${leftBar(t("weeklyWindow"), windows.weekly ? windows.weekly.used_percent : undefined, t("weeklyHint"), weeklyReset, "codex.weekly.remaining")}</div>`;
      return [
        panel(t("onlineRateLimits"), t("onlineSubtitle"), bars, true, "codex-rate", headerExtras),
        panel(t("profileStatistics"), t("profileSubtitle"), table([t("metric"), t("value")], profileRows, [1]), false, "profile")
      ];
    }

    function renderClaude(claude, showDetailsLink = false) {
      if (!claude) {
        return [];
      }
      const rate = claude.rate_limits || {};
      const fiveHour = rate.five_hour || null;
      const sevenDay = rate.seven_day || null;
      const authStatus = rate.auth_status || {};
      const loginHealthy = authStatus.indicator === "logged_in";
      const requiresLogin = authStatus.indicator === "requires_login";
      const captureReady = rate.capture_ready ?? rate.capture_installed;
      const captureValue = rate.capture_method === "usage_command"
        ? t("claudeUsageCommand")
        : (rate.capture_installed ? t("claudeStatusLine") : t("claudeNotInstalled"));
      const headerExtras = [
        { label: t("claudeSnapshotAge"), valueHtml: quotaAgeMarkup(rate) },
        {
          label: t("claudeSnapshotState"),
          valueHtml: quotaStateMarkup(rate),
          position: "end",
          tone: rate.available && !rate.stale ? "good" : "warn"
        },
        {
          label: t("claudeCapture"),
          value: captureValue,
          position: "end",
          tone: captureReady ? "good" : "warn"
        }
      ];
      if (loginHealthy || requiresLogin) {
        headerExtras.splice(1, 0, {
          label: t("claudeLogin"),
          value: t(requiresLogin ? "claudeLoginRequired" : "claudeLoginHealthy"),
          tone: requiresLogin ? "bad" : "good"
        });
      }
      const planValue = rate.plan_type || rate.plan;
      if (planValue !== undefined && planValue !== null && planValue !== "") {
        headerExtras.push({ label: t("plan"), value: planValue });
      }
      if (rate.limit_reached !== undefined && rate.limit_reached !== null) {
        headerExtras.push({ label: t("limitReached"), value: rate.limit_reached });
      }
      const setup = rate.available && captureReady ? "" : `
        <div class="setup-callout">
          <strong>${esc(t(captureReady ? "claudeWaitingTitle" : "claudeSetupTitle"))}</strong>
          <span>${esc(t(captureReady ? "claudeWaitingHint" : "claudeSetupHint"))}</span>
          ${captureReady ? "" : '<code class="setup-command mono">Setup-Claude-Capture.cmd</code>'}
        </div>`;
      const loginWarning = requiresLogin ? `
        <div class="setup-callout setup-callout--bad">
          <strong>${esc(t("claudeLoginWarningTitle"))}</strong>
          <span>${esc(t("claudeLoginWarningHint"))}</span>
          <code class="setup-command mono">claude auth login</code>
        </div>` : "";
      const bars = `<div class="bars quota-bars">${quotaBar("claude", "five_hour", fiveHour, t("claudeFiveHour"))}${quotaBar("claude", "seven_day", sevenDay, t("claudeWeekly"))}</div>`;

      const quota = panel(t("claudeRateLimits"), t("quotaLocal"), bars + loginWarning + setup, !showDetailsLink, "claude-rate", headerExtras);
      return [quota];
    }

    function renderApiUsage(api) {
      if (!api) {
        return [];
      }
      const usageRows = get(api, ["usage", "rows"], []);
      const costRows = get(api, ["costs", "rows"], []);
      const usageTableRows = Array.isArray(usageRows) ? usageRows
        .slice()
        .sort((a, b) => (asNumber(b.total_tokens) || 0) - (asNumber(a.total_tokens) || 0))
        .map((row) => [
          esc(row.start_time_local || "-"),
          esc(row.model || row.project_id || row.api_key_id || "(all)"),
          esc(fmtNumber(row.input_tokens)),
          esc(fmtNumber(row.output_tokens)),
          esc(fmtNumber(row.total_tokens)),
          esc(fmtNumber(row.num_model_requests))
        ]) : [];
      const costTableRows = Array.isArray(costRows) ? costRows
        .slice()
        .sort((a, b) => (asNumber(b.amount) || 0) - (asNumber(a.amount) || 0))
        .map((row) => [
          esc(row.start_time_local || "-"),
          esc(row.line_item || row.project_id || row.api_key_id || "(all)"),
          esc(row.amount ?? "-"),
          esc((row.currency || "-").toUpperCase())
        ]) : [];
      const statusRows = [
        [esc(t("retrieved")), esc(api.retrieved_at_local || "-")],
        [esc(t("days")), esc(fmtNumber(api.days))],
        [esc(t("bucketWidth")), esc(api.bucket_width || "-")],
        [esc(t("usageStatus")), esc(get(api, ["usage", "ok"], false) ? "ok" : "error")],
        [esc(t("costsStatus")), esc(get(api, ["costs", "skipped"], false) ? "skipped" : (get(api, ["costs", "ok"], false) ? "ok" : "error"))],
        [esc(t("error")), esc(api.error || get(api, ["usage", "error", "error"], "") || "")]
      ];
      return [
        panel(t("adminApiStatus"), t("adminApiSubtitle"), table([t("metric"), t("value")], statusRows)),
        panel(t("completionsUsage"), t("adminApi"), table([t("bucketStart"), t("group"), t("input"), t("output"), t("total"), t("requests")], usageTableRows, [2, 3, 4, 5]), true),
        panel(t("costs"), t("adminApi"), table([t("bucketStart"), t("group"), t("amount"), t("currency")], costTableRows, [2]), true)
      ];
    }

    function isambardStatusKind(item) {
      const sourceClass = String(item?.class || "").toLowerCase();
      const title = String(item?.title || "").toLowerCase();
      if (sourceClass.includes("success") || title.includes("no known issue")) {
        return "ok";
      }
      if (sourceClass.includes("warning") || title.includes("degraded") || title.includes("at risk")) {
        return "warning";
      }
      if (sourceClass.includes("failure") || title.includes("outage")) {
        return "outage";
      }
      return "unknown";
    }

    function isambardStatusLabel(kind) {
      return {
        ok: t("operational"),
        warning: t("degraded"),
        outage: t("outage"),
        unknown: t("unknown")
      }[kind] || t("unknown");
    }

    function renderIsambard(isambard) {
      if (!isambard) {
        return [];
      }
      const snapshot = isambard.status || {};
      const statuses = Array.isArray(snapshot.statuses) ? snapshot.statuses : [];
      const source = isambard.source === "live" ? "live" : "cache";
      const rows = (Array.isArray(snapshot.maintenance_rows) ? snapshot.maintenance_rows : [])
        .filter(row => !(String(row[0] || "").trim().toLowerCase() === "no planned maintenance" && row.slice(1).every(cell => !String(cell || "").trim())));
      const maintenanceLabel = rows.length === 1 ? t("maintenanceWindow") : t("maintenanceWindows");
      const headerExtras = [
        { label: t("cacheAge"), value: source === "cache" ? fmtDurationSeconds(isambard.cache_age_seconds) : "-" },
        {
          label: t("plannedMaintenance"),
          valueHtml: `<a class="maintenance-link" href="/isambard-maintenance">${esc(`${fmtNumber(rows.length)} ${maintenanceLabel}`)} · ${esc(t("viewMaintenance"))}</a>`
        }
      ];
      const statusCards = statuses.map((item) => {
        const kind = isambardStatusKind(item);
        const tone = kind === "ok" ? "" : kind === "outage" ? "bad" : "warn";
        return `
          <details class="service-card ${esc(kind)}">
            <summary>
              <span>${esc(item.title || "-")}</span>
              ${pill(isambardStatusLabel(kind), tone)}
            </summary>
            <p>${esc(item.body || t("emptySection"))}</p>
          </details>`;
      }).join("");
      const cards = statusCards || `<div class="empty">${esc(t("emptySection"))}</div>`;

      return [
        panel(
          t("isambardStatus"),
          t("isambardSubtitle"),
          `<div class="subtle">${esc(t("serviceStatus"))}</div><div class="service-cards">${cards}</div>`,
          true,
          "isambard-status",
          headerExtras
        )
      ];
    }

    function render(payload, highlightChanges = false) {
      const previousValues = displayedTrackedValues();
      const report = payload.report;
      const data = payload.data || {};
      const sections = splitSections(data, report);
      sections.retrieved = data.retrieved_at_local || payload.served_at_local || "-";
      if (!dashboardConfig.sources.includes("isambard")) {
        sections.isambard = report === "isambard-status" ? {ok:true, disabled:true, source:"isambard"} : null;
      }
      const disabled = [];
      for (const [name, value] of Object.entries(sections)) {
        if (value?.disabled) {
          if (!value.local_only && name !== "api" && (name !== "isambard" || report === "isambard-status")) disabled.push(value.source);
          sections[name] = null;
        }
      }


      const warnings = [];
      if (Array.isArray(payload.errors)) {
        payload.errors.filter(item => item.section !== "isambard_status" || dashboardConfig.sources.includes("isambard")).forEach((item) => warnings.push(`${item.section || "report"}: ${item.message || item}`));
      }
      for (const [name, sectionData] of Object.entries(sections)) {
        if (name === "retrieved" || !sectionData || typeof sectionData !== "object") {
          continue;
        }
        if (sectionData.ok === false) {
          warnings.push(`${name}: ${summarizeError(sectionData.error || "not available")}`);
        }
        if (sectionData.warning) {
          warnings.push(`${name}: ${summarizeError(sectionData.warning)}`);
        }
        if (sectionData.endpoints && typeof sectionData.endpoints === "object") {
          for (const [endpointName, endpoint] of Object.entries(sectionData.endpoints)) {
            if (endpoint && endpoint.ok === false) {
              warnings.push(`${name}.${endpointName}: ${summarizeError(endpoint.error || "not available")}`);
            }
          }
        }
      }
      showNotice(warnings);

      const overview = report === "all";
      const loadingPanels = (payload.pending || []).filter(name => !data[name] && (name !== "isambard_status" || dashboardConfig.sources.includes("isambard"))).map(name => panel(
        {local_usage:"Codex", claude_usage:"Claude Code", isambard_status:"Isambard"}[name] || name,
        t("loadingSources"), `<div class="empty" role="status">${esc(t("refreshing"))}…</div>`, false, `loading-${name}`));
      const disabledPanels = [...new Set(disabled)].map(source => panel(
        source === "claude" ? "Claude Code" : source === "codex" ? "Codex" : "Isambard",
        t("sourceDisabled"), `<div class="empty">${esc(t("sourceDisabled"))}</div>`, false, `disabled-${source}`));
      const radar = dashboardConfig.sources.includes("radar") && ["all", "codex-usage"].includes(report)
        ? panel(CodexRadar.title(state.lang), CodexRadar.subtitle(state.lang), '<div id="codex-radar"></div>', true, "codex-radar-panel",
            [{label:t("updated"),valueHtml:'<span data-radar-age>—</span>'}]) : null;
      const panels = [
        ...renderCodexQuota(sections.local, overview), ...renderClaude(sections.claude, overview),
        ...renderLocal(sections.local, overview), ...renderUsage(sections.claude?.local_usage, "claude", overview),
        ...loadingPanels, ...disabledPanels, ...renderIsambard(sections.isambard),
        collapsePanel(radar, "radar-details", "Radar · " + t("moduleScores"))
      ];
      const expanded = new Set([...document.querySelectorAll("[data-disclosure][open]")].map(node => node.dataset.disclosure));
      const radarRoot = document.getElementById("codex-radar");
      const radarFocus = radarRoot?.contains(document.activeElement) ? document.activeElement : null;
      $("sections").innerHTML = packSections(panels);
      const radarPlaceholder = document.getElementById("codex-radar");
      if (radarRoot && radarPlaceholder) radarPlaceholder.replaceWith(radarRoot);
      document.querySelectorAll("[data-disclosure]").forEach(node => { node.open = expanded.has(node.dataset.disclosure); });
      $("scope-note").textContent = t("rangePublicNote");
      $("local-policy").textContent = t("localPolicy");
      $("quota-note").textContent = t("quotaNote");
      if (radarPlaceholder) radarFocus?.focus({preventScroll: true});
      CodexRadar.mount(document.getElementById("codex-radar"), state.lang, fmtAgeSince);
      updateQuotaClocks();
      const hasRateLimits = Boolean(document.querySelector('[data-panel-id="codex-rate"], [data-panel-id="claude-rate"]'));
      $("return-to-limits").hidden = !hasRateLimits;
      document.body.classList.toggle("has-return-to-limits", hasRateLimits);
      highlightChangedValues(previousValues, highlightChanges);
    }

    function positionInitialPanel(report) {
      if (!state.initialPanelPositionPending) return;
      if (!["all", "codex-usage"].includes(report)) {
        state.initialPanelPositionPending = false;
        return;
      }
      const target = document.getElementById("codex-radar");
      if (!target) return;
      const disclosure = target.closest("details");
      if (disclosure) disclosure.open = true;
      requestAnimationFrame(() => {
        if (!state.initialPanelPositionPending || !target.isConnected) return;
        state.initialPanelPositionPending = false;
        target.scrollIntoView({block: "start", behavior: "instant"});
      });
    }

    function applySourceSettings(settings) {
      dashboardConfig.sources = settings.sources;
      $("isambard-enabled").checked = settings.sources.includes("isambard");
      $("radar-enabled").checked = settings.sources.includes("radar");
    }

    async function toggleSource(source, checked) {
      const previous = [...dashboardConfig.sources];
      state.updatingSources = true;
      state.sourceRevision++;
      state.initialPanelPositionPending = false;
      state.refreshController?.abort();
      clearTimeout(state.timer);
      applySourceSettings({sources: checked ? [...new Set([...previous, source])] : previous.filter(s => s !== source)});
      $("isambard-enabled").disabled = $("radar-enabled").disabled = true;
      if (state.lastPayload) render(state.lastPayload);
      try {
        const response = await fetch(`/api/sources?${source}=${checked}`, {
          method: "POST", headers: {"X-Codex-Usage-Action": "set-sources"}, cache: "no-store"
        });
        const settings = await response.json();
        if (!response.ok) throw new Error(settings.error || `HTTP ${response.status}`);
        applySourceSettings(settings);
      } catch (error) {
        applySourceSettings({sources: previous});
        if (state.lastPayload) render(state.lastPayload);
        showNotice([error.message || String(error)]);
      } finally {
        state.updatingSources = false;
        $("isambard-enabled").disabled = $("radar-enabled").disabled = false;
        refresh();
      }
    }

    async function refresh(forceIsambardRefresh = false) {
      if (state.updatingSources) return;
      if (state.loading) {
        state.pendingRefresh = true;
        state.pendingForceRefresh = state.pendingForceRefresh || forceIsambardRefresh === true;
        return;
      }
      clearTimeout(state.timer);
      state.timer = null;
      const report = $("report").value;
      const days = String(dashboardConfig.days);
      const range = $("time-range").value;
      const revision = state.sourceRevision;
      const controller = new AbortController();
      state.refreshController = controller;
      let sameReport = state.lastPayload?.report === report && state.lastPayload?.range === range;
      state.loading = true;
      $("refresh-now").disabled = true;
      $("sections").setAttribute("aria-busy", "true");
      setStatus(t("refreshing"), t("refreshingDetail"));
      try {
        const sourceResponse = await fetch("/api/sources", {cache: "no-store", signal: controller.signal});
        if (!sourceResponse.ok) throw new Error(`HTTP ${sourceResponse.status}`);
        const sourceSettings = await sourceResponse.json();
        if (revision !== state.sourceRevision) return;
        applySourceSettings(sourceSettings);
        sameReport = sameReport && state.lastPayload?.rangeAnchor === sourceSettings.localDate;
        await DashboardRefresh.run({report, days, range, rangeAnchor:sourceSettings.localDate, sources: dashboardConfig.sources,
          adminEnabled: dashboardConfig.adminEnabled, accountNetworkEnabled: dashboardConfig.accountNetworkEnabled, force: forceIsambardRefresh === true, signal: controller.signal}, payload => {
          // A result from the previous selection must never overwrite the new view.
          if ($("report").value !== report || $("time-range").value !== range || revision !== state.sourceRevision || controller.signal.aborted) return;
          // Preserve completed sections during a refresh, replacing each as it arrives.
          if (sameReport && payload.pending.length) {
            payload.data = ["all", "codex-usage"].includes(report)
              ? {...state.lastPayload.data, ...payload.data}
              : state.lastPayload.data;
          }
          state.lastPayload = payload;
          render(payload, sameReport);
          if (payload.pending.length) {
            setStatus(t("refreshing"), `${t("loadingSources")}: ${payload.pending.length}`);
          } else {
            setStatus(payload.ok ? t("upToDate") : t("loadedWithNotes"), `${t("lastRefresh")} ${new Date().toLocaleTimeString()}`);
            positionInitialPanel(report);
          }
        });
      } catch (error) {
        if (controller.signal.aborted) return;
        showNotice([error.message || String(error)]);
        setStatus(t("refreshFailed"), t("refreshFailedDetail"));
      } finally {
        state.loading = false;
        $("sections").setAttribute("aria-busy", "false");
        $("refresh-now").disabled = false;
        if (state.pendingRefresh) {
          const pendingForce = state.pendingForceRefresh;
          state.pendingRefresh = false;
          state.pendingForceRefresh = false;
          refresh(pendingForce);
        } else {
          schedule();
        }
      }
    }

    function schedule() {
      if (state.timer) {
        clearTimeout(state.timer);
        state.timer = null;
      }
      const enabled = $("auto").checked;
      const seconds = dashboardConfig.refreshSeconds;
      if (enabled) {
        state.timer = setTimeout(refresh, seconds * 1000);
      }
    }

    $("refresh-now").addEventListener("click", () => refresh(true));
    $("return-to-limits").addEventListener("click", () => {
      state.initialPanelPositionPending = false;
      const target = document.querySelector('[data-panel-id="codex-rate"], [data-panel-id="claude-rate"]');
      target?.scrollIntoView({
        block: "start",
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth"
      });
    });
    function changeView() {
      state.initialPanelPositionPending = false;
      state.sourceRevision++;
      state.refreshController?.abort();
      state.lastPayload = null;
      $("sections").replaceChildren();
      localStorage.setItem("pulsedeckRange", $("time-range").value);
      const params = new URLSearchParams({report:$("report").value, range:$("time-range").value});
      history.replaceState(null, "", `/?${params}`);
      refresh();
    }
    $("report").addEventListener("change", changeView);
    $("time-range").addEventListener("change", changeView);
    $("isambard-enabled").addEventListener("change", event => toggleSource("isambard", event.target.checked));
    $("radar-enabled").addEventListener("change", event => toggleSource("radar", event.target.checked));
    $("auto").addEventListener("change", schedule);
    $("language").addEventListener("change", () => {
      state.lang = $("language").value === "zh" ? "zh" : "en";
      localStorage.setItem("pulsedeckLanguage", state.lang);
      applyLanguage();
      if (state.lastPayload) {
        render(state.lastPayload);
        const when = new Date().toLocaleTimeString();
        if (state.loading) {
          setStatus(t("refreshing"), `${t("loadingSources")}: ${state.lastPayload.pending?.length || 0}`);
        } else {
          setStatus(state.lastPayload.ok ? t("upToDate") : t("loadedWithNotes"), `${t("lastRefresh")} ${when}`);
        }
      } else {
        setStatus(t("statusStarting"), t("statusWaiting"));
      }
    });

    const requestedRange = new URLSearchParams(window.location.search).get("range") || localStorage.getItem("pulsedeckRange") || "30d";
    $("time-range").value = ["today", "7d", "30d", "all"].includes(requestedRange) ? requestedRange : "30d";
    const requestedReport = new URLSearchParams(window.location.search).get("report") || dashboardConfig.defaultReport;
    if (requestedReport && Array.from($("report").options).some((option) => option.value === requestedReport)) {
      $("report").value = requestedReport;
    }
    if (state.initialPanelPositionPending && ["all", "codex-usage"].includes($("report").value)) {
      history.scrollRestoration = "manual";
    }
    const cancelInitialPosition = () => { state.initialPanelPositionPending = false; };
    window.addEventListener("wheel", cancelInitialPosition, {passive: true});
    window.addEventListener("touchmove", cancelInitialPosition, {passive: true});
    window.addEventListener("keydown", (event) => {
      if (["ArrowUp", "ArrowDown", "PageUp", "PageDown", "Home", "End", " "].includes(event.key)) {
        cancelInitialPosition();
      }
    });
    applySourceSettings(dashboardConfig);
    applyLanguage();
    setStatus(t("statusStarting"), t("statusWaiting"));
    refresh();
    setInterval(updateQuotaClocks, 1000);
