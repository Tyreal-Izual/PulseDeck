__RADAR_SCRIPT__
__REFRESH_SCRIPT__
__PREFERENCES_SCRIPT__
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
      initialPanelPositionPending: !window.location.hash || window.location.hash === "#codex-radar",
      lang: PulseDeckPreferences.language()
    };

    const $ = (id) => document.getElementById(id);

    const TEXT = {
      en: {
        appTitle: "PulseDeck",
        subtitle: "Local usage, service status, and model intelligence.",
        sourceDisabled: "Not enabled",
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
        totalTokens: "Total Tokens",
        retrieved: "Retrieved",
        updated: "Updated",
        status: "Status",
        topSessions: "Top Sessions",
        field: "Field",
        total: "Total",
        model: "Model",
        models: "Models",
        share: "Share",
        date: "Date",
        project: "Project",
        sessionFile: "Session File",
        plan: "Plan",
        limitReached: "Limit Reached",
        resetsIn: "Resets In",
        inputTokens: "Input Tokens",
        cachedInputTokens: "Cached Input Tokens",
        outputTokens: "Output Tokens",
        reasoningOutputTokens: "Reasoning Output Tokens",
        claudeRateLimits: "Claude Code Rate Limits",
        claudeFiveHour: "5-Hour Window",
        claudeWeekly: "7-Day Window",
        claudeSnapshotAge: "Snapshot Age",
        claudeSnapshotState: "Snapshot State",
        claudeCapture: "Usage Capture",
        claudeNotInstalled: "Not Installed",
        claudeStatusLine: "statusLine",
        claudeUsageCommand: "Background /usage",
        claudeSetupTitle: "Claude rate-limit capture is not ready",
        claudeSetupHint: "On Windows, double-click Setup-Claude-Capture.cmd in the project folder, then complete a response in a compatible Claude Code client.",
        claudeWaitingTitle: "Quota capture configured · waiting for data",
        claudeWaitingHint: "Local token history is available. Quotas appear after a compatible Claude Code client supplies a snapshot; Claude Desktop may not invoke the capture. Missing values are not zero usage.",
        cacheCreationTokens: "Cache Creation Tokens",
        cacheReadTokens: "Cache Read Tokens",
        isambardStatus: "Isambard Service Status",
        isambardSubtitle: "Public service-status and planned-maintenance pages",
        serviceStatus: "Current Service Status",
        plannedMaintenance: "Planned Maintenance",
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
        appTitle: "PulseDeck",
        subtitle: "本地 AI 用量、服务状态和模型评测。",
        sourceDisabled: "未启用",
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
        totalTokens: "总 token",
        retrieved: "获取时间",
        updated: "更新时间",
        status: "状态",
        topSessions: "最高用量会话",
        field: "字段",
        total: "总计",
        model: "模型",
        models: "模型",
        share: "占比",
        date: "日期",
        project: "项目",
        sessionFile: "Session 文件",
        plan: "套餐",
        limitReached: "是否达到限制",
        resetsIn: "重置倒计时",
        inputTokens: "输入 token",
        cachedInputTokens: "缓存输入 token",
        outputTokens: "输出 token",
        reasoningOutputTokens: "推理输出 token",
        claudeRateLimits: "Claude Code 用量限制",
        claudeFiveHour: "5 小时窗口",
        claudeWeekly: "7 天窗口",
        claudeSnapshotAge: "快照时长",
        claudeSnapshotState: "快照状态",
        claudeCapture: "用量采集",
        claudeNotInstalled: "未安装",
        claudeStatusLine: "statusLine",
        claudeUsageCommand: "后台 /usage",
        claudeSetupTitle: "Claude 限额采集尚未就绪",
        claudeSetupHint: "Windows 用户可双击项目中的 Setup-Claude-Capture.cmd，然后在兼容的 Claude Code 客户端中完成一次回复。",
        claudeWaitingTitle: "额度采集已配置 · 等待数据",
        claudeWaitingHint: "本地 token 历史可正常查看。额度需要兼容的 Claude Code 客户端生成快照；Claude Desktop 可能不会触发采集。暂无数据不代表用量为零。",
        cacheCreationTokens: "缓存创建 token",
        cacheReadTokens: "缓存读取 token",
        isambardStatus: "Isambard 服务状态",
        isambardSubtitle: "公开服务状态和计划维护页面",
        serviceStatus: "当前服务状态",
        plannedMaintenance: "计划维护",
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

    function asNumber(value) {
      if (value == null || typeof value === "boolean" || (typeof value === "string" && !value.trim())) return null;
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

    function modelKey(model, index) {
      const color = modelColor(index);
      return `
        <span class="model-key" title="${esc(model || "-")}">
          <span class="model-dot" style="--dot-color: ${color}"></span>
          <span class="model-key-text">${esc(model || "-")}</span>
        </span>`;
    }

    function splitSections(data, report) {
      return {
        resets: ["all", "codex-usage"].includes(report) ? data?.reset_credits : null,
        local: ["all", "codex-usage"].includes(report) ? data?.local_usage : null,
        claude: report === "all" ? data?.claude_usage : (report === "claude-usage" ? data : null),
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

    function renderLocal(local, overview = false) {
      return local?.usage ? renderUsage(local.usage, "codex", overview) : [];
    }

    function renderClaudeQuota(claude) {
      if (!claude) {
        return [];
      }
      const rate = claude.rate_limits || {};
      const fiveHour = rate.five_hour || null;
      const sevenDay = rate.seven_day || null;
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
      const bars = `<div class="bars quota-bars">${quotaBar("claude", "five_hour", fiveHour, t("claudeFiveHour"))}${quotaBar("claude", "seven_day", sevenDay, t("claudeWeekly"))}</div>`;

      const quota = panel(t("claudeRateLimits"), t("quotaLocal"), bars + setup, true, "claude-rate", headerExtras);
      return [quota];
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
      if (!dashboardConfig.sources.includes("isambard")) {
        sections.isambard = report === "isambard-status" ? {ok:true, disabled:true, source:"isambard"} : null;
      }
      const disabled = [];
      for (const [name, value] of Object.entries(sections)) {
        if (name === "resets") continue;
        if (value?.disabled) {
          if (name !== "isambard" || report === "isambard-status") disabled.push(value.source);
          sections[name] = null;
        }
      }


      const warnings = [];
      const reportErrors = Array.isArray(payload.errors) ? payload.errors : [];
      const reportedErrors = new Set(reportErrors.map(item => item.section));
      const sourceNames = {local:"local_usage", claude:"claude_usage", resets:"reset_credits", isambard:"isambard_status"};
      reportErrors.filter(item => item.section !== "isambard_status" || dashboardConfig.sources.includes("isambard")).forEach((item) => warnings.push(`${item.section || "report"}: ${item.message || item}`));
      for (const [name, sectionData] of Object.entries(sections)) {
        if (!sectionData || typeof sectionData !== "object") {
          continue;
        }
        if (sectionData.ok === false && !reportedErrors.has(sourceNames[name])) {
          warnings.push(`${sourceNames[name] || name}: ${summarizeError(sectionData.error || "not available")}`);
        }
        if (sectionData.warning) {
          warnings.push(`${name}: ${summarizeError(sectionData.warning)}`);
        }
      }
      showNotice(warnings);

      const overview = report === "all";
      const loadingPanels = (payload.pending || []).filter(name => name !== "reset_credits" && !data[name] && (name !== "isambard_status" || dashboardConfig.sources.includes("isambard"))).map(name => panel(
        {local_usage:"Codex", claude_usage:"Claude Code", isambard_status:"Isambard"}[name] || name,
        t("loadingSources"), `<div class="empty" role="status">${esc(t("refreshing"))}…</div>`, name === "isambard_status", `loading-${name}`));
      const disabledPanels = [...new Set(disabled)].map(source => panel(
        source === "claude" ? "Claude Code" : source === "codex" ? "Codex" : "Isambard",
        t("sourceDisabled"), `<div class="empty">${esc(t("sourceDisabled"))}</div>`, false, `disabled-${source}`));
      const radar = dashboardConfig.sources.includes("radar") && ["all", "codex-usage"].includes(report)
        ? panel(CodexRadar.title(state.lang), CodexRadar.subtitle(state.lang), '<div id="codex-radar"></div>', true, "codex-radar-panel",
            [{label:t("updated"),valueHtml:'<span data-radar-age>—</span>'}]) : null;
      const panels = [
        ...renderCodexQuota(sections.local), ...renderClaudeQuota(sections.claude),
        ...renderIsambard(sections.isambard), ...loadingPanels.filter(p => p.title === "loading-isambard_status"),
        ...renderLocal(sections.local, overview), ...renderUsage(sections.claude?.local_usage, "claude", overview),
        ...loadingPanels.filter(p => p.title !== "loading-isambard_status"), ...disabledPanels,
        ...(["all", "codex-usage"].includes(report) && dashboardConfig.sources.includes("codex") ? renderResetCredits(sections.resets) : []),
        radar
      ];
      const expanded = new Set([...document.querySelectorAll("[data-disclosure][open]")].map(node => node.dataset.disclosure));
      const radarRoot = document.getElementById("codex-radar");
      const radarFocus = radarRoot?.contains(document.activeElement) ? document.activeElement : null;
      $("sections").innerHTML = packSections(panels);
      const radarPlaceholder = document.getElementById("codex-radar");
      if (radarRoot && radarPlaceholder) radarPlaceholder.replaceWith(radarRoot);
      document.querySelectorAll("[data-disclosure]").forEach(node => { node.open = expanded.has(node.dataset.disclosure); });
      $("scope-note").textContent = t("rangePublicNote");
      $("local-policy").textContent = t(dashboardConfig.resetCreditsNetworkEnabled ? "localPolicyWithResets" : "localPolicy");
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
      if (window.location.hash === "#codex-radar" && state.lastPayload?.pending?.length) return;
      if (!["all", "codex-usage"].includes(report)) {
        state.initialPanelPositionPending = false;
        return;
      }
      const target = window.location.hash === "#codex-radar"
        ? document.getElementById("codex-radar")
        : document.querySelector('[data-panel-id="codex-rate"]');
      if (!target) {
        if (!state.lastPayload?.pending?.length) state.initialPanelPositionPending = false;
        return;
      }
      requestAnimationFrame(() => {
        if (!state.initialPanelPositionPending || !target.isConnected) return;
        target.scrollIntoView({block: "start", behavior: "instant"});
        // Early partial results can leave too little page height to align the card.
        state.initialPanelPositionPending = target.getBoundingClientRect().top > 1 && Boolean(state.lastPayload?.pending?.length);
      });
    }

    function applySourceSettings(settings) {
      dashboardConfig.sources = settings.sources;
      if (settings.resetCreditsNetworkEnabled !== undefined) dashboardConfig.resetCreditsNetworkEnabled = settings.resetCreditsNetworkEnabled;
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
          resetCreditsNetworkEnabled: dashboardConfig.resetCreditsNetworkEnabled,
          force: forceIsambardRefresh === true, signal: controller.signal}, payload => {
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
          positionInitialPanel(report);
          if (payload.pending.length) {
            setStatus(t("refreshing"), `${t("loadingSources")}: ${payload.pending.length}`);
          } else {
            setStatus(payload.ok ? t("upToDate") : t("loadedWithNotes"), `${t("lastRefresh")} ${new Date().toLocaleTimeString()}`);
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
      PulseDeckPreferences.setRange($("time-range").value);
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
      state.lang = PulseDeckPreferences.setLanguage($("language").value);
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

    const requestedRange = new URLSearchParams(window.location.search).get("range") || PulseDeckPreferences.range();
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
