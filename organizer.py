#!/usr/bin/env python3
"""
Cleandahouse — Downloads Organizer
Mueve archivos de Downloads a carpetas configurables tras un delay.

Uso: pythonw organizer.py   (tray, sin consola)
     python  organizer.py   (con log en consola para debug)
"""

import json
import sys
import time
import shutil
import logging
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pystray
from PIL import Image, ImageDraw

# Importacion adelantada para que PyInstaller la detecte
from gui import SettingsWindow

# ---------------------------------------------------------------------------
# PATHS  (funciona tanto en .py como en .exe de PyInstaller)
# ---------------------------------------------------------------------------

if getattr(sys, "frozen", False):
    HERE = Path(sys.executable).parent
else:
    HERE = Path(__file__).parent

DOWNLOADS    = Path.home() / "Downloads"
CONFIG_FILE  = HERE / "config.json"
PENDING_FILE = HERE / "pending.json"
LOG_FILE     = HERE / "cleandahouse.log"

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "delay_value": 1,
    "delay_unit": "dias",
    "rules": [
        {
            "name": "Audio",
            "enabled": True,
            "conditions": {
                "extensions": [".mp3", ".m4a", ".wav", ".ogg", ".flac", ".aac"],
                "name_starts": [],
                "name_contains": [],
            },
            "dest": "Media/Audio",
        },
        {
            "name": "Video",
            "enabled": True,
            "conditions": {
                "extensions": [".mp4", ".mkv", ".avi", ".mov", ".wmv"],
                "name_starts": [],
                "name_contains": [],
            },
            "dest": "Media/Video",
        },
        {
            "name": "Imagenes",
            "enabled": True,
            "conditions": {
                "extensions": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"],
                "name_starts": [],
                "name_contains": [],
            },
            "dest": "Media/Imagenes",
        },
        {
            "name": "Instaladores",
            "enabled": True,
            "conditions": {
                "extensions": [".exe", ".msi", ".iso", ".apk", ".dmg", ".pkg"],
                "name_starts": [],
                "name_contains": [],
            },
            "dest": "Instaladores",
        },
        {
            "name": "Documentos",
            "enabled": True,
            "conditions": {
                "extensions": [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".odt"],
                "name_starts": [],
                "name_contains": [],
            },
            "dest": "Documentos",
        },
    ],
}

_config: dict = {}


def load_config() -> dict:
    global _config
    if CONFIG_FILE.exists():
        try:
            _config = {**DEFAULT_CONFIG, **json.loads(CONFIG_FILE.read_text(encoding="utf-8"))}
        except Exception:
            _config = DEFAULT_CONFIG.copy()
    else:
        _config = DEFAULT_CONFIG.copy()
        CONFIG_FILE.write_text(json.dumps(_config, indent=2, ensure_ascii=False), encoding="utf-8")
    return _config


def delay_seconds() -> float:
    units = {"minutos": 60, "horas": 3_600, "dias": 86_400, "semanas": 604_800}
    return _config.get("delay_value", 1) * units.get(_config.get("delay_unit", "dias"), 86_400)


def delay_label() -> str:
    return f"{_config.get('delay_value', 1)} {_config.get('delay_unit', 'dias')}"

# ---------------------------------------------------------------------------
# CLASIFICADOR  (lee reglas del config en cada llamada)
# ---------------------------------------------------------------------------

SKIP_NAMES = {"desktop.ini", "thumbs.db", ".ds_store"}
SKIP_EXT   = {".tmp", ".crdownload", ".part", ".download"}


def classify(filename: str) -> str | None:
    """Retorna carpeta destino o None si ninguna regla aplica."""
    name_low = filename.lower()
    ext = Path(filename).suffix.lower()

    for rule in _config.get("rules", []):
        if not rule.get("enabled", True):
            continue
        conds = rule.get("conditions", {})

        if ext in [e.lower() for e in conds.get("extensions", [])]:
            return rule["dest"]
        for prefix in conds.get("name_starts", []):
            if prefix and name_low.startswith(prefix.lower()):
                return rule["dest"]
        for substr in conds.get("name_contains", []):
            if substr and substr.lower() in name_low:
                return rule["dest"]
    return None


