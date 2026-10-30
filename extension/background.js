// Quick Profile Switch: Ein Klick auf den Knopf öffnet das jeweils andere Firefox-Profil.
// Profile auflisten und starten übernimmt das Hilfsprogramm "quick_profile_switch" (Native Messaging).

const HOST = "quick_profile_switch";
// Die interne Kennung der Erweiterung ist pro Profil verschieden – daran erkennt das Hilfsprogramm das aktuelle Profil
const OWN_UUID = new URL(browser.runtime.getURL("/")).host;
// Alle Fensterarten: Bleibt auch nur ein Popup (z. B. ein Anmeldefenster) offen, beendet sich Firefox nicht
// und das Hauptfenster landet nur unter „Kürzlich geschlossene Fenster“
const ALL_WINDOW_TYPES = ["normal", "popup", "panel", "app", "devtools"];
const t = (key, ...subs) => browser.i18n.getMessage(key, subs);

class HelperMissing extends Error {}

async function callHost(cmd, extra = {}) {
  let res;
  try {
    res = await browser.runtime.sendNativeMessage(HOST, { cmd, uuid: OWN_UUID, ...extra });
  } catch (e) {
    throw new HelperMissing(e.message);
  }
  if (res.error) throw new Error(res.error);
  return res;
}

async function showError(message) {
  await browser.action.setBadgeText({ text: "!" });
  await browser.action.setTitle({ title: t("errorTitle", message) });
}

function openSetup() {
  return browser.tabs.create({ url: browser.runtime.getURL("setup.html") });
}

// Knopf, Tooltip und Rechtsklick-Menü an die aktuelle Profil-Liste anpassen.
// Ergebnis: { profiles } oder { missing: true }, wenn das Hilfsprogramm fehlt
async function refresh() {
  let profiles;
  try {
    ({ profiles } = await callHost("list"));
  } catch (e) {
    await browser.action.setPopup({ popup: "" });
    if (e instanceof HelperMissing) {
      await browser.action.setBadgeText({ text: "!" });
      await browser.action.setTitle({ title: t("helperMissing") });
      await buildMenu([], true);
      return { missing: true };
    }
    await showError(e.message);
    await buildMenu([], false);
    return { profiles: [] };
  }
  const others = profiles.filter(p => !p.current);
  await browser.action.setBadgeText({ text: "" });
  if (others.length === 1) {
    await browser.action.setPopup({ popup: "" });
    await browser.action.setTitle({ title: t("switchTo", others[0].name) });
  } else {
    await browser.action.setPopup({ popup: "popup.html" });
    await browser.action.setTitle({ title: t("chooseProfile") });
  }
  await buildMenu(profiles, false);
  return { profiles };
}

async function buildMenu(profiles, missing) {
  await browser.menus.removeAll();
  if (missing) {
    browser.menus.create({ id: "einrichten", contexts: ["action"], title: t("menuSetup") });
    return;
  }
  profiles.forEach((p, i) => browser.menus.create({
    id: `profil-${i}`,
    contexts: ["action"],
    enabled: !p.current,
    title: p.current ? t("menuCurrent", p.name) : t("menuOpen", p.name),
  }));
  browser.menus.create({ id: "trenner", type: "separator", contexts: ["action"] });
  const { closeOnSwitch } = await browser.storage.local.get({ closeOnSwitch: true });
  browser.menus.create({
    id: "profil-schliessen",
    type: "checkbox",
    contexts: ["action"],
    checked: closeOnSwitch,
    title: t("menuCloseOnSwitch"),
  });
}

