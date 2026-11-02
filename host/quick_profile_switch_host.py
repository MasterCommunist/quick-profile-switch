"""Quick Profile Switch - native helper for the Firefox add-on (Windows).

Double-click        installs the helper for the current Windows user (no admin rights needed)
--uninstall         removes it again (also listed under Windows "Installed apps")
--quiet             no message boxes, for scripted installs

When Firefox starts it (native messaging), it lists the Firefox profiles and opens one.

Privacy: everything stays on this computer. The helper reads Firefox's own profile list,
starts Firefox and answers the add-on. It never uses the network and stores nothing
except a small local error log next to the program.
"""
import configparser
import ctypes
import glob
import json
import os
import re
import shutil
import sqlite3
import struct
import subprocess
import sys
import traceback
import winreg

APP_NAME = "Quick Profile Switch"
VERSION = "2.0.1"
HOST_NAME = "quick_profile_switch"
EXTENSION_ID = "{b6ab8238-405a-45f7-8639-3d49e9481d82}"
INSTALL_DIR = os.path.join(os.environ["LOCALAPPDATA"], "Programs", "QuickProfileSwitch")
EXE_NAME = "quick-profile-switch-host.exe"
MANIFEST_NAME = HOST_NAME + ".json"
NM_KEY = "Software\\Mozilla\\NativeMessagingHosts\\" + HOST_NAME
UNINSTALL_KEY = "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\QuickProfileSwitch"
FIREFOX_DIR = os.path.join(os.environ["APPDATA"], "Mozilla", "Firefox")
FALLBACK_EXES = [
    os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Mozilla Firefox", "firefox.exe"),
    os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Mozilla Firefox", "firefox.exe"),
]
UUID_RE = re.compile(r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}")

TEXTS = {
    "en": {
        "installed": "Quick Profile Switch is installed.\n\nYou can now switch profiles with the button in Firefox.\n"
                     "To remove the helper, use Windows Settings > Apps > Installed apps.",
        "uninstalled": "Quick Profile Switch helper has been removed.",
        "busy": "The helper is in use right now. Please close Firefox completely and try again.",
        "not_frozen": "Please run the built quick-profile-switch-host.exe to install.",
        "failed": "Installation failed:\n\n",
    },
    "de": {
        "installed": "Quick Profile Switch ist installiert.\n\nDu kannst jetzt mit dem Knopf in Firefox zwischen Profilen wechseln.\n"
                     "Zum Entfernen: Windows-Einstellungen > Apps > Installierte Apps.",
        "uninstalled": "Das Hilfsprogramm von Quick Profile Switch wurde entfernt.",
        "busy": "Das Hilfsprogramm wird gerade benutzt. Bitte Firefox ganz schließen und es noch einmal versuchen.",
        "not_frozen": "Zum Installieren bitte die fertige quick-profile-switch-host.exe starten.",
        "failed": "Installation fehlgeschlagen:\n\n",
    },
}


def text(key):
    german = (ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF) == 0x07
    return TEXTS["de" if german else "en"][key]


def message(body, error=False, quiet=False):
    if not quiet:
        ctypes.windll.user32.MessageBoxW(None, body, APP_NAME, 0x10 if error else 0x40)


def log_error(details):
    # Nur lokal, nur Fehler, klein gehalten
    path = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "error.log")
    try:
        if os.path.exists(path) and os.path.getsize(path) > 50_000:
            os.remove(path)
        with open(path, "a", encoding="utf-8") as f:
            f.write(details.rstrip() + "\n")
    except OSError:
        pass


# ---------- Installation ----------

