# Quick Profile Switch

Switch between Firefox profiles with one click. The current profile closes and keeps all its tabs, so the next time you open it, everything is back.

*Deutsch: siehe [unten](#deutsch).*

## Features

- **One click or Alt+Shift+P** opens the other profile (with more than two profiles, a small menu in the profile colors).
- **Closes the current profile** when switching, keeping every tab: tabs from several windows are merged into one window first, pinned tabs stay pinned, and pop-up windows (e.g. sign-in windows) are closed so the profile really quits. Can be turned off by right-clicking the button.
- Works with Firefox's built-in profile manager (profile names and colors) and with classic profiles.
- English and German.

## Requirements

- Firefox 140 or newer on **Windows** (macOS and Linux are not supported yet).
- The small **helper app** `quick-profile-switch-host.exe`. Firefox does not allow add-ons to start other profiles on their own, so the helper does this via Firefox's native messaging.

## Installation

1. Install the add-on from [addons.mozilla.org](https://addons.mozilla.org/).
2. Download `quick-profile-switch-host.exe` from the [latest release](https://github.com/MasterCommunist/quick-profile-switch/releases/latest) and double-click it. It installs itself for your Windows user (no admin rights) into `%LOCALAPPDATA%\Programs\QuickProfileSwitch`. Windows SmartScreen may warn because the file is not code-signed: choose "More info" → "Run anyway". You can compare the file with `SHA256SUMS.txt` from the release.
3. Install the add-on in **every** profile you want to switch from.

**Uninstall:** Windows Settings → Apps → Installed apps → Quick Profile Switch, and remove the add-on in Firefox.

## Privacy

No data is collected or sent anywhere. Details: [PRIVACY.md](PRIVACY.md).

## Building from source

```
python tools/make_icons.py
pip install pyinstaller
python tools/build_host.py
python tools/build_release.py --owner <github-user> --host-exe ../dist-build/dist/quick-profile-switch-host.exe
```

The add-on in `extension/` is plain JavaScript without a build step.

## License

[MIT](LICENSE). The helper bundles the Python runtime and other components under their own licenses, see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md). Firefox is a trademark of the Mozilla Foundation; this project is not affiliated with Mozilla.

---

## Deutsch

Mit einem Klick zwischen Firefox-Profilen wechseln. Das aktuelle Profil schließt sich und behält alle Tabs, beim nächsten Öffnen ist alles wieder da.

### Funktionen

- **Ein Klick oder Alt+Shift+P** öffnet das andere Profil (bei mehr als zwei Profilen ein kleines Menü in den Profilfarben).
- **Schließt das aktuelle Profil** beim Wechsel und behält alle Tabs: Tabs aus mehreren Fenstern werden vorher in einem Fenster gesammelt, angeheftete Tabs bleiben angeheftet, Popup-Fenster (z. B. Anmeldefenster) werden geschlossen, damit sich das Profil wirklich beendet. Per Rechtsklick auf den Knopf abschaltbar.
- Funktioniert mit Firefox' eingebautem Profil-Manager (Namen und Farben) und mit klassischen Profilen.
- Deutsch und Englisch.

### Voraussetzungen

- Firefox 140 oder neuer unter **Windows** (macOS und Linux noch nicht).
- Das kleine **Hilfsprogramm** `quick-profile-switch-host.exe`. Firefox erlaubt Erweiterungen nicht, selbst andere Profile zu starten; das übernimmt das Hilfsprogramm über Firefox' Native Messaging.

### Installation

1. Die Erweiterung von [addons.mozilla.org](https://addons.mozilla.org/) installieren.
2. `quick-profile-switch-host.exe` aus dem [neuesten Release](https://github.com/MasterCommunist/quick-profile-switch/releases/latest) herunterladen und doppelklicken. Es installiert sich für deinen Windows-Benutzer (ohne Administratorrechte) nach `%LOCALAPPDATA%\Programs\QuickProfileSwitch`. Windows SmartScreen warnt eventuell, weil die Datei nicht signiert ist: „Weitere Informationen“ → „Trotzdem ausführen“. Die Datei lässt sich mit `SHA256SUMS.txt` aus dem Release vergleichen.
3. Die Erweiterung in **jedem** Profil installieren, aus dem du wechseln willst.

**Deinstallation:** Windows-Einstellungen → Apps → Installierte Apps → Quick Profile Switch, und die Erweiterung in Firefox entfernen.

### Datenschutz

Es werden keine Daten erhoben oder versendet. Details: [PRIVACY.md](PRIVACY.md).

### Lizenz

[MIT](LICENSE). Das Hilfsprogramm enthält die Python-Laufzeit und weitere Komponenten unter eigenen Lizenzen, siehe [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md). Firefox ist eine Marke der Mozilla Foundation; dieses Projekt steht in keiner Verbindung zu Mozilla.