def is_eligible(path: Path) -> bool:
    return (
        path.is_file()
        and path.parent == DOWNLOADS
        and path.name.lower() not in SKIP_NAMES
        and path.suffix.lower() not in SKIP_EXT
    )

# ---------------------------------------------------------------------------
# LOGGER
# ---------------------------------------------------------------------------

log = logging.getLogger("cleandahouse")
log.setLevel(logging.INFO)

_fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-5s  %(message)s", "%Y-%m-%d %H:%M:%S"))
log.addHandler(_fh)

if not getattr(sys, "frozen", False):
    _ch = logging.StreamHandler()
    _ch.setFormatter(logging.Formatter("%(asctime)s  %(message)s", "%H:%M:%S"))
    log.addHandler(_ch)

# ---------------------------------------------------------------------------
# PENDING
# ---------------------------------------------------------------------------

_pending_lock = threading.Lock()


def load_pending() -> dict:
    with _pending_lock:
        try:
            return json.loads(PENDING_FILE.read_text(encoding="utf-8")) if PENDING_FILE.exists() else {}
        except Exception:
            return {}


def save_pending(data: dict):
    with _pending_lock:
        PENDING_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def add_to_pending(path: Path):
    if not is_eligible(path):
        return
    pending = load_pending()
    if path.name not in pending:
        ts = datetime.fromtimestamp(path.stat().st_mtime).isoformat()
        pending[path.name] = ts
        save_pending(pending)
        log.info(f"PENDIENTE  {path.name}  (delay: {delay_label()})")

# ---------------------------------------------------------------------------
# MOVER
# ---------------------------------------------------------------------------

def wait_stable(path: Path, timeout: int = 60) -> bool:
    deadline = time.time() + timeout
    prev = -1
    while time.time() < deadline:
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            return False
        if size == prev:
            return True
        prev = size
        time.sleep(1)
    return path.exists()


def move_file(src: Path):
    if not is_eligible(src):
        return
    dest_folder = classify(src.name)
    if dest_folder is None:
        return  # ninguna regla aplica → se queda

    dest_dir = DOWNLOADS / dest_folder
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name

    if dest.exists():
        revisar = DOWNLOADS / "revisar"
        revisar.mkdir(exist_ok=True)
        src_t, dest_t = src.stat().st_mtime, dest.stat().st_mtime
        if src_t > dest_t:
            old = revisar / dest.name
            if old.exists():
                old = revisar / f"{dest.stem}_{int(dest_t)}{dest.suffix}"
            shutil.move(str(dest), str(old))
        else:
            dup = revisar / src.name
            if dup.exists():
                dup = revisar / f"{src.stem}_{int(src_t)}{src.suffix}"
            shutil.move(str(src), str(dup))
            log.info(f"DUPLICADO  {src.name}  -> revisar/")
            return

    try:
        shutil.move(str(src), str(dest))
        log.info(f"MOVIDO     {src.name}  ->  {dest_dir.relative_to(DOWNLOADS)}/")
    except Exception as e:
        log.error(f"ERROR      {src.name}  ({e})")

# ---------------------------------------------------------------------------
# LOOP PRINCIPAL DE MOVIMIENTO
# ---------------------------------------------------------------------------

def check_and_move():
    load_config()
    delay = delay_seconds()
    pending = load_pending()
    changed = False
    now = datetime.now()

    for filename, ts_str in list(pending.items()):
        path = DOWNLOADS / filename
        if not path.exists():
            del pending[filename]
            changed = True
            continue
        try:
            age = (now - datetime.fromisoformat(ts_str)).total_seconds()
        except ValueError:
            del pending[filename]
            changed = True
            continue
        if age >= delay:
            move_file(path)
            del pending[filename]
            changed = True

    if changed:
        save_pending(pending)