def install(quiet):
    if not getattr(sys, "frozen", False):
        message(text("not_frozen"), error=True, quiet=quiet)
        return 1
    target = os.path.join(INSTALL_DIR, EXE_NAME)
    try:
        os.makedirs(INSTALL_DIR, exist_ok=True)
        if os.path.normcase(os.path.abspath(sys.executable)) != os.path.normcase(target):
            shutil.copy2(sys.executable, target)
        manifest_path = os.path.join(INSTALL_DIR, MANIFEST_NAME)
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({"name": HOST_NAME, "description": APP_NAME + " helper", "path": target,
                       "type": "stdio", "allowed_extensions": [EXTENSION_ID]}, f, indent=2)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, NM_KEY) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, manifest_path)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as key:
            for name, value in (("DisplayName", APP_NAME), ("DisplayVersion", VERSION), ("Publisher", APP_NAME),
                                ("DisplayIcon", target), ("InstallLocation", INSTALL_DIR),
                                ("UninstallString", f'"{target}" --uninstall'),
                                ("QuietUninstallString", f'"{target}" --uninstall --quiet')):
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, os.path.getsize(target) // 1024)
    except PermissionError:
        message(text("busy"), error=True, quiet=quiet)
        return 1
    except OSError as e:
        message(text("failed") + str(e), error=True, quiet=quiet)
        return 1
    message(text("installed"), quiet=quiet)
    return 0


def uninstall(quiet):
    for key in (NM_KEY, UNINSTALL_KEY):
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key)
        except FileNotFoundError:
            pass
    for name in (MANIFEST_NAME, "error.log"):
        try:
            os.remove(os.path.join(INSTALL_DIR, name))
        except FileNotFoundError:
            pass
    target = os.path.join(INSTALL_DIR, EXE_NAME)
    if os.path.normcase(os.path.abspath(sys.executable)) == os.path.normcase(target):
        # Ein laufendes Programm kann sich nicht selbst löschen: kurz nach dem Beenden aufräumen lassen
        # Windows gibt die gelöschte .exe teils verzögert frei, darum vor dem Ordner-Löschen noch einmal warten
        subprocess.Popen(f'cmd /c ping 127.0.0.1 -n 3 > nul & del /q "{target}" & ping 127.0.0.1 -n 3 > nul'
                         f' & rmdir /s /q "{INSTALL_DIR}"',
                         cwd=os.environ.get("SystemRoot", "C:\\Windows"),
                         creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
    else:
        try:
            os.remove(target)
            os.rmdir(INSTALL_DIR)
        except OSError:
            pass
    message(text("uninstalled"), quiet=quiet)
    return 0


# ---------- Native Messaging ----------

def read_message():
    raw = sys.stdin.buffer.read(4)
    if len(raw) < 4:
        sys.exit(0)
    length = struct.unpack("<I", raw)[0]
    return json.loads(sys.stdin.buffer.read(length).decode("utf-8"))


def send_message(obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(data)) + data)
    sys.stdout.buffer.flush()


def profile_path(rel_or_abs, is_relative=True):
    # Schreibweise beibehalten: Firefox erkennt ein laufendes Profil am exakten Pfad
    return os.path.normpath(os.path.join(FIREFOX_DIR, rel_or_abs) if is_relative else rel_or_abs)


def same_path(a, b):
    return os.path.normcase(os.path.normpath(a)) == os.path.normcase(os.path.normpath(b))


def query_profile_db(db):
    # Bei laufendem Firefox normal lesen; falls gesperrt, den letzten gespeicherten Stand nehmen
    for mode in ("mode=ro", "immutable=1"):
        try:
            con = sqlite3.connect(f"file:{db.replace(os.sep, '/')}?{mode}", uri=True)
            rows = con.execute("select path, name, themeFg, themeBg from Profiles order by id").fetchall()
            con.close()
            return rows
        except sqlite3.Error:
            continue
    return []


