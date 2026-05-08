"""
gui.py — Ventana de configuración de Cleandahouse
"""

import sys
import json
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

UNIT_OPTIONS = ["minutos", "horas", "dias", "semanas"]

_HERE = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent


def _apply_icon(window):
    """Aplica icon.ico a la ventana — barra de título Y barra de tareas de Windows."""
    ico = _HERE / "icon.ico"
    if not ico.exists():
        return
    ico_str = str(ico)

    def do_apply():
        # 1) Ícono en barra de título (tkinter nativo)
        try:
            window.iconbitmap(ico_str)
        except Exception:
            pass
        # 2) Ícono en barra de tareas via Win32 API
        try:
            import ctypes
            IMAGE_ICON   = 1
            LR_LOADFROMFILE = 0x00000010
            LR_DEFAULTSIZE  = 0x00000040
            WM_SETICON   = 0x0080
            hicon = ctypes.windll.user32.LoadImageW(
                None, ico_str, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE
            )
            if hicon:
                hwnd = window.winfo_id()
                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, 1, hicon)  # ICON_BIG
                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, 0, hicon)  # ICON_SMALL
        except Exception:
            pass

    # Delay necesario: customtkinter pisa el ícono durante su inicialización
    window.after(250, do_apply)


# ---------------------------------------------------------------------------
# Editor de regla (modal)
# ---------------------------------------------------------------------------

class RuleEditor(ctk.CTkToplevel):
    def __init__(self, parent, downloads: Path, rule: dict = None):
        super().__init__(parent)
        self.downloads = downloads
        self.result: dict | None = None

        self.title("Editar regla" if rule else "Nueva regla")
        self.geometry("480x430")
        self.resizable(False, False)
        self.lift()
        self.focus_force()
        self.grab_set()
        _apply_icon(self)

        self._build(rule or {})

    def _build(self, rule: dict):
        pad = {"padx": 16, "pady": 3}
        conds = rule.get("conditions", {})

        ctk.CTkLabel(self, text="Nombre de la regla", anchor="w").pack(fill="x", **pad)
        self.name_var = ctk.StringVar(value=rule.get("name", ""))
        ctk.CTkEntry(self, textvariable=self.name_var).pack(fill="x", **pad)

        ctk.CTkLabel(
            self, text="Condiciones — se mueve si cumple ALGUNA:",
            anchor="w", font=ctk.CTkFont(weight="bold")
        ).pack(fill="x", padx=16, pady=(12, 2))

        ctk.CTkLabel(self, text="Extensiones  (ej: .mp3 .wav .flac)", anchor="w").pack(fill="x", **pad)
        self.ext_var = ctk.StringVar(value=" ".join(conds.get("extensions", [])))
        ctk.CTkEntry(self, textvariable=self.ext_var, placeholder_text=".pdf .docx .xlsx").pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Nombre empieza con  (sep. por comas)", anchor="w").pack(fill="x", **pad)
        self.starts_var = ctk.StringVar(value=", ".join(conds.get("name_starts", [])))
        ctk.CTkEntry(self, textvariable=self.starts_var, placeholder_text="factura_, invoice-, cv-").pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Nombre contiene  (sep. por comas)", anchor="w").pack(fill="x", **pad)
        self.contains_var = ctk.StringVar(value=", ".join(conds.get("name_contains", [])))
        ctk.CTkEntry(self, textvariable=self.contains_var, placeholder_text="recibo, comprobante").pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Carpeta destino", anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=16, pady=(12, 2))

        dest_row = ctk.CTkFrame(self, fg_color="transparent")
        dest_row.pack(fill="x", **pad)
        self.dest_var = ctk.StringVar(value=rule.get("dest", ""))
        ctk.CTkEntry(dest_row, textvariable=self.dest_var, placeholder_text="Carpeta o subcarpeta/anidada").pack(side="left", fill="x", expand=True)
        ctk.CTkButton(dest_row, text="Buscar", width=74, command=self._browse).pack(side="left", padx=(6, 0))

        ctk.CTkButton(self, text="+ Crear carpeta en Downloads ahora", command=self._create_folder).pack(fill="x", **pad)

        sep = ctk.CTkFrame(self, height=1, fg_color="gray50")
        sep.pack(fill="x", padx=16, pady=(12, 4))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=4)
        ctk.CTkButton(btn_row, text="Cancelar", fg_color="gray40", hover_color="gray30",
                      command=self.destroy).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ctk.CTkButton(btn_row, text="Guardar regla", command=self._save).pack(side="left", expand=True, fill="x", padx=(4, 0))

    def _browse(self):
        folder = filedialog.askdirectory(initialdir=self.downloads, title="Seleccionar carpeta destino", parent=self)
        if folder:
            try:
                rel = Path(folder).relative_to(self.downloads)
                self.dest_var.set(str(rel).replace("\\", "/"))
            except ValueError:
                self.dest_var.set(folder)

    def _create_folder(self):
        dest = self.dest_var.get().strip()
        if not dest:
            messagebox.showwarning("Atención", "Escribí el nombre de la carpeta primero.", parent=self)
            return
        folder = self.downloads / dest
        folder.mkdir(parents=True, exist_ok=True)
        messagebox.showinfo("Carpeta creada", f"{folder}", parent=self)

    def _save(self):
        name = self.name_var.get().strip()
        dest = self.dest_var.get().strip()

        if not name:
            messagebox.showerror("Error", "La regla necesita un nombre.", parent=self)
            return
        if not dest:
            messagebox.showerror("Error", "Definí una carpeta destino.", parent=self)
            return

        raw_exts = self.ext_var.get().replace(",", " ")
        extensions = []
        for e in raw_exts.split():
            e = e.strip()
            if e:
                extensions.append(e if e.startswith(".") else f".{e}")

        name_starts = [s.strip() for s in self.starts_var.get().split(",") if s.strip()]
        name_contains = [s.strip() for s in self.contains_var.get().split(",") if s.strip()]

        if not extensions and not name_starts and not name_contains:
            messagebox.showerror("Error", "Agregá al menos una condición.", parent=self)
            return

        self.result = {
            "name": name,
            "enabled": True,
            "conditions": {
                "extensions": extensions,
                "name_starts": name_starts,
                "name_contains": name_contains,
            },
            "dest": dest,
        }
        self.destroy()


