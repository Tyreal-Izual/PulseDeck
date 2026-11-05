// Shared local usage views: totals, rankings and charts always use one scope.
Object.assign(TEXT.en, {
  timeRange: "Time range", rangeToday: "Today", range7d: "Last 7 days", range30d: "Last 30 days", rangeAll: "All local history",
  localScope: "Local time", localPolicy: "This computer only · Account network access is off",
  viewDetails: "View details", usageEvents: "Usage records", modelBreakdown: "Models", projectBreakdown: "Projects",
  otherModels: "Other models", unknownModel: "Unknown model", dataNotes: "Data notes", dailyTrend: "Daily tokens",
  noUsage: "No usage recorded in this range.", dataUnavailable: "Local usage unavailable",
  unknownDates: "Tokens without a known date", excludedDates: "excluded from this range", includedDates: "included in the total, excluded from the chart",
  unknownModels: "Tokens without a known model", skippedDuplicates: "Repeated records merged", parseErrors: "Unreadable files / malformed lines",
  pendingLines: "Incomplete lines awaiting the next refresh", counterResets: "Counter resets detected", localFiles: "Local log files",
  readBytes: "Log bytes read on this scan", codexAccounting: "Input includes cached input; output includes reasoning. These details are not added twice.",
  claudeAccounting: "Total = input + output + cache creation + cache read. Repeated messages keep the most complete usage.",
  quotaNote: "Quotas use the latest local snapshots; token history uses the selected time range.",
  codexQuota: "Codex · Remaining quota", quotaLocal: "Local quota snapshot", quotaNotReported: "Not provided in the local snapshot",
  quotaResetWaiting: "Reset time reached; awaiting a new snapshot", quotaNoSnapshot: "No quota snapshot", quotaFresh: "Recent snapshot", quotaStale: "Snapshot is stale",
  rangePublicNote: "Time range applies to local token history. Public service status and Radar show their latest snapshots.",
  trendBucket: "days per bar", cacheWriteTokens: "Cache write input (detail)"
});
Object.assign(TEXT.zh, {
  timeRange: "时间范围", rangeToday: "今天", range7d: "近 7 天", range30d: "近 30 天", rangeAll: "全部本地历史",
  localScope: "本地时间", localPolicy: "仅此电脑 · 账户网络访问已关闭",
  viewDetails: "查看详情", usageEvents: "用量记录", modelBreakdown: "模型排行", projectBreakdown: "项目排行",
  otherModels: "其他模型", unknownModel: "模型未知", dataNotes: "数据说明", dailyTrend: "每日 Token",
  noUsage: "此时间范围内暂无用量记录。", dataUnavailable: "本地用量暂不可用",
  unknownDates: "日期未知的 Token", excludedDates: "未计入此时间范围", includedDates: "已计入总量，未计入趋势图",
  unknownModels: "模型未知的 Token", skippedDuplicates: "已合并的重复记录", parseErrors: "无法读取的文件 / 格式错误行",
  pendingLines: "待下次刷新读取的未完成行", counterResets: "检测到的计数器重置", localFiles: "本地日志文件",
  readBytes: "本次扫描读取的日志字节", codexAccounting: "输入已包含缓存输入，输出已包含推理用量；这些细项不重复相加。",
  claudeAccounting: "总量 = 输入 + 输出 + 缓存写入 + 缓存读取；重复消息保留最完整的用量。",
  quotaNote: "额度显示最新本地快照；Token 历史使用所选时间范围。",
  codexQuota: "Codex · 剩余额度", quotaLocal: "本地额度快照", quotaNotReported: "本地快照未提供此窗口",
  quotaResetWaiting: "已到重置时间，等待新快照", quotaNoSnapshot: "暂无额度快照", quotaFresh: "近期快照", quotaStale: "快照已过期",
  rangePublicNote: "时间筛选适用于本地 Token 历史；服务状态和 Radar 显示最新快照。",
  trendBucket: "天 / 柱", cacheWriteTokens: "缓存写入输入（细项）"
});

function rangeLabel(range) {
  return t({today:"rangeToday", "7d":"range7d", "30d":"range30d", all:"rangeAll"}[range] || "range30d");
}

function scopeLabel(scope = {}) {
  return `${rangeLabel(scope.range)} · ${t("localScope")} · ${scope.start && scope.start !== scope.end ? scope.start + " – " : ""}${scope.end || ""}`;
}

function modelLabel(model) {
  return model === "__other__" ? t("otherModels") : model === "(unknown)" ? t("unknownModel") : model;
}

