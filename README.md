# Cleandahouse

Windows tray app that automatically moves files from your Downloads folder to organized subfolders — after a configurable delay.

## Features

- **Multiple source folders** — monitor Downloads, Personal, Work, or any folder you want
- **Delay-based moving** — files stay put for X minutes/hours/days/weeks before being moved
- **Fully configurable rules** — define your own conditions (extension, name prefix, name contains) and destinations
- **Per-folder organization** — each monitored folder gets its own subfolder structure (e.g. `Downloads/PDF`, `Work/PDF`)
- **System tray** — runs silently in the background, near the clock
- **GUI settings** — right-click the tray icon → "Configurar reglas"
- **Duplicate handling** — if a file already exists in the destination, the older version goes to `revisar/`
- **Crash-safe** — uses `mtime` as the file's age reference; restarts pick up from where they left off
- **Distributable as .exe** — no Python required for end users

---

## Quickstart (Python)

```bash
git clone https://github.com/NecroLeader/Cleandahouse.git
cd Cleandahouse
pip install -r requirements.txt
pythonw organizer.py
```

> Use `python organizer.py` to see live logs in the console.

---

## Quickstart (executable)

1. Download `Cleandahouse.exe` and `config.json` from [Releases](../../releases)
2. Put both files in the same folder
3. Double-click `Cleandahouse.exe`
4. A folder icon appears near the system clock

---

## Auto-start with Windows

Run `instalar_inicio.bat` — creates a shortcut in the Windows Startup folder.
Run `desinstalar_inicio.bat` to remove it.

---

## Configuring monitored folders

Right-click the tray icon → **Configurar reglas** → section **"Carpetas monitoreadas"**

Add any folder you want to watch. Each folder is organized independently — if a rule sends `*.pdf` to `PDF`, the subfolder is created inside each monitored folder.

Example with three monitored folders and one rule (`*.pdf → PDF`):
```
Downloads/PDF/
Personal/PDF/
Work/PDF/
```

---

## Configuring rules

Right-click the tray icon → **Configurar reglas**

Each rule has:
- **Name** — label for the rule (e.g. "Audio")
- **Conditions** (any match triggers the rule):
  - Extensions: `.mp3 .wav .flac`
  - Name starts with: `factura_, invoice-`
  - Name contains: `recibo, comprobante`
- **Destination folder** — relative to Downloads (e.g. `Media/Audio`, `Trabajo/Facturas`)

You can also create destination folders directly from the rule editor.

Rules are evaluated top-to-bottom — first match wins.

### Manual editing (`config.json`)

```json
{
  "delay_value": 1,
  "delay_unit": "dias",
  "rules": [
    {
      "name": "Audio",
      "enabled": true,
      "conditions": {
        "extensions": [".mp3", ".wav", ".flac"],
        "name_starts": [],
        "name_contains": []
      },
      "dest": "Media/Audio"
    }
  ]
}
```

`delay_unit` options: `minutos` · `horas` · `dias` · `semanas`

---

## Build your own .exe

```bash
build.bat
```

Output: `dist/Cleandahouse.exe` + `dist/config.json`
Distribute both files together. The user edits `config.json` for their own rules.

---

## How it works

```
file lands in Downloads
        ↓
organizer detects it → records in pending.json with file's mtime
        ↓
every 60s: checks if (now - mtime) >= delay
        ↓  yes
moves to configured subfolder
```

Files with no matching rule stay in Downloads untouched.

---

## License

MIT