def list_profiles():
    profiles = {}
    # Profile aus Firefox' Profil-Manager (Namen und Farben)
    for db in glob.glob(os.path.join(FIREFOX_DIR, "Profile Groups", "*.sqlite")):
        for path, name, fg, bg in query_profile_db(db):
            p = profile_path(path)
            profiles[os.path.normcase(p)] = {"name": name, "path": p, "fg": fg, "bg": bg}
    # Klassische Profile aus profiles.ini, falls sie nicht im Profil-Manager stehen
    ini = configparser.ConfigParser(interpolation=None)
    ini.read(os.path.join(FIREFOX_DIR, "profiles.ini"), encoding="utf-8")
    for section in ini.sections():
        if section.startswith("Profile") and ini.has_option(section, "Path"):
            p = profile_path(ini[section]["Path"], ini[section].get("IsRelative", "1") == "1")
            profiles.setdefault(os.path.normcase(p), {"name": ini[section].get("Name", section), "path": p, "fg": None, "bg": None})
    return [p for p in profiles.values() if os.path.isdir(p["path"])]


def is_current(profile, uuid):
    # Firefox legt die interne Kennung der Erweiterung in der prefs.js des Profils ab, in dem sie läuft
    if not UUID_RE.fullmatch(uuid):
        return False
    try:
        with open(os.path.join(profile["path"], "prefs.js"), encoding="utf-8", errors="replace") as f:
            return uuid in f.read()
    except OSError:
        return False


def firefox_exe(profile):
    compat = configparser.ConfigParser(interpolation=None)
    compat.read(os.path.join(profile["path"], "compatibility.ini"), encoding="utf-8")
    candidates = []
    if compat.has_option("Compatibility", "LastPlatformDir"):
        candidates.append(os.path.join(compat["Compatibility"]["LastPlatformDir"], "firefox.exe"))
    for exe in candidates + FALLBACK_EXES:
        if os.path.isfile(exe):
            return exe
    raise FileNotFoundError("firefox.exe not found")


def firefox_environment():
    # PyInstaller setzt im eigenen Prozess Variablen, die auf seinen temporären Ordner zeigen. Erbt Firefox sie,
    # sucht jedes später von diesem Firefox gestartete Hilfsprogramm Python im längst gelöschten Ordner
    # ("Failed to load Python DLL"). Darum entfernen und zusätzlich PyInstallers Reset-Schalter setzen.
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("_PYI_", "_MEIPASS"))}
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    return env


def open_profile(profile):
    exe = firefox_exe(profile)
    args = [exe, "--profile", profile["path"]]
    base = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    # Arbeitsverzeichnis = Firefox-Ordner; sonst erbt Firefox den Ordner des Hilfsprogramms und sperrt ihn
    # (Deinstallation könnte ihn dann nicht löschen)
    common = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True,
                  cwd=os.path.dirname(exe), env=firefox_environment())
    try:
        # Aus Firefox' Prozessgruppe lösen, damit das neue Fenster nicht mit diesem Programm beendet wird
        subprocess.Popen(args, creationflags=base | subprocess.CREATE_BREAKAWAY_FROM_JOB, **common)
    except OSError:
        subprocess.Popen(args, creationflags=base, **common)


def messaging():
    try:
        msg = read_message()
        uuid = msg.get("uuid", "")
        profiles = list_profiles()
        for p in profiles:
            p["current"] = bool(uuid) and is_current(p, uuid)
        if msg.get("cmd") == "list":
            send_message({"profiles": profiles})
        elif msg.get("cmd") == "open":
            target = next((p for p in profiles if same_path(p["path"], msg.get("path", ""))), None)
            if target is None:
                send_message({"error": "Unknown profile"})
                return 1
            open_profile(target)
            send_message({"ok": True, "opened": target["name"]})
        else:
            send_message({"error": f"Unknown command: {msg.get('cmd')}"})
    except Exception as e:  # Fehler an die Erweiterung melden statt stumm abzubrechen
        log_error(traceback.format_exc())
        send_message({"error": f"{type(e).__name__}: {e}"})
        return 1
    return 0


def main():
    args = sys.argv[1:]
    # Firefox übergibt den Pfad des Manifests und die ID der Erweiterung
    if EXTENSION_ID in args or any(a.lower().endswith(".json") for a in args):
        return messaging()
    quiet = "--quiet" in args
    return uninstall(quiet) if "--uninstall" in args else install(quiet)


if __name__ == "__main__":
    sys.exit(main())