function usageTrend(daily = []) {
  if (!daily.length) return `<div class="empty">${esc(t("noDailyRows"))}</div>`;
  const start = parseLocalDate(daily[0].date), end = parseLocalDate(daily[daily.length - 1].date);
  if (!start || !end) return "";
  // Calendar UTC arithmetic avoids 23/25-hour DST days changing bucket widths.
  const ordinal = d => Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 86400000;
  const span = ordinal(end) - ordinal(start) + 1;
  const width = Math.max(1, Math.ceil(span / 60));
  const buckets = Array.from({length:Math.ceil(span / width)}, (_, i) => ({
    start:dateKey(addDays(start, i * width)), end:dateKey(addDays(start, Math.min(span - 1, (i + 1) * width - 1))), total:0
  }));
  for (const row of daily) {
    const i = Math.floor((ordinal(parseLocalDate(row.date)) - ordinal(start)) / width);
    buckets[i].total += asNumber(row.total_tokens) || 0;
  }
  const max = Math.max(...buckets.map(row => row.total), 0);
  return `<div class="usage-trend">
    <div class="trend-caption"><span>${esc(t("dailyTrend"))}${width > 1 ? ` · ${width} ${esc(t("trendBucket"))}` : ""}</span></div>
    <div class="trend-plot"><div class="trend-bars">${buckets.map(row => {
      const title = `${row.start}${row.end !== row.start ? " – " + row.end : ""}: ${fmtNumber(row.total)} tokens`;
      return `<span class="trend-slot" tabindex="0" title="${esc(title)}" aria-label="${esc(title)}"><i style="height:${max ? row.total / max * 100 : 0}%"></i></span>`;
    }).join("")}</div><div class="trend-scale"><span>${esc(fmtNumber(max))}</span><span>0</span></div></div>
    <div class="trend-axis"><span>${esc(daily[0].date)}</span><span>${esc(daily[daily.length - 1].date)}</span></div>
  </div>`;
}

function usageQuality(usage, source, compact = false) {
  const q = usage.quality || {};
  const unknown = q.unknown_date_tokens ? `<p>${esc(t("unknownDates"))}: <strong>${esc(fmtNumber(q.unknown_date_tokens))}</strong> · ${esc(t(usage.scope?.range === "all" ? "includedDates" : "excludedDates"))}</p>` : "";
  if (compact) return unknown ? `<div class="usage-caveat">${unknown}</div>` : "";
  const rows = [
    [t("unknownModels"), q.unknown_model_tokens], [t("skippedDuplicates"), q.duplicates_skipped],
    [t("counterResets"), q.counter_resets], [t("parseErrors"), q.parse_errors], [t("pendingLines"), q.pending_lines],
    [t("localFiles"), usage.files], [t("readBytes"), usage.refresh?.bytes_read]
  ].map(([key, value]) => [esc(key), esc(fmtNumber(value || 0))]);
  return `<details class="data-notes" data-disclosure="${source}-notes"><summary>${esc(t("dataNotes"))}</summary>
    <p>${esc(t(source === "codex" ? "codexAccounting" : "claudeAccounting"))}</p>${unknown}${table([t("metric"), t("value")], rows, [1])}</details>`;
}

function renderUsage(usage, source, overview = false) {
  if (!usage) return [];
  const name = source === "codex" ? "Codex" : "Claude Code";
  const totals = usage.token_totals || {};
  const models = usage.by_model || [];
  const total = totals.total_tokens || 0;
  const head = `<div class="usage-total">${trackedNumber(`${source}.total`, total)}<span>Tokens</span></div>
    <div class="usage-meta">${esc(fmtNumber(usage.session_count || 0))} ${esc(t("sessions"))}<span>·</span>${esc(fmtNumber(usage.model_count || 0))} ${esc(t("models"))}</div>`;
  const modelRows = (overview ? models.slice(0, 3) : models).map((row, i) => [
    modelKey(modelLabel(row.model), i), trackedModelNumber(source, row.model, "tokens", row.total_tokens), esc(fmtPercent(row.share))
  ]);
  const modelTable = table([t("model"), t("totalTokens"), t("share")], modelRows, [1, 2]);
  const link = `/?report=${source === "codex" ? "codex-usage" : "claude-usage"}&range=${encodeURIComponent(usage.scope?.range || "30d")}`;
  if (overview) {
    return [panel(name, scopeLabel(usage.scope), head + usageTrend(usage.daily_usage) +
      (total ? modelTable : `<div class="empty">${esc(t("noUsage"))}</div>`) + usageQuality(usage, source, true) +
      `<a class="detail-link" href="${link}">${esc(t("viewDetails"))} →</a>`, false, `${source}-summary`)];
  }
  const tokenRows = Object.keys(totals).map(field => [esc(usageFieldLabel(field)), esc(fmtNumber(totals[field]))]);
  const projects = (usage.by_project || []).map(row => [esc(row.project), esc(fmtNumber(row.sessions)), esc(fmtNumber(row.total_tokens))]);
  const sessions = (usage.top_sessions || []).map(row => [esc(row.date === "unknown" ? t("unknown") : row.date),
    esc((row.models || []).map(modelLabel).join(", ")), esc(fmtNumber(row.usage.total_tokens)), esc(row.project), `<span class="mono">${esc(row.session_file)}</span>`]);
  return [
    panel(name, scopeLabel(usage.scope), head + table([t("field"), t("total")], tokenRows, [1]) + usageQuality(usage, source), false, `${source}-totals`),
    panel(t("modelBreakdown"), scopeLabel(usage.scope), modelTable, false, `${source}-models`),
    panel(t("dailyTrend"), scopeLabel(usage.scope), usageTrend(usage.daily_usage) + usageQuality(usage, source, true), true, `${source}-daily`),
    panel(t("projectBreakdown"), "Top 10", table([t("project"), t("sessions"), t("totalTokens")], projects, [1, 2]), true, `${source}-projects`),
    panel(t("topSessions"), "Top 10", table([t("date"), t("model"), t("totalTokens"), t("project"), t("sessionFile")], sessions, [2]), true, `${source}-sessions`)
  ];
}

