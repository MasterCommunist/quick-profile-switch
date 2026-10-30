// Auswahlliste, falls es mehr als zwei Profile gibt oder das aktuelle Profil (noch) unbekannt ist
const t = (key, ...subs) => browser.i18n.getMessage(key, subs);
const container = document.getElementById("profile");
document.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });

browser.runtime.sendMessage({ type: "list" }).then(state => {
  container.textContent = "";
  if (state.missing || !state.profiles.length) {
    const button = document.createElement("button");
    button.textContent = t("menuSetup");
    button.addEventListener("click", async () => {
      await browser.runtime.sendMessage({ type: "setup" });
      window.close();
    });
    const note = document.createElement("p");
    note.textContent = t("popupNoHelper");
    container.append(note, button);
    return;
  }
  for (const profile of state.profiles) {
    const button = document.createElement("button");
    button.textContent = profile.current ? t("menuCurrent", profile.name) : profile.name;
    button.disabled = profile.current;
    if (profile.bg && profile.fg) {
      button.style.background = profile.bg;
      button.style.color = profile.fg;
    }
    button.addEventListener("click", async () => {
      await browser.runtime.sendMessage({ type: "open", profile });
      window.close();
    });
    container.append(button);
  }
});