# ---------------------------------------------------------------------------
# Ventana principal de configuración
# ---------------------------------------------------------------------------

class SettingsWindow(ctk.CTk):
    def __init__(self, config_path: Path, downloads: Path):
        super().__init__()
        self.config_path = config_path
        self.downloads = downloads

        self.title("Cleandahouse — Configuración")
        self.geometry("580x540")
        self.minsize(480, 420)
        self.protocol("WM_DELETE_WINDOW", self.quit)  # cierre limpio via X
        _apply_icon(self)

        self._load()
        self._build()

    # --- data ----------------------------------------------------------------

    def _load(self):
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        self.delay_value = data.get("delay_value", 1)
        self.delay_unit  = data.get("delay_unit", "dias")
        self.rules: list[dict] = data.get("rules", [])

    # --- layout --------------------------------------------------------------

    def _build(self):
        # Delay
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=16, pady=(16, 4))
        ctk.CTkLabel(top, text="Mover archivos después de:", anchor="w").pack(side="left", padx=(8, 6))
        self.delay_val_var = ctk.StringVar(value=str(self.delay_value))
        ctk.CTkEntry(top, textvariable=self.delay_val_var, width=52).pack(side="left", padx=2)
        self.delay_unit_var = ctk.StringVar(value=self.delay_unit)
        ctk.CTkOptionMenu(top, variable=self.delay_unit_var, values=UNIT_OPTIONS, width=130).pack(side="left", padx=4)

        # Rules header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 2))
        ctk.CTkLabel(hdr, text="Reglas", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkButton(hdr, text="+ Nueva regla", width=110, command=self._add_rule).pack(side="right")

        # Rules list
        self.rules_frame = ctk.CTkScrollableFrame(self, label_text="")
        self.rules_frame.pack(fill="both", expand=True, padx=16, pady=4)
        self._render_rules()

        # Save
        ctk.CTkButton(self, text="Guardar y aplicar", height=38, command=self._save).pack(
            fill="x", padx=16, pady=(4, 16)
        )

    def _render_rules(self):
        for w in self.rules_frame.winfo_children():
            w.destroy()

        if not self.rules:
            ctk.CTkLabel(
                self.rules_frame,
                text="Sin reglas todavía.\nHacé clic en '+ Nueva regla' para empezar.",
                text_color="gray"
            ).pack(pady=30)
            return

        for i, rule in enumerate(self.rules):
            self._rule_row(i, rule)

    def _rule_row(self, i: int, rule: dict):
        row = ctk.CTkFrame(self.rules_frame)
        row.pack(fill="x", pady=2)

        var = ctk.BooleanVar(value=rule.get("enabled", True))

        def make_toggle(idx, v):
            def _t():
                self.rules[idx]["enabled"] = v.get()
            return _t

        ctk.CTkSwitch(row, text="", variable=var, width=44,
                      command=make_toggle(i, var)).pack(side="left", padx=(8, 4), pady=6)

        conds = rule.get("conditions", {})
        parts = []
        if conds.get("extensions"):
            parts.append(" ".join(conds["extensions"]))
        if conds.get("name_starts"):
            parts.append("empieza: " + ", ".join(conds["name_starts"]))
        if conds.get("name_contains"):
            parts.append("contiene: " + ", ".join(conds["name_contains"]))
        summary = "  |  ".join(parts) if parts else "(sin condiciones)"

        # Botones PRIMERO (side=right), así el label expansivo nunca los empuja
        btns = ctk.CTkFrame(row, fg_color="transparent")
        btns.pack(side="right", padx=6)

        def make_edit(idx):
            def _e():
                self._edit_rule(idx)
            return _e

        def make_delete(idx):
            def _d():
                self._delete_rule(idx)
            return _d

        ctk.CTkButton(btns, text="Editar", width=64, command=make_edit(i)).pack(side="left", padx=(0, 4))
        ctk.CTkButton(btns, text="Borrar", width=64,
                      fg_color="#c0392b", hover_color="#922b21",
                      command=make_delete(i)).pack(side="left")

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, pady=4)
        ctk.CTkLabel(info, text=f"{rule['name']}  →  {rule['dest']}",
                     anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=4)
        ctk.CTkLabel(info, text=summary, anchor="w",
                     text_color="gray", font=ctk.CTkFont(size=11)).pack(fill="x", padx=4)

    # --- actions -------------------------------------------------------------

    def _add_rule(self):
        dlg = RuleEditor(self, self.downloads)
        self.wait_window(dlg)
        if dlg.result:
            self.rules.append(dlg.result)
            self._render_rules()

    def _edit_rule(self, idx: int):
        dlg = RuleEditor(self, self.downloads, self.rules[idx])
        self.wait_window(dlg)
        if dlg.result:
            dlg.result["enabled"] = self.rules[idx].get("enabled", True)
            self.rules[idx] = dlg.result
            self._render_rules()

    def _delete_rule(self, idx: int):
        name = self.rules[idx]["name"]
        if messagebox.askyesno("Borrar regla", f"¿Borrar la regla «{name}»?", parent=self):
            self.rules.pop(idx)
            self._render_rules()

    def _save(self):
        try:
            val = int(self.delay_val_var.get())
            assert val > 0
        except Exception:
            messagebox.showerror("Error", "El delay debe ser un número mayor a 0.", parent=self)
            return

        config = {
            "delay_value": val,
            "delay_unit":  self.delay_unit_var.get(),
            "rules":       self.rules,
        }
        self.config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
        messagebox.showinfo("Guardado", "Configuración aplicada.\nLos cambios entran en el próximo ciclo.", parent=self)
        self.quit()  # termina el mainloop; destroy() lo hace main() después