function collapsePanel(item, id, label) {
  if (!item) return null;
  return {title:id, wide:true, html:`<details class="collapsed-panel" data-disclosure="${id}"><summary>${esc(label)}</summary>${item.html}</details>`};
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

function quotaCountdown(reset, now = Date.now()) {
  if (!Number.isFinite(reset)) return "";
  const seconds = Math.max(0, Math.ceil(reset - now / 1000));
  if (!seconds) return t("quotaResetWaiting");
  const days = Math.floor(seconds / 86400);
  const clock = [Math.floor(seconds / 3600) % 24, Math.floor(seconds / 60) % 60, seconds % 60]
    .map(value => String(value).padStart(2, "0")).join(":");
  return `${t("resetsIn")} ${days ? days + " " + t("day") + " " : ""}${clock}`;
}

function quotaBar(source, key, window, label) {
  const reset = window?.resets_at;
  const expired = Number.isFinite(reset) && reset * 1000 <= Date.now();
  const body = leftBar(label, expired ? undefined : window?.used_percentage,
    t(expired ? "quotaResetWaiting" : window ? "quotaLocal" : "quotaNotReported"),
    quotaCountdown(reset), `${source}.${key}.remaining`);
  return `<div class="quota-window" ${Number.isFinite(reset) ? `data-quota-reset="${reset}"` : ""} data-expired="${expired}">${body}</div>`;
}

function quotaAgeMarkup(rate) {
  const captured = rate.captured_at_unix_ms;
  return Number.isFinite(captured) ? `<span data-quota-age="${captured}">${esc(fmtAgeSince(captured))}</span>` : "—";
}

function quotaStateMarkup(rate) {
  if (!rate.available) return esc(t("quotaNoSnapshot"));
  const captured = rate.captured_at_unix_ms;
  return `<span data-quota-state="${Number.isFinite(captured) ? captured : 0}" data-stale-after="${rate.stale_after_seconds || 900}">${esc(t(rate.stale ? "quotaStale" : "quotaFresh"))}</span>`;
}

function updateQuotaClocks() {
  const now = Date.now();
  document.querySelectorAll("[data-quota-age]").forEach(node => {
    node.textContent = fmtAgeSince(Number(node.dataset.quotaAge));
  });
  document.querySelectorAll("[data-quota-state]").forEach(node => {
    const stale = !Number(node.dataset.quotaState) || now - Number(node.dataset.quotaState) > Number(node.dataset.staleAfter) * 1000;
    node.textContent = t(stale ? "quotaStale" : "quotaFresh");
    const fact = node.closest(".panel-heading-extra");
    fact?.classList.toggle("panel-heading-extra--warn", stale);
    fact?.classList.toggle("panel-heading-extra--good", !stale);
  });
  document.querySelectorAll("[data-quota-reset]").forEach(node => {
    const reset = Number(node.dataset.quotaReset);
    const footer = node.querySelector(".bar-reset");
    if (footer) footer.textContent = quotaCountdown(reset, now);
    if (reset * 1000 <= now && node.dataset.expired !== "true") {
      node.dataset.expired = "true";
      node.querySelector(".barhead > span:last-child").textContent = "—";
      node.querySelector(".fill").style.width = "0%";
      node.querySelector(".subtle").textContent = t("quotaResetWaiting");
    }
  });
}

function renderCodexQuota(local) {
  const rate = local?.rate_limits;
  if (!rate) return [];
  const extras = [
    {label:t("updated"), valueHtml:quotaAgeMarkup(rate)},
    {label:t("status"), valueHtml:quotaStateMarkup(rate)},
    ...(rate.plan_type ? [{label:t("plan"), value:rate.plan_type}] : [])
  ];
  const bars = `<div class="bars quota-bars">${quotaBar("codex", "five_hour", rate.five_hour, t("claudeFiveHour"))}${quotaBar("codex", "seven_day", rate.seven_day, t("claudeWeekly"))}</div>`;
  return [panel(t("codexQuota"), t("quotaLocal"), bars, true, "codex-rate", extras)];
}
