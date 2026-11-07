__PREFERENCES_SCRIPT__
const state = {
      loading: false,
      disabled: false,
      failed: false,
      lastPayload: null,
      lang: PulseDeckPreferences.language()
    };

    const $ = (id) => document.getElementById(id);
    const TEXT = {
      en: {
        back: "← Back to Dashboard",
        language: "Language",
        title: "Planned Maintenance",
        schedule: "Maintenance Schedule",
        refresh: "Refresh Source",
        refreshing: "Refreshing…",
        loading: "Loading…",
        noRows: "No planned maintenance is currently listed.",
        fetchedAt: "Source Fetched",
        liveFetch: "Live Fetch",
        cachedData: "Cached Result",
        disabled: "Isambard is disabled. Enable Isambard Status on the dashboard.",
        failed: "Could not load maintenance details."
      },
      zh: {
        back: "← 返回仪表盘",
        language: "语言",
        title: "计划维护",
        schedule: "维护计划",
        refresh: "刷新源数据",
        refreshing: "刷新中…",
        loading: "正在加载…",
        noRows: "当前没有列出的计划维护。",
        fetchedAt: "源数据抓取时间",
        liveFetch: "实时抓取",
        cachedData: "缓存结果",
        disabled: "Isambard 未启用，请在首页勾选 Isambard Status。",
        failed: "无法加载维护详情。"
      }
    };

    function t(key) {
      return TEXT[state.lang]?.[key] || TEXT.en[key] || key;
    }

    function esc(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    function applyLanguage() {
      document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
      document.title = `${t("title")} · PulseDeck`;
      document.querySelectorAll("[data-i18n]").forEach((node) => {
        node.textContent = t(node.dataset.i18n);
      });
      $("language").value = state.lang;
    }

    function showNotice(lines) {
      const clean = lines.filter(Boolean);
      $("notice").textContent = clean.join("\n");
      $("notice").classList.toggle("show", clean.length > 0);
    }

    function maintenanceTable(headers, rows) {
      if (!headers.length) {
        return `<div class="empty">${esc(t("noRows"))}</div>`;
      }
      const head = headers.map((item) => `<th>${esc(item)}</th>`).join("");
      const body = rows.length
        ? rows.map((row) => `<tr>${row.map((item) => `<td>${esc(item)}</td>`).join("")}</tr>`).join("")
        : `<tr><td colspan="${headers.length}">${esc(t("noRows"))}</td></tr>`;
      return `<div class="table-wrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
    }

    function render(payload) {
      state.lastPayload = payload;
      const data = payload.data || {};
      const snapshot = data.status || {};
      const headers = Array.isArray(snapshot.maintenance_headers) ? snapshot.maintenance_headers : [];
      const rows = Array.isArray(snapshot.maintenance_rows)
        ? snapshot.maintenance_rows.filter(Array.isArray)
        : [];
      $("content").innerHTML = maintenanceTable(headers, rows);
      const source = data.source === "live" ? t("liveFetch") : t("cachedData");
      $("meta").textContent = `${t("fetchedAt")}: ${snapshot.fetched_at || "-"} · ${source}`;
      const warnings = [data.warning];
      if (Array.isArray(payload.errors)) {
        payload.errors.forEach((item) => warnings.push(`${item.section || "report"}: ${item.message || item}`));
      }
      showNotice(warnings);
    }

    async function load(forceRefresh = false) {
      if (state.loading) {
        return;
      }
      state.loading = true;
      state.disabled = state.failed = false;
      $("refresh").disabled = true;
      $("refresh").textContent = t("refreshing");
      try {
        const params = new URLSearchParams({ report: "isambard-status", _: Date.now().toString() });
        if (forceRefresh) {
          params.set("isambard_force_refresh", "true");
        }
        const options = { cache: "no-store" };
        if (forceRefresh) {
          options.method = "POST";
          options.headers = { "X-Codex-Usage-Action": "force-refresh" };
        }
        const response = await fetch(`/api/usage?${params.toString()}`, options);
        const payload = await response.json();
        if (response.ok && payload.data?.disabled) {
          state.disabled = true;
          $("content").innerHTML = `<div class="empty">${esc(t("disabled"))}</div>`;
          $("meta").textContent = "";
          return;
        }
        if (!response.ok || !payload.data?.status) {
          throw new Error(payload.data?.error?.message || payload.error || t("failed"));
        }
        render(payload);
      } catch (error) {
        state.failed = true;
        showNotice([error.message || t("failed")]);
        $("content").innerHTML = `<div class="empty">${esc(t("failed"))}</div>`;
        $("meta").textContent = "";
      } finally {
        state.loading = false;
        $("refresh").disabled = false;
        $("refresh").textContent = t("refresh");
      }
    }

    applyLanguage();
    $("language").addEventListener("change", () => {
      state.lang = PulseDeckPreferences.setLanguage($("language").value);
      applyLanguage();
      if (state.disabled || state.failed) {
        $("content").innerHTML = `<div class="empty">${esc(t(state.disabled ? "disabled" : "failed"))}</div>`;
      } else if (state.lastPayload) {
        render(state.lastPayload);
      }
      if (state.loading) $("refresh").textContent = t("refreshing");
    });
    $("refresh").addEventListener("click", () => load(!state.disabled));
    load();