// Schließt alle Fenster dieses Profils; beim letzten Fenster beendet sich Firefox und speichert die Sitzung.
// Firefox stellt beim Start nur das zuletzt geschlossene Fenster wieder her – darum vorher alle Tabs dort sammeln.
async function closeProfile(windowId) {
  const closedBefore = new Set((await browser.sessions.getRecentlyClosed())
    .filter(e => e.window).map(e => e.window.sessionId));
  const windows = await browser.windows.getAll({ windowTypes: ALL_WINDOW_TYPES });
  const normal = windows.filter(w => w.type === "normal" && !w.incognito);
  const target = normal.find(w => w.id === windowId) ?? normal[0];
  for (const w of windows) {
    if (w === target) continue;
    if (w.incognito || w.type !== "normal") {
      // Private Tabs speichert Firefox ohnehin nicht; Popups sind kurzlebig (Anmeldung, Zahlung, Erweiterungs-Fenster)
      await browser.windows.remove(w.id);
      continue;
    }
    // Angeheftete Tabs dürfen nur in den angehefteten Bereich, sonst ignoriert Firefox das Verschieben
    const tabs = await browser.tabs.query({ windowId: w.id });
    const pinnedInTarget = (await browser.tabs.query({ windowId: target.id, pinned: true })).length;
    const pinned = tabs.filter(tab => tab.pinned).map(tab => tab.id);
    const rest = tabs.filter(tab => !tab.pinned).map(tab => tab.id);
    if (pinned.length) await browser.tabs.move(pinned, { windowId: target.id, index: pinnedInTarget });
    if (rest.length) await browser.tabs.move(rest, { windowId: target.id, index: -1 });
  }
  if (!target) return;
  // Erst schließen, wenn wirklich nur noch dieses Fenster übrig ist – sonst gingen Tabs verloren
  let merged = false;
  for (let i = 0; i < 20 && !merged; i++) {
    await new Promise(r => setTimeout(r, 100));
    merged = !(await browser.windows.getAll({ windowTypes: ALL_WINDOW_TYPES })).some(w => w.id !== target.id);
  }
  if (!merged) {
    await showError(t("mergeFailed"));
    return;
  }
  // Leer gewordene Fenster landen in „Kürzlich geschlossene Fenster“ und würden beim Start mit doppeltem Tab wiederhergestellt
  for (const entry of await browser.sessions.getRecentlyClosed()) {
    if (entry.window && !closedBefore.has(entry.window.sessionId)) {
      await browser.sessions.forgetClosedWindow(entry.window.sessionId);
    }
  }
  await browser.windows.remove(target.id);
}

async function switchTo(profile, windowId) {
  try {
    await callHost("open", { path: profile.path });
  } catch (e) {
    await showError(e.message);
    return;
  }
  const { closeOnSwitch } = await browser.storage.local.get({ closeOnSwitch: true });
  if (closeOnSwitch) await closeProfile(windowId);
}

browser.runtime.onInstalled.addListener(async ({ reason }) => {
  const state = await refresh();
  if (reason === "install" && state.missing) await openSetup();
});
browser.runtime.onStartup.addListener(refresh);

// Bei genau einem anderen Profil wechselt der Knopf direkt (sonst ist ein Popup gesetzt und dieses Ereignis kommt nicht)
browser.action.onClicked.addListener(async tab => {
  const state = await refresh();
  if (state.missing) return openSetup();
  const others = state.profiles.filter(p => !p.current);
  if (others.length === 1) await switchTo(others[0], tab.windowId);
  else if (others.length > 1) browser.action.openPopup().catch(() => {});
});

browser.menus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "einrichten") return openSetup();
  if (info.menuItemId === "profil-schliessen") {
    await browser.storage.local.set({ closeOnSwitch: info.checked });
    return;
  }
  const { profiles = [] } = await refresh();
  const profile = profiles[Number(String(info.menuItemId).replace("profil-", ""))];
  if (profile && !profile.current) await switchTo(profile, tab?.windowId);
});

// Nachrichten aus dem Popup und der Einrichtungsseite
browser.runtime.onMessage.addListener(async msg => {
  if (msg.type === "list") return refresh();
  if (msg.type === "setup") return openSetup();
  if (msg.type === "open") {
    const win = await browser.windows.getLastFocused();
    await switchTo(msg.profile, win.id);
  }
});
