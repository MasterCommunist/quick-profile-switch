"""Durchsucht Veröffentlichungs-Dateien nach persönlichen Daten (auch in gepackten .exe-, .zip- und .xpi-Inhalten).

Aufruf: python tools/scan_private.py <Datei oder Ordner> ...
Die Suchbegriffe (eine Zeile pro Begriff) liegen bewusst AUSSERHALB des Repositorys in ../../private_terms.txt (also im Ordner neben dem Repository),
damit die persönlichen Begriffe selbst nie veröffentlicht werden.
"""
import io
import os
import sys
import zipfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
TERMS_FILE = os.environ.get("QPS_PRIVATE_TERMS") or os.path.join(os.path.dirname(os.path.dirname(HERE)), "private_terms.txt")


ALLOWED = []  # Zeilen mit "!" am Anfang: bekannte harmlose Fundstellen, z. B. fremde Namen in Python-Quellenangaben


def load_terms():
    with open(TERMS_FILE, encoding="utf-8") as f:
        lines = [t.strip() for t in f if t.strip() and not t.startswith("#")]
    ALLOWED.extend(a[1:].encode("utf-8").lower() for a in lines if a.startswith("!"))
    variants = set()
    for t in (t for t in lines if not t.startswith("!")):
        for v in (t, t.lower(), t.upper()):
            variants.add(v.encode("utf-8"))
            variants.add(v.encode("utf-16-le"))
    return variants


def hits(data, terms):
    low = data.lower()
    for allowed in ALLOWED:
        low = low.replace(allowed, b"")
    data = low
    return sorted({t.decode("utf-8", "ignore") if b"\x00" not in t else t.decode("utf-16-le", "ignore") + " (UTF-16)"
                   for t in terms if t in data or t.lower() in low})


def pyinstaller_parts(path):
    # Eingebettete Teile einer PyInstaller-.exe entpacken (CArchive und PYZ)
    try:
        from PyInstaller.archive.readers import CArchiveReader, ZlibArchiveReader
    except ImportError:
        return []
    parts = []
    try:
        arch = CArchiveReader(path)
    except Exception:
        return []
    for name in arch.toc:
        try:
            data = arch.extract(name)
        except Exception:
            continue
        if data is None:
            continue
        parts.append((name, data))
        if name.endswith(".pyz") or data[:4] == b"PYZ\x00":
            tmp = os.path.join(os.environ.get("TEMP", "."), "_scan_tmp.pyz")
            with open(tmp, "wb") as f:
                f.write(data)
            try:
                pyz = ZlibArchiveReader(tmp)
                for mod in pyz.toc:
                    try:
                        parts.append((f"{name}/{mod}", pyz.extract(mod, raw=True)))
                    except Exception:
                        pass
            finally:
                os.remove(tmp)
    return parts


def scan_bytes(label, data, terms, found):
    h = hits(data, terms)
    if h:
        found.append((label, h))
    if data[:2] == b"PK":
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for n in z.namelist():
                    scan_bytes(f"{label}!{n}", z.read(n), terms, found)
        except zipfile.BadZipFile:
            pass


def scan_path(path, terms, found):
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for f in files:
                scan_path(os.path.join(root, f), terms, found)
        return
    data = open(path, "rb").read()
    scan_bytes(path, data, terms, found)
    if path.lower().endswith(".exe"):
        for name, part in pyinstaller_parts(path):
            if isinstance(part, bytes):
                for blob in (part, safe_unzlib(part)):
                    if blob:
                        scan_bytes(f"{path}::{name}", blob, terms, found)


def safe_unzlib(data):
    try:
        return zlib.decompress(data)
    except Exception:
        return None


if __name__ == "__main__":
    terms = load_terms()
    found = []
    for p in sys.argv[1:]:
        scan_path(p, terms, found)
    for label, h in found:
        print(f"TREFFER {label}: {', '.join(h)}")
    print(f"{len(found)} Treffer" if found else "Keine persönlichen Daten gefunden")
