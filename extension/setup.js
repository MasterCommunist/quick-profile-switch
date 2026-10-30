// Einrichtungsseite: erklärt das Hilfsprogramm, verlinkt den Download und prüft, ob es erreichbar ist
const REPOSITORY = "https://github.com/MasterCommunist/quick-profile-switch";
const t = (key, ...subs) => browser.i18n.getMessage(key, subs);

document.documentElement.lang = browser.i18n.getUILanguage();
document.title = t("setupPageTitle");
document.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });
document.getElementById("download").href = `${REPOSITORY}/releases/latest`;
document.getElementById("source").href = REPOSITORY;

const status = document.getElementById("status");
document.getElementById("check").addEventListener("click", async () => {
  status.className = "";
  status.textContent = t("setupChecking");
  const state = await browser.runtime.sendMessage({ type: "list" });
  const ok = !state.missing && state.profiles.length > 0;
  status.className = ok ? "ok" : "missing";
  status.textContent = t(ok ? "setupOk" : "setupMissing");
});