def mover_loop(stop_event: threading.Event, icon: pystray.Icon):
    # Al arrancar: registrar archivos ya presentes usando su mtime
    pending = load_pending()
    added = 0
    for f in DOWNLOADS.iterdir():
        if is_eligible(f) and f.name not in pending:
            pending[f.name] = datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            added += 1
    if added:
        save_pending(pending)
        log.info(f"INICIO     {added} archivos registrados con su fecha de descarga")

    while not stop_event.is_set():
        check_and_move()
        try:
            n = len(load_pending())
            icon.title = f"Cleandahouse — {n} pendiente{'s' if n != 1 else ''} | delay: {delay_label()}"
        except Exception:
            pass
        stop_event.wait(60)

# ---------------------------------------------------------------------------
# WATCHDOG
# ---------------------------------------------------------------------------

class DownloadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        time.sleep(2)
        if wait_stable(path):
            add_to_pending(path)

    def on_moved(self, event):
        if event.is_directory:
            return
        path = Path(event.dest_path)
        if path.suffix.lower() not in SKIP_EXT:
            time.sleep(1)
            add_to_pending(path)

# ---------------------------------------------------------------------------
# ICONO TRAY
# ---------------------------------------------------------------------------

def create_icon_image() -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 20, 60, 56], radius=6, fill=(52, 152, 219))
    d.rounded_rectangle([4, 14, 28, 24], radius=4, fill=(41, 128, 185))
    d.polygon([(32, 28), (44, 28), (38, 40)], fill="white")
    d.rectangle([36, 40, 40, 48], fill="white")
    return img


def generate_icon_ico() -> Path:
    """Genera icon.ico para el build de PyInstaller."""
    path = HERE / "icon.ico"
    img = create_icon_image().resize((256, 256)).convert("RGBA")
    img.save(path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    return path

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Cleandahouse.Organizer")
    except Exception:
        pass

    load_config()
    generate_icon_ico()  # necesario para el ícono de la ventana de settings

    stop_event        = threading.Event()
    settings_event    = threading.Event()

    observer = Observer()
    observer.schedule(DownloadHandler(), str(DOWNLOADS), recursive=False)
    observer.daemon = True
    observer.start()

    def on_settings(icon, item):
        settings_event.set()

    def on_quit(icon, item):
        stop_event.set()
        icon.stop()

    def on_open(icon, item):
        subprocess.Popen(["explorer", str(DOWNLOADS)])

    def on_log(icon, item):
        subprocess.Popen(["notepad", str(LOG_FILE)])

    icon = pystray.Icon(
        name="cleandahouse",
        icon=create_icon_image(),
        title=f"Cleandahouse | delay: {delay_label()}",
        menu=pystray.Menu(
            pystray.MenuItem("Abrir Downloads",     on_open,     default=True),
            pystray.MenuItem("Configurar reglas",   on_settings),
            pystray.MenuItem("Ver log",             on_log),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Detener",             on_quit),
        ),
    )

    threading.Thread(
        target=mover_loop, args=(stop_event, icon), daemon=True
    ).start()

    icon.run_detached()
    log.info(f"Cleandahouse activo | delay: {delay_label()} | {DOWNLOADS}")

    # Hilo principal: maneja la GUI cuando se solicita
    try:
        while not stop_event.is_set():
            if settings_event.is_set():
                settings_event.clear()
                win = SettingsWindow(CONFIG_FILE, DOWNLOADS)
                win.mainloop()
                try:
                    win.destroy()
                except Exception:
                    pass
            time.sleep(0.1)
    except KeyboardInterrupt:
        stop_event.set()
        icon.stop()
    finally:
        observer.stop()
        observer.join()
        log.info("Cleandahouse detenido.")


if __name__ == "__main__":
    main()
