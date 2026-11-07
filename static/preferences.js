// Shared by the dashboard and maintenance page. English is the initial default.
const PulseDeckPreferences = (() => {
  function read(key) {
    try { return localStorage.getItem(key); } catch { return null; }
  }
  function write(key, value) {
    try { localStorage.setItem(key, value); } catch { /* Keep the current selection in memory. */ }
    return value;
  }
  return {
    language: () => read("pulsedeckLanguage") === "zh" ? "zh" : "en",
    setLanguage: value => write("pulsedeckLanguage", value === "zh" ? "zh" : "en"),
    range: () => read("pulsedeckRange") || "30d",
    setRange: value => write("pulsedeckRange", value)
  };
})();
