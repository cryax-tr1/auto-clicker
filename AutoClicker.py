from __future__ import annotations

import json
import queue
import re
import sys
import threading
import time
import tkinter as tk
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button


APP_DIR = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent
)
RECORDINGS_DIR = APP_DIR / "recordings"
SETTINGS_FILE = APP_DIR / "settings.json"
DEFAULT_INSTALL_DIR = (
    Path.home() / "AppData" / "Local" / "Makro"
    if sys.platform.startswith("win")
    else Path.home() / ".auto-clicker"
)
APP_VERSION = "1.0.1"
GITHUB_REPOSITORY = "cryax-tr1/auto-clicker"
LATEST_RELEASE_API = (
    f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/latest"
)
RELEASES_PAGE = f"https://github.com/{GITHUB_REPOSITORY}/releases"
DISCORD_INVITE_URL = "https://discord.gg/QvVYQfbcT"
DEFAULT_HOTKEYS = {
    "record": "F6",
    "play_once": "F7",
    "play_loop": "F8",
    "click_loop": "F9",
    "stop": "F10",
}
LICENSE_TEXT = """MIT License

Copyright (c) 2026 Aras

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the \"Software\"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
HOTKEY_LABELS = {
    "record": "Kaydı başlat / bitir",
    "play_once": "Seçili kaydı bir kez oynat",
    "play_loop": "Makro tekrarını aç / kapat",
    "click_loop": "Sürekli tıklamayı aç / kapat",
    "stop": "Tüm işlemleri durdur",
}
HOTKEY_DESCRIPTIONS = {
    "record": "Fare ve klavye hareketlerini kaydeder.",
    "play_once": "Seçili makroyu bir kez çalıştırır.",
    "play_loop": "Seçili makroyu durdurana kadar tekrarlar.",
    "click_loop": "Seçilen fare tuşuyla aralıklı tıklar.",
    "stop": "Kayıt, oynatma ve tıklamayı durdurur.",
}


def key_name(key: Key | KeyCode) -> str | None:
    if isinstance(key, Key) and key.name:
        return key.name.upper()
    if isinstance(key, KeyCode) and key.char:
        return key.char.upper()
    return None


def key_from_name(name: str) -> Key | KeyCode:
    if hasattr(Key, name.lower()):
        return getattr(Key, name.lower())
    if len(name) == 1:
        return KeyCode.from_char(name.lower())
    raise ValueError(f"Desteklenmeyen tuş: {name}")


def _load_settings() -> dict[str, Any]:
    if not SETTINGS_FILE.exists():
        return {}
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_settings(data: dict[str, Any]) -> None:
    try:
        SETTINGS_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


class InstallerWizard:
    def __init__(self, root: tk.Tk | None = None) -> None:
        self.root = root or tk.Tk()
        self.root.title("Makro - Kurulum Sihirbazı")
        self.root.geometry("720x700")
        self.root.minsize(680, 620)
        self.root.configure(bg="#07131d")
        self.completed = False

        self.language_var = tk.StringVar(value="tr")
        self.install_mode_var = tk.StringVar(value="install")
        self.install_dir_var = tk.StringVar(value=str(DEFAULT_INSTALL_DIR))
        self.shortcut_var = tk.BooleanVar(value=True)
        self.autostart_var = tk.BooleanVar(value=False)
        self.update_check_var = tk.BooleanVar(value=True)
        self.accept_license_var = tk.BooleanVar(value=False)

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._cancel)

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=24)
        main.pack(fill="both", expand=True)

        title = ttk.Label(
            main,
            text="Makro Kurulum",
            font=("Segoe UI Semibold", 22),
            foreground="#e9f7ff",
            background="#07131d",
        )
        title.pack(anchor="w", pady=(0, 8))

        subtitle = ttk.Label(
            main,
            text="Dil seçimi, kurulum yeri ve işlem modunu ayarlayın.",
            foreground="#9aa9b8",
            background="#07131d",
            font=("Segoe UI", 10),
        )
        subtitle.pack(anchor="w", pady=(0, 14))

        card = ttk.Frame(main, padding=18, style="Card.TFrame")
        card.pack(fill="both", expand=True)

        ttk.Label(card, text="Dil", foreground="#dbe9f5", background="#0c1b28").pack(anchor="w", pady=(0, 6))
        language_frame = ttk.Frame(card, style="Card.TFrame")
        language_frame.pack(fill="x")
        ttk.Radiobutton(
            language_frame,
            text="Türkçe",
            variable=self.language_var,
            value="tr",
            style="TRadiobutton",
        ).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(
            language_frame,
            text="English",
            variable=self.language_var,
            value="en",
            style="TRadiobutton",
        ).pack(side="left")

        ttk.Label(card, text="Kurulum modu", foreground="#dbe9f5", background="#0c1b28").pack(anchor="w", pady=(18, 6))
        mode_frame = ttk.Frame(card, style="Card.TFrame")
        mode_frame.pack(fill="x")
        ttk.Radiobutton(
            mode_frame,
            text="Kur",
            variable=self.install_mode_var,
            value="install",
            style="TRadiobutton",
        ).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(
            mode_frame,
            text="Güncelle",
            variable=self.install_mode_var,
            value="update",
            style="TRadiobutton",
        ).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(
            mode_frame,
            text="Yalnızca çalıştır",
            variable=self.install_mode_var,
            value="run",
            style="TRadiobutton",
        ).pack(side="left")

        ttk.Label(card, text="Kurulum yolu", foreground="#dbe9f5", background="#0c1b28").pack(anchor="w", pady=(18, 6))
        dir_row = ttk.Frame(card, style="Card.TFrame")
        dir_row.pack(fill="x")
        entry = ttk.Entry(dir_row, textvariable=self.install_dir_var)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(dir_row, text="Gözat", command=self._choose_install_dir).pack(side="right")

        options = ttk.Frame(card, style="Card.TFrame")
        options.pack(fill="x", pady=(18, 0))
        ttk.Checkbutton(options, text="Masaüstü kısayolu oluştur", variable=self.shortcut_var, onvalue=True, offvalue=False).pack(anchor="w")
        ttk.Checkbutton(options, text="Windows başlangıçta otomatik başlat", variable=self.autostart_var, onvalue=True, offvalue=False).pack(anchor="w", pady=(6, 0))
        ttk.Checkbutton(options, text="Güncelleme kontrolünü aç", variable=self.update_check_var, onvalue=True, offvalue=False).pack(anchor="w", pady=(6, 0))

        license_box = tk.Text(card, height=12, wrap="word", bg="#0a1926", fg="#d9e9f5", insertbackground="#ddedff", bd=1, relief="solid")
        license_box.insert("end", LICENSE_TEXT)
        license_box.config(state="disabled")
        license_box.pack(fill="both", expand=True, pady=(18, 10))

        ttk.Checkbutton(
            card,
            text="Lisans şartlarını okudum ve kabul ediyorum.",
            variable=self.accept_license_var,
            onvalue=True,
            offvalue=False,
        ).pack(anchor="w", pady=(0, 12))

        actions = ttk.Frame(main, style="Header.TFrame")
        actions.pack(fill="x", pady=(12, 0))
        ttk.Button(actions, text="İptal", command=self._cancel).pack(side="right", padx=(8, 0))
        ttk.Button(actions, text="Kur / Devam Et", command=self._confirm).pack(side="right")

    def _choose_install_dir(self) -> None:
        chosen = filedialog.askdirectory(
            initialdir=self.install_dir_var.get() or str(DEFAULT_INSTALL_DIR),
            title="Kurulum klasörünü seçin",
        )
        if chosen:
            self.install_dir_var.set(chosen)

    def _cancel(self) -> None:
        self.completed = False
        self.root.destroy()

    def _confirm(self) -> None:
        if not self.accept_license_var.get():
            messagebox.showwarning(
                "Lisans onayı",
                "Kuruluma devam etmek için lisans şartlarını kabul etmelisiniz.",
                parent=self.root,
            )
            return

        install_dir = Path(self.install_dir_var.get()).expanduser()
        if not install_dir.exists():
            try:
                install_dir.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                messagebox.showerror(
                    "Klasör oluşturulamadı",
                    f"Seçilen klasör oluşturulamadı:\n{install_dir}\n\n{exc}",
                    parent=self.root,
                )
                return

        settings = _load_settings()
        settings["language"] = self.language_var.get()
        settings["install"] = {
            "mode": self.install_mode_var.get(),
            "directory": str(install_dir),
            "shortcut": bool(self.shortcut_var.get()),
            "autostart": bool(self.autostart_var.get()),
            "update_check": bool(self.update_check_var.get()),
            "completed": True,
        }
        settings["hotkeys"] = settings.get("hotkeys", DEFAULT_HOTKEYS)
        _save_settings(settings)

        summary = (
            f"Dil: {('Türkçe' if self.language_var.get() == 'tr' else 'English')}\n"
            f"Kurulum yolu: {install_dir}\n"
            f"İşlem: {self.install_mode_var.get()}\n"
            f"Masaüstü kısayolu: {'Evet' if self.shortcut_var.get() else 'Hayır'}\n"
            f"Güncelleme kontrolü: {'Açık' if self.update_check_var.get() else 'Kapalı'}"
        )
        self.completed = True
        messagebox.showinfo(
            "Kurulum hazır",
            f"Aşağıdaki ayarlar kaydedildi:\n\n{summary}",
            parent=self.root,
        )
        self.root.destroy()


class AutoClickerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Makro")
        self.root.geometry("1180x800")
        self.root.minsize(1050, 720)
        self.root.configure(bg="#07131d")

        self.events: list[dict[str, Any]] = []
        self.event_counts = {"click": 0, "move": 0, "key": 0}
        self.recording_started = 0.0
        self.recording_duration = 0.0
        self.recording_lock = threading.Lock()
        self.last_move_at = 0.0
        self.last_position: tuple[int, int] | None = None
        self.mouse_listener: mouse.Listener | None = None
        self.keyboard_listener: keyboard.Listener | None = None
        self.hotkey_listener: keyboard.Listener | None = None
        self._hotkey_events: queue.SimpleQueue[tuple[str, str]] = queue.SimpleQueue()
        self._recording_count_events: queue.SimpleQueue[int] = queue.SimpleQueue()
        self._update_events: queue.SimpleQueue[tuple[str, str, str]] = queue.SimpleQueue()
        self.pressed_keys: set[str] = set()
        self.capture_hotkey: str | None = None
        self._closing = False
        self._window_bounds: tuple[int, int, int, int] | None = None

        self.play_token = 0
        self.play_events: list[dict[str, Any]] = []
        self.play_duration = 0.0
        self.play_started = 0.0
        self.play_index = 0
        self.play_loop = False
        self.held_keys: dict[str, Key | KeyCode] = {}
        self.held_buttons: dict[str, Button] = {}

        self.click_token = 0
        self.click_loop = False
        self.click_button: Button | None = None
        self.click_count = 0
        self.app_started = time.perf_counter()
        self.macro_event_total = 0
        self.invalid_macro_count = 0
        self.selected_macro_event_count: int | None = None

        self.hotkeys = self._load_hotkeys()
        self._configure_style()
        self._build_ui()
        self.root.bind("<Configure>", self._update_window_bounds)
        self._update_window_bounds()
        self._refresh_recording_list()
        self._start_hotkey_listener()
        self.root.after(30, self._process_hotkey_events)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        install_settings = _load_settings().get("install", {})
        if not isinstance(install_settings, dict) or install_settings.get(
            "update_check", True
        ):
            self.root.after(1200, self._check_for_updates)

    @staticmethod
    def _version_key(version: str) -> tuple[int, ...] | None:
        normalized = version.strip().lower()
        if normalized.startswith("v"):
            normalized = normalized[1:]
        if not re.fullmatch(r"\d+(?:\.\d+)*", normalized):
            return None
        return tuple(int(part) for part in normalized.split("."))

    def _check_for_updates(self) -> None:
        thread = threading.Thread(
            target=self._fetch_latest_release,
            daemon=True,
            name="release-check",
        )
        thread.start()
        self.root.after(200, self._process_update_result)

    def _fetch_latest_release(self) -> None:
        try:
            request = urllib.request.Request(
                LATEST_RELEASE_API,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": f"AutoClicker/{APP_VERSION}",
                },
            )
            with urllib.request.urlopen(request, timeout=8) as response:
                release = json.loads(response.read().decode("utf-8"))

            if not isinstance(release, dict):
                raise ValueError("GitHub yanıtı beklenen biçimde değil.")
            version = release.get("tag_name")
            release_url = release.get("html_url")
            if not isinstance(version, str) or not isinstance(release_url, str):
                raise ValueError("Sürüm etiketi veya Release bağlantısı bulunamadı.")
            if not release_url.startswith(RELEASES_PAGE + "/"):
                raise ValueError("Release bağlantısı beklenen GitHub deposuna ait değil.")

            current_key = self._version_key(APP_VERSION)
            latest_key = self._version_key(version)
            if current_key is None or latest_key is None:
                raise ValueError("Sürüm numarası x.y.z biçiminde olmalı.")
            if latest_key > current_key:
                self._update_events.put(("available", version, release_url))
            else:
                self._update_events.put(("current", version, release_url))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                self._update_events.put(("none", "", ""))
            else:
                self._update_events.put(("error", "", str(exc)))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self._update_events.put(("error", "", str(exc)))

    def _process_update_result(self) -> None:
        try:
            result, version, release_url = self._update_events.get_nowait()
        except queue.Empty:
            if not self._closing and self.root.winfo_exists():
                self.root.after(200, self._process_update_result)
            return

        if self._closing or not self.root.winfo_exists():
            return
        if result == "available":
            should_open = messagebox.askyesno(
                "Güncelleme bulundu",
                (
                    f"Makro için yeni sürüm ({version}) yayınlandı.\n"
                    f"Yüklü sürüm: {APP_VERSION}\n\n"
                    "GitHub sürüm sayfasını açmak ister misin?"
                ),
                parent=self.root,
            )
            if should_open:
                webbrowser.open(release_url)
        elif result == "error":
            self.status_var.set("Güncelleme kontrolü başarısız oldu; sonra tekrar dene.")

    def _load_hotkeys(self) -> dict[str, str]:
        hotkeys = DEFAULT_HOTKEYS.copy()
        try:
            if SETTINGS_FILE.exists():
                settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                saved = settings.get("hotkeys", {})
                for action in hotkeys:
                    candidate = saved.get(action)
                    if isinstance(candidate, str) and candidate:
                        hotkeys[action] = candidate.upper()
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            messagebox.showwarning(
                "Kısayol ayarları",
                f"Ayar dosyası okunamadı; varsayılan kısayollar kullanılacak.\n{exc}",
                parent=self.root,
            )
        assigned_hotkeys = [name for name in hotkeys.values() if name != "-"]
        if len(set(assigned_hotkeys)) != len(assigned_hotkeys):
            hotkeys = DEFAULT_HOTKEYS.copy()
        return hotkeys

    @staticmethod
    def _hotkey_display(name: str) -> str:
        return "—" if name == "-" else name

    def _save_hotkeys(self) -> None:
        try:
            settings = _load_settings()
            settings["hotkeys"] = self.hotkeys
            SETTINGS_FILE.write_text(
                json.dumps(settings, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            messagebox.showerror(
                "Ayarlar kaydedilemedi",
                f"Kısayollar bu oturumda kullanılacak, ancak dosyaya yazılamadı.\n{exc}",
                parent=self.root,
            )

    def _configure_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#07131d")
        style.configure("Card.TFrame", background="#0c1b28")
        style.configure("Header.TFrame", background="#07131d")
        style.configure("Sidebar.TFrame", background="#0b1b29")
        style.configure("StatusBar.TFrame", background="#0c1b28")
        style.configure("HotkeyRow.TFrame", background="#102333")
        style.configure(
            "SidebarCaption.TLabel",
            background="#0b1b29",
            foreground="#66869a",
            font=("Consolas", 8, "bold"),
        )
        style.configure(
            "Nav.TButton",
            background="#0b1b29",
            foreground="#9eb6c6",
            anchor="w",
            padding=(12, 12),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "Nav.TButton",
            background=[("active", "#122c3c")],
            foreground=[("active", "#d9f7ff")],
        )
        style.configure(
            "NavActive.TButton",
            background="#123849",
            foreground="#55e4ff",
            anchor="w",
            padding=(12, 12),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "NavActive.TButton",
            background=[("active", "#17485c")],
            foreground=[("active", "#8af0ff")],
        )
        style.configure(
            "TLabel",
            background="#07131d",
            foreground="#edf2ff",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Card.TLabel",
            background="#0c1b28",
            foreground="#edf2ff",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Row.TLabel",
            background="#102333",
            foreground="#edf2ff",
            font=("Segoe UI Semibold", 10),
        )
        style.configure(
            "RowHint.TLabel",
            background="#102333",
            foreground="#99a8c2",
            font=("Segoe UI", 9),
        )
        style.configure(
            "RowIndex.TLabel",
            background="#102333",
            foreground="#31e6ff",
            font=("Consolas", 10, "bold"),
        )
        style.configure(
            "Telemetry.TLabel",
            background="#07131d",
            foreground="#7895a8",
            font=("Consolas", 8),
        )
        style.configure(
            "Title.TLabel",
            background="#07131d",
            foreground="#f5f7ff",
            font=("Segoe UI Semibold", 26),
        )
        style.configure(
            "Subtitle.TLabel",
            background="#07131d",
            foreground="#9aa8c2",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Eyebrow.TLabel",
            background="#07131d",
            foreground="#31e6ff",
            font=("Segoe UI Semibold", 9),
        )
        style.configure(
            "HeaderLink.TLabel",
            background="#07131d",
            foreground="#75eaff",
            font=("Segoe UI", 9, "underline"),
        )
        style.configure(
            "BrandMark.TLabel",
            background="#102333",
            foreground="#31e6ff",
            font=("Segoe UI Semibold", 15),
            padding=(12, 8),
        )
        style.configure(
            "HeaderBadge.TLabel",
            background="#0b303a",
            foreground="#5eeeff",
            font=("Segoe UI Semibold", 9),
            padding=(10, 7),
        )
        style.configure(
            "HeaderBadgeOff.TLabel",
            background="#3a2430",
            foreground="#ffb3c1",
            font=("Segoe UI Semibold", 9),
            padding=(10, 7),
        )
        style.configure(
            "CardEyebrow.TLabel",
            background="#0c1b28",
            foreground="#51dcff",
            font=("Segoe UI Semibold", 9),
        )
        style.configure(
            "Section.TLabel",
            background="#0c1b28",
            foreground="#f5f7ff",
            font=("Segoe UI Semibold", 14),
        )
        style.configure(
            "Hint.TLabel",
            background="#0c1b28",
            foreground="#9aaec1",
            font=("Segoe UI", 9),
        )
        style.configure(
            "Key.TLabel",
            background="#10394a",
            foreground="#75eaff",
            font=("Segoe UI Semibold", 10),
            padding=(12, 7),
        )
        style.configure(
            "Count.TLabel",
            background="#17283a",
            foreground="#b3d7e5",
            font=("Segoe UI Semibold", 9),
            padding=(9, 5),
        )
        style.configure(
            "TButton",
            font=("Segoe UI Semibold", 10),
            padding=(13, 10),
            background="#263248",
            foreground="#edf2ff",
            borderwidth=0,
            focusthickness=0,
        )
        style.map(
            "TButton",
            background=[
                ("pressed", "#35445f"),
                ("active", "#33415a"),
                ("disabled", "#1a2333"),
            ],
            foreground=[("disabled", "#68748a")],
        )
        style.configure(
            "Accent.TButton",
            background="#159fc1",
            foreground="#f1fdff",
        )
        style.map(
            "Accent.TButton",
            background=[("pressed", "#087a9a"), ("active", "#20c5e8")],
        )
        style.configure("Stop.TButton", background="#a84156", foreground="#ffffff")
        style.map(
            "Stop.TButton",
            background=[("pressed", "#8c3045"), ("active", "#c44d65")],
        )
        style.configure(
            "Capture.TButton",
            background="#6847a8",
            foreground="#f4edff",
            padding=(13, 9),
        )
        style.map(
            "Capture.TButton",
            background=[("active", "#825fd0"), ("pressed", "#4e3388")],
        )
        style.configure(
            "TCheckbutton",
            background="#0c1b28",
            foreground="#dbe4f4",
            font=("Segoe UI", 10),
        )
        style.map(
            "TCheckbutton",
            background=[("active", "#0c1b28")],
            foreground=[("active", "#ffffff")],
        )
        style.configure(
            "TRadiobutton",
            background="#0c1b28",
            foreground="#dbe4f4",
            font=("Segoe UI", 10),
        )
        style.map(
            "TRadiobutton",
            background=[("active", "#0c1b28")],
            foreground=[("active", "#ffffff")],
        )
        style.configure(
            "TEntry",
            fieldbackground="#071722",
            foreground="#f4f7ff",
            insertcolor="#31e6ff",
            bordercolor="#244256",
            lightcolor="#244256",
            darkcolor="#244256",
            padding=8,
        )
        style.map("TEntry", bordercolor=[("focus", "#31dfff")])
        style.configure("Hidden.TNotebook", background="#07131d", borderwidth=0)
        style.layout("Hidden.TNotebook.Tab", [])
        style.configure(
            "TNotebook.Tab",
            background="#102333",
            foreground="#a7bac8",
            padding=(18, 11),
            font=("Segoe UI Semibold", 10),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#10394a"), ("active", "#173347")],
            foreground=[("selected", "#75eaff"), ("active", "#edf8ff")],
        )
        style.configure(
            "Vertical.TScrollbar",
            background="#24506a",
            troughcolor="#0c1b28",
            bordercolor="#0c1b28",
            arrowcolor="#aab6cb",
            width=11,
        )
        style.map("Vertical.TScrollbar", background=[("active", "#31b9d7")])

    def _create_hud_panel(
        self,
        parent: ttk.Frame,
        module_id: str,
        *,
        height: int = 180,
        expand: bool = True,
        pady: tuple[int, int] = (0, 0),
    ) -> ttk.Frame:
        canvas = tk.Canvas(
            parent,
            background="#081722",
            height=height,
            highlightthickness=0,
            borderwidth=0,
        )
        canvas.pack(fill="both", expand=expand, pady=pady)
        content = ttk.Frame(
            canvas,
            style="Card.TFrame",
            padding=(18, 13, 18, 15),
        )
        window_id = canvas.create_window(
            10, 22, anchor="nw", window=content, tags=("hud-content",)
        )
        canvas.bind(
            "<Configure>",
            lambda event: self._draw_hud_panel(
                canvas, window_id, module_id, event.width, event.height
            ),
        )
        return content

    @staticmethod
    def _draw_hud_panel(
        canvas: tk.Canvas,
        window_id: int,
        module_id: str,
        width: int,
        height: int,
    ) -> None:
        canvas.delete("hud-decoration")
        inner_width = max(1, width - 20)
        inner_height = max(1, height - 32)
        canvas.coords(window_id, 10, 22)
        canvas.itemconfigure(window_id, width=inner_width, height=inner_height)
        if width < 80 or height < 60:
            return

        points = [
            (1, 17), (17, 1), (width - 30, 1), (width - 14, 15),
            (width - 2, 15), (width - 2, height - 17),
            (width - 17, height - 2), (22, height - 2), (1, height - 22),
        ]
        canvas.create_line(
            *(coordinate for point in points for coordinate in point),
            fill="#17768d",
            width=1,
            tags=("hud-decoration",),
        )
        canvas.create_line(
            1, 17, 17, 1, width=2, fill="#31e6ff",
            tags=("hud-decoration",),
        )
        canvas.create_line(
            17, 1, width - 30, 1, width=2, fill="#31e6ff",
            tags=("hud-decoration",),
        )
        canvas.create_line(
            1, height - 22, 1, 36, fill="#14556c",
            tags=("hud-decoration",),
        )
        canvas.create_text(
            22,
            10,
            text=module_id,
            fill="#50cde8",
            anchor="w",
            font=("Consolas", 7, "bold"),
            tags=("hud-decoration",),
        )
        canvas.create_line(
            22, 18, 124, 18, fill="#164255",
            tags=("hud-decoration",),
        )
        for index in range(4):
            x = width - 58 + index * 9
            canvas.create_rectangle(
                x,
                7,
                x + 5,
                10,
                fill="#31e6ff" if index == 0 else "#1b5367",
                outline="",
                tags=("hud-decoration",),
            )
        for x in range(30, width - 12, 32):
            canvas.create_line(
                x, height - 10, x + 7, height - 10,
                fill="#174356", tags=("hud-decoration",),
            )
        canvas.tag_raise(window_id)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=(18, 16, 18, 14))
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer, style="Header.TFrame")
        header.pack(fill="x", pady=(0, 13))
        brand = ttk.Frame(header, style="Header.TFrame")
        brand.pack(side="left", fill="x", expand=True)
        ttk.Label(brand, text="✦", style="BrandMark.TLabel").pack(
            side="left", padx=(0, 14)
        )
        title_block = ttk.Frame(brand, style="Header.TFrame")
        title_block.pack(side="left", anchor="w")
        ttk.Label(
            title_block, text="Developed by Aras", style="Eyebrow.TLabel"
        ).pack(anchor="w")
        ttk.Label(title_block, text="MAKRO", style="Title.TLabel").pack(
            anchor="w", pady=(1, 0)
        )
        discord_link = ttk.Label(
            title_block,
            text="Discord: discord.gg/QvVYQfbcT",
            style="HeaderLink.TLabel",
            cursor="hand2",
        )
        discord_link.pack(anchor="w", pady=(2, 0))
        discord_link.bind("<Button-1>", self._open_discord)
        self.hotkey_badge_var = tk.StringVar(value="●  KISAYOLLAR BAŞLATILIYOR")
        self.hotkey_badge = ttk.Label(
            header,
            textvariable=self.hotkey_badge_var,
            style="HeaderBadgeOff.TLabel",
        )
        self.hotkey_badge.pack(side="right", anchor="n", pady=(5, 0))

        workspace = ttk.Frame(outer, style="Header.TFrame")
        workspace.pack(fill="both", expand=True)
        self.sidebar = ttk.Frame(
            workspace, style="Sidebar.TFrame", padding=(10, 12)
        )
        self.sidebar.pack(side="left", fill="y", padx=(0, 14))
        ttk.Label(
            self.sidebar, text="NAVIGATION", style="SidebarCaption.TLabel"
        ).pack(anchor="w", padx=8, pady=(4, 10))

        self.tabs = ttk.Notebook(workspace, style="Hidden.TNotebook")
        self.tabs.pack(side="left", fill="both", expand=True)
        self.page_names = {
            "control": "Kontrol Merkezi",
            "macros": "Makro Kütüphanesi",
            "hotkeys": "Tuş Atamaları",
            "settings": "Genel Ayarlar",
            "statistics": "İstatistikler",
            "about": "Hakkında",
        }
        self.pages: dict[str, ttk.Frame] = {}
        for key, title in self.page_names.items():
            page = ttk.Frame(self.tabs, padding=(4, 6, 4, 4))
            self.pages[key] = page
            self.tabs.add(page, text=title)
            ttk.Button(
                self.sidebar,
                text=title,
                style="Nav.TButton",
                command=lambda selected=key: self._show_page(selected),
            ).pack(fill="x", pady=3)

        ttk.Separator(self.sidebar, orient="horizontal").pack(
            fill="x", pady=(12, 10)
        )
        ttk.Label(
            self.sidebar,
            text="SYSTEM ONLINE\nNEON UI  /  v1.0",
            style="SidebarCaption.TLabel",
            justify="left",
        ).pack(anchor="w", padx=8, pady=(2, 6))

        self.macro_tab = self.pages["macros"]
        self.settings_tab = self.pages["hotkeys"]
        self._build_dashboard_page(self.pages["control"])
        self._build_macro_tab()
        self._build_settings_tab()
        self._build_preferences_page(self.pages["settings"])
        self._build_statistics_page(self.pages["statistics"])
        self._build_about_page(self.pages["about"])
        self._show_page("control")

        self.status_var = tk.StringVar(value="Hazır")
        status_bar = ttk.Frame(outer, style="StatusBar.TFrame", padding=(14, 9))
        status_bar.pack(fill="x", pady=(13, 0))
        self.status_indicator_var = tk.StringVar(value="● READY")
        ttk.Label(
            status_bar, textvariable=self.status_indicator_var, style="Telemetry.TLabel"
        ).pack(side="left")
        ttk.Label(status_bar, text="STATUS /", style="CardEyebrow.TLabel").pack(
            side="left", padx=(10, 0)
        )
        ttk.Label(status_bar, textvariable=self.status_var, style="Card.TLabel").pack(
            side="left", padx=(8, 0)
        )
        self.session_clock_var = tk.StringVar(value="SESSION 00:00:00")
        ttk.Label(
            status_bar,
            textvariable=self.session_clock_var,
            style="Telemetry.TLabel",
        ).pack(side="right")
        self.root.after(500, self._refresh_live_dashboard)

    def _open_discord(self, _event: tk.Event[tk.Misc]) -> None:
        try:
            opened = webbrowser.open(DISCORD_INVITE_URL)
        except OSError as exc:
            messagebox.showerror(
                "Discord açılamadı",
                f"Discord davet bağlantısı açılamadı:\n{exc}",
                parent=self.root,
            )
            return
        if not opened:
            messagebox.showerror(
                "Discord açılamadı",
                "Discord davet bağlantısı varsayılan tarayıcıda açılamadı.",
                parent=self.root,
            )

    def _build_dashboard_page(self, page: ttk.Frame) -> None:
        hero = self._create_hud_panel(
            page, "CONTROL CENTER // OPERATOR CONSOLE", height=220, expand=False
        )
        ttk.Label(
            hero, text="Kontrol Merkezi", style="Section.TLabel"
        ).pack(anchor="w", pady=(0, 5))
        ttk.Label(
            hero,
            text="Makrolarını yönet, iş akışını kaydet ve tıklama motorunu çalıştır.",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(0, 17))
        actions = ttk.Frame(hero, style="Card.TFrame")
        actions.pack(fill="x")
        ttk.Button(
            actions,
            text="●  KAYDI BAŞLAT",
            style="Accent.TButton",
            command=self.toggle_recording,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            actions,
            text="▶  SEÇİLİ MAKROYU OYNAT",
            command=self.play_selected_once,
        ).pack(side="left", padx=8)
        ttk.Button(
            actions,
            text="↻  SÜREKLİ TIKLAMA",
            command=self.toggle_clicking,
        ).pack(side="left", padx=8)
        ttk.Button(
            actions,
            text="■  TÜMÜNÜ DURDUR",
            style="Stop.TButton",
            command=self.stop_all,
        ).pack(side="right", padx=(8, 0))

        lower = ttk.Frame(page, style="Header.TFrame")
        lower.pack(fill="both", expand=True, pady=(12, 0))
        lower.columnconfigure(0, weight=3)
        lower.columnconfigure(1, weight=2)
        activity_column = ttk.Frame(lower, style="Header.TFrame")
        activity_column.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        shortcut_column = ttk.Frame(lower, style="Header.TFrame")
        shortcut_column.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        activity = self._create_hud_panel(
            activity_column, "LIVE TELEMETRY // SESSION", height=300, expand=True
        )
        ttk.Label(
            activity, text="Canlı oturum verileri", style="Section.TLabel"
        ).pack(anchor="w", pady=(0, 12))
        self.dashboard_readouts: dict[str, tk.StringVar] = {}
        for name in ("Durum", "Makro sayısı", "Oturum tıklaması", "Tıklama hızı"):
            value = tk.StringVar(value="—")
            self.dashboard_readouts[name] = value
            self._add_readout(activity, name.upper(), value)
        ttk.Button(
            activity,
            text="MAKRO KÜTÜPHANESİNİ AÇ  →",
            command=lambda: self._show_page("macros"),
        ).pack(anchor="w", pady=(15, 0))

        shortcuts = self._create_hud_panel(
            shortcut_column, "QUICK ACCESS // KEY MATRIX", height=300, expand=True
        )
        ttk.Label(
            shortcuts, text="Hızlı erişim", style="Section.TLabel"
        ).pack(anchor="w", pady=(0, 10))
        self.dashboard_hotkey_vars: dict[str, tk.StringVar] = {}
        for action in ("record", "play_once", "play_loop", "click_loop", "stop"):
            value = tk.StringVar(value=self._hotkey_display(self.hotkeys[action]))
            self.dashboard_hotkey_vars[action] = value
            self._add_readout(shortcuts, HOTKEY_LABELS[action], value)
        ttk.Button(
            shortcuts,
            text="TUŞLARI DÜZENLE  →",
            command=lambda: self._show_page("hotkeys"),
        ).pack(anchor="w", pady=(12, 0))

    def _show_page(self, key: str) -> None:
        page_keys = list(self.page_names)
        self.tabs.select(self.pages[key])
        for index, button in enumerate(
            child for child in self.sidebar.winfo_children()
            if isinstance(child, ttk.Button)
        ):
            button.configure(
                style="NavActive.TButton"
                if page_keys[index] == key
                else "Nav.TButton"
            )

    def _refresh_live_dashboard(self) -> None:
        if self._closing or not self.root.winfo_exists():
            return
        elapsed = int(time.perf_counter() - self.app_started)
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.session_clock_var.set(f"SESSION {hours:02d}:{minutes:02d}:{seconds:02d}")
        if self.click_loop:
            state = "TIKLAMA AKTİF"
            self.status_indicator_var.set("● CLICK ENGINE ACTIVE")
        elif self.play_events:
            state = "MAKRO ÇALIŞIYOR"
            self.status_indicator_var.set("● MACRO RUNNING")
        elif self.mouse_listener is not None or self.keyboard_listener is not None:
            state = "KAYIT YAPILIYOR"
            self.status_indicator_var.set("● RECORDING")
        else:
            state = "HAZIR"
            self.status_indicator_var.set("● READY")
        self.system_state_var.set(state)
        interval = self.interval_var.get().strip()
        try:
            milliseconds = int(interval)
            rate = f"{1000 / milliseconds:.1f} CPS" if milliseconds > 0 else "— CPS"
        except ValueError:
            rate = "— CPS"
        self.click_rate_var.set(rate)
        self.click_total_var.set(str(self.click_count))
        self.telemetry_vars["Fare olayları"].set(
            str(self.event_counts["click"] + self.event_counts["move"])
        )
        self.telemetry_vars["Klavye olayları"].set(str(self.event_counts["key"]))
        self.telemetry_vars["Makro olayları"].set(str(len(self.play_events)))
        self.dashboard_readouts["Durum"].set(state)
        self.dashboard_readouts["Makro sayısı"].set(str(len(self.recording_files)))
        self.dashboard_readouts["Oturum tıklaması"].set(str(self.click_count))
        self.dashboard_readouts["Tıklama hızı"].set(rate)
        self._update_statistics_values()
        self.root.after(500, self._refresh_live_dashboard)

    def _build_macro_tab(self) -> None:
        columns = ttk.Frame(self.macro_tab, style="Header.TFrame")
        columns.pack(fill="both", expand=True)
        library_column = ttk.Frame(columns, style="Header.TFrame")
        library_column.pack(side="left", fill="both", expand=True, padx=(0, 12))
        system_column = ttk.Frame(columns, style="Header.TFrame", width=280)
        system_column.pack(side="left", fill="y")
        system_column.pack_propagate(False)

        card = self._create_hud_panel(
            library_column, "MODULE 01 // MACRO MEMORY", height=360
        )
        header = ttk.Frame(card, style="Card.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text="Makro kütüphanesi", style="Section.TLabel").pack(
            side="left", anchor="w"
        )
        self.recording_count_var = tk.StringVar(value="0 KAYIT")
        ttk.Label(header, textvariable=self.recording_count_var, style="Count.TLabel").pack(
            side="right"
        )
        ttk.Label(
            card,
            text="Bir kayıt seçip oynat. Yeni makrolar otomatik olarak kütüphaneye eklenir.",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(5, 14))

        list_frame = ttk.Frame(card, style="Card.TFrame")
        list_frame.pack(fill="both", expand=True, pady=(0, 2))
        self.recording_list = tk.Listbox(
            list_frame,
            height=6,
            bg="#071722",
            fg="#e8eefb",
            selectbackground="#087a9a",
            selectforeground="#ffffff",
            highlightthickness=0,
            selectborderwidth=0,
            relief="flat",
            activestyle="none",
            font=("Segoe UI", 11),
            borderwidth=0,
            exportselection=False,
            takefocus=True,
        )
        self.recording_list.pack(side="left", fill="both", expand=True)
        self.empty_recordings_label = ttk.Label(
            list_frame,
            text="Henüz makro kaydı yok\nBir tane oluşturmak için “Kaydı başlat”a bas.",
            style="Hint.TLabel",
            anchor="center",
            justify="center",
        )
        self.empty_recordings_label.place(relx=0.5, rely=0.5, anchor="center")
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.recording_list.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.recording_list.configure(yscrollcommand=scrollbar.set)
        self.recording_list.bind("<<ListboxSelect>>", self._select_recording)
        self.recording_files: list[Path] = []

        ttk.Separator(card, orient="horizontal").pack(fill="x", pady=(14, 13))
        buttons = ttk.Frame(card, style="Card.TFrame")
        buttons.pack(fill="x")
        buttons.columnconfigure(0, weight=1, uniform="macro-action")
        buttons.columnconfigure(1, weight=1, uniform="macro-action")
        self.record_button = ttk.Button(
            buttons,
            text=f"Kaydı başlat ({self._hotkey_display(self.hotkeys['record'])})",
            style="Accent.TButton",
            command=self.toggle_recording,
        )
        self.record_button.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=3)
        self.play_button = ttk.Button(
            buttons,
            text=f"Seçileni oynat ({self._hotkey_display(self.hotkeys['play_once'])})",
            command=self.play_selected_once,
            state="disabled",
        )
        self.play_button.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=3)
        self.loop_button = ttk.Button(
            buttons,
            text=f"Tekrarı başlat ({self._hotkey_display(self.hotkeys['play_loop'])})",
            command=self.toggle_playback_loop,
            state="disabled",
        )
        self.loop_button.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=3)
        self.stop_button = ttk.Button(
            buttons,
            text=f"Durdur ({self._hotkey_display(self.hotkeys['stop'])})",
            style="Stop.TButton",
            command=self.stop_all,
        )
        self.stop_button.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=3)

        click_card = self._create_hud_panel(
            library_column,
            "OUTPUT CHANNEL // CLICK ENGINE",
            height=170,
            expand=False,
            pady=(12, 0),
        )
        click_header = ttk.Frame(click_card, style="Card.TFrame")
        click_header.pack(fill="x")
        ttk.Label(click_header, text="Sürekli tıklama", style="Section.TLabel").pack(
            side="left", anchor="w"
        )
        self.click_hotkey_label = ttk.Label(
            click_header,
            text=f"KISAYOL  {self._hotkey_display(self.hotkeys['click_loop'])}",
            style="Key.TLabel",
        )
        self.click_hotkey_label.pack(side="right")
        click_settings = ttk.Frame(click_card, style="Card.TFrame")
        click_settings.pack(fill="x", pady=(16, 0))
        ttk.Label(click_settings, text="Aralık (ms):", style="Card.TLabel").pack(
            side="left"
        )
        self.interval_var = tk.StringVar(value="100")
        ttk.Entry(click_settings, textvariable=self.interval_var, width=9).pack(
            side="left", padx=(8, 18)
        )
        ttk.Label(click_settings, text="Tıklama:", style="Card.TLabel").pack(
            side="left"
        )
        self.button_var = tk.StringVar(value="left")
        ttk.Radiobutton(
            click_settings, text="Sol", variable=self.button_var, value="left"
        ).pack(side="left", padx=(6, 0))
        ttk.Radiobutton(
            click_settings, text="Sağ", variable=self.button_var, value="right"
        ).pack(side="left", padx=(6, 0))
        self.click_start_button = ttk.Button(
            click_settings,
            text=f"Başlat ({self._hotkey_display(self.hotkeys['click_loop'])})",
            style="Accent.TButton",
            command=self.toggle_clicking,
        )
        self.click_start_button.pack(side="right")

        self.system_panel = self._create_hud_panel(
            system_column,
            "SYSTEM STATUS // LIVE",
            height=530,
            expand=True,
        )
        ttk.Label(
            self.system_panel, text="Sistem durumu", style="Section.TLabel"
        ).pack(anchor="w", pady=(0, 12))
        self.system_state_var = tk.StringVar(value="HAZIR")
        self._add_readout(self.system_panel, "ÇALIŞMA DURUMU", self.system_state_var)
        self._add_readout(
            self.system_panel, "MAKRO KÜTÜPHANESİ", self.recording_count_var
        )
        self.click_rate_var = tk.StringVar(value="10.0 CPS")
        self._add_readout(self.system_panel, "TIKLAMA HIZI", self.click_rate_var)
        self.click_total_var = tk.StringVar(value="0")
        self._add_readout(self.system_panel, "OTURUM TIKLAMASI", self.click_total_var)
        ttk.Separator(self.system_panel, orient="horizontal").pack(
            fill="x", pady=12
        )
        ttk.Label(
            self.system_panel, text="INPUT TELEMETRY", style="CardEyebrow.TLabel"
        ).pack(anchor="w", pady=(2, 8))
        self.telemetry_vars: dict[str, tk.StringVar] = {}
        for label in ("Fare olayları", "Klavye olayları", "Makro olayları"):
            value = tk.StringVar(value="0")
            self.telemetry_vars[label] = value
            self._add_readout(self.system_panel, label.upper(), value)
        ttk.Separator(self.system_panel, orient="horizontal").pack(
            fill="x", pady=12
        )
        ttk.Label(
            self.system_panel,
            text="F6 Kayıt   /   F7 Oynat\nF8 Döngü   /   F9 Tıklama\nF10 Durdur",
            style="Telemetry.TLabel",
            justify="left",
        ).pack(anchor="w", pady=(3, 0))

    @staticmethod
    def _add_readout(
        parent: ttk.Frame, label: str, value: tk.StringVar
    ) -> None:
        row = ttk.Frame(parent, style="Card.TFrame")
        row.pack(fill="x", pady=5)
        ttk.Label(row, text=label, style="Telemetry.TLabel").pack(
            side="left", anchor="w"
        )
        ttk.Label(row, textvariable=value, style="Card.TLabel").pack(
            side="right", anchor="e"
        )

    def _build_preferences_page(self, page: ttk.Frame) -> None:
        panel = self._create_hud_panel(
            page, "SYSTEM CONFIGURATION // PREFERENCES", height=540
        )
        ttk.Label(
            panel, text="Uygulama ayarları", style="Section.TLabel"
        ).pack(anchor="w", pady=(0, 5))
        ttk.Label(
            panel,
            text="Tıklama davranışını ve kayıt alanlarını buradan yönet.",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(0, 17))

        rate_row = ttk.Frame(panel, style="Card.TFrame")
        rate_row.pack(fill="x", pady=7)
        ttk.Label(
            rate_row, text="Tıklama aralığı (ms)", style="Card.TLabel"
        ).pack(side="left")
        ttk.Entry(
            rate_row, textvariable=self.interval_var, width=12
        ).pack(side="right")

        button_row = ttk.Frame(panel, style="Card.TFrame")
        button_row.pack(fill="x", pady=7)
        ttk.Label(button_row, text="Fare tuşu", style="Card.TLabel").pack(
            side="left"
        )
        ttk.Radiobutton(
            button_row, text="Sol", variable=self.button_var, value="left"
        ).pack(side="right", padx=(10, 0))
        ttk.Radiobutton(
            button_row, text="Sağ", variable=self.button_var, value="right"
        ).pack(side="right")

        ttk.Separator(panel, orient="horizontal").pack(fill="x", pady=15)
        self._add_readout(
            panel,
            "Global kısayol dinleyicisi",
            self.hotkey_badge_var,
        )
        ttk.Label(
            panel, text="KAYIT KONUMU", style="CardEyebrow.TLabel"
        ).pack(anchor="w", pady=(16, 4))
        ttk.Label(
            panel,
            text=str(RECORDINGS_DIR),
            style="Hint.TLabel",
            wraplength=720,
        ).pack(anchor="w")
        ttk.Label(
            panel, text="AYAR DOSYASI", style="CardEyebrow.TLabel"
        ).pack(anchor="w", pady=(13, 4))
        ttk.Label(
            panel,
            text=str(SETTINGS_FILE),
            style="Hint.TLabel",
            wraplength=720,
        ).pack(anchor="w")
        ttk.Button(
            panel,
            text="Makro listesini yenile",
            command=self._refresh_recording_list,
        ).pack(anchor="w", pady=(17, 0))

    def _build_statistics_page(self, page: ttk.Frame) -> None:
        panel = self._create_hud_panel(
            page, "PERFORMANCE DATA // SESSION STATISTICS", height=540
        )
        ttk.Label(
            panel, text="İstatistikler", style="Section.TLabel"
        ).pack(anchor="w", pady=(0, 5))
        ttk.Label(
            panel,
            text="Bu oturum ve kayıt kütüphanesinden canlı hesaplanan veriler.",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(0, 16))
        self.statistics_vars: dict[str, tk.StringVar] = {}
        for label in (
            "Kayıtlı makro",
            "Toplam makro olayı",
            "Okunamayan makro",
            "Bu oturum tıklaması",
            "Seçili makro",
            "Seçili makro olayı",
            "Geçen oturum süresi",
            "Ayarlanan tıklama hızı",
        ):
            value = tk.StringVar(value="—")
            self.statistics_vars[label] = value
            self._add_readout(panel, label.upper(), value)

        ttk.Separator(panel, orient="horizontal").pack(fill="x", pady=14)
        ttk.Label(
            panel,
            text="Veriler makro JSON dosyalarından ve uygulamanın bu oturumdaki işlem sayaçlarından hesaplanır.",
            style="Hint.TLabel",
            wraplength=740,
        ).pack(anchor="w")

    def _build_about_page(self, page: ttk.Frame) -> None:
        panel = self._create_hud_panel(
            page, "MAKRO // SYSTEM INFORMATION", height=540
        )
        ttk.Label(
            panel, text="Makro", style="Section.TLabel"
        ).pack(anchor="w", pady=(0, 6))
        ttk.Label(
            panel,
            text="Makro kaydetme, oynatma ve hassas aralıklı tıklama aracı.",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(0, 17))
        for label, description in (
            ("01 / MAKRO KAYDI", "Fare ve klavye olaylarını zamanlamalarıyla kaydeder."),
            ("02 / OYNATMA", "Seçilen makroyu bir kez veya döngü halinde oynatır."),
            ("03 / TIKLAMA MOTORU", "Sol veya sağ tuşla 1–60000 ms aralığında tıklar."),
            ("04 / GLOBAL KISAYOLLAR", "Uygulama arka plandayken eylemleri kontrol eder."),
        ):
            row = ttk.Frame(panel, style="HotkeyRow.TFrame", padding=(12, 10))
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=label, style="Row.TLabel").pack(anchor="w")
            ttk.Label(row, text=description, style="RowHint.TLabel").pack(
                anchor="w", pady=(3, 0)
            )
        ttk.Label(
            panel,
            text=f"DEVELOPED BY ARAS   /   VERSION {APP_VERSION}",
            style="Telemetry.TLabel",
        ).pack(anchor="w", pady=(16, 0))

    def _update_statistics_values(self) -> None:
        if not hasattr(self, "statistics_vars"):
            return
        selected_path = self._selected_path()
        selected_events = (
            str(self.selected_macro_event_count)
            if selected_path is not None
            and self.selected_macro_event_count is not None
            else "—"
        )
        elapsed = int(time.perf_counter() - self.app_started)
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        try:
            interval = int(self.interval_var.get().strip())
            click_rate = f"{1000 / interval:.1f} CPS" if interval > 0 else "—"
        except ValueError:
            click_rate = "—"
        values = {
            "Kayıtlı makro": str(len(self.recording_files)),
            "Toplam makro olayı": str(self.macro_event_total),
            "Okunamayan makro": str(self.invalid_macro_count),
            "Bu oturum tıklaması": str(self.click_count),
            "Seçili makro": selected_path.stem if selected_path else "—",
            "Seçili makro olayı": selected_events,
            "Geçen oturum süresi": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            "Ayarlanan tıklama hızı": click_rate,
        }
        for label, value in values.items():
            self.statistics_vars[label].set(value)
    def _build_settings_tab(self) -> None:
        card = self._create_hud_panel(
            self.settings_tab, "CONTROL PANEL // HOTKEY MATRIX", height=490
        )
        heading = ttk.Frame(card, style="Card.TFrame")
        heading.pack(fill="x")
        ttk.Label(heading, text="Kısayollarını kişiselleştir", style="Section.TLabel").pack(
            side="left", anchor="w"
        )
        ttk.Label(heading, text="5 EYLEM", style="Count.TLabel").pack(side="right")
        ttk.Label(
            card,
            text="Her eylem için ayrı bir tuş seç. Değişiklikler anında kaydedilir ve uygulama arka plandayken de çalışır.",
            style="Hint.TLabel",
            wraplength=650,
        ).pack(anchor="w", pady=(5, 16))

        self.hotkey_vars: dict[str, tk.StringVar] = {}
        self.hotkey_buttons: dict[str, ttk.Button] = {}
        for index, (action, label) in enumerate(HOTKEY_LABELS.items(), start=1):
            row = ttk.Frame(card, style="HotkeyRow.TFrame", padding=(13, 11))
            row.pack(fill="x", pady=4)
            ttk.Label(
                row, text=f"{index:02d}", style="RowIndex.TLabel"
            ).pack(side="left", padx=(0, 13))
            label_block = ttk.Frame(row, style="HotkeyRow.TFrame")
            label_block.pack(side="left", fill="x", expand=True)
            ttk.Label(label_block, text=label, style="Row.TLabel").pack(
                anchor="w"
            )
            ttk.Label(
                label_block,
                text=HOTKEY_DESCRIPTIONS[action],
                style="RowHint.TLabel",
            ).pack(anchor="w", pady=(3, 0))
            assignment = ttk.Frame(row, style="HotkeyRow.TFrame")
            assignment.pack(side="right")
            variable = tk.StringVar(value=self._hotkey_display(self.hotkeys[action]))
            self.hotkey_vars[action] = variable
            value_label = ttk.Label(assignment, textvariable=variable, style="Key.TLabel")
            value_label.pack(side="left", padx=(8, 10))
            value_label.configure(anchor="center")
            button = ttk.Button(
                assignment,
                text="Değiştir",
                command=lambda selected=action: self.begin_hotkey_capture(selected),
            )
            button.pack(side="left")
            self.hotkey_buttons[action] = button

        ttk.Separator(card, orient="horizontal").pack(fill="x", pady=(14, 13))
        footer = ttk.Frame(card, style="Card.TFrame")
        footer.pack(fill="x")
        ttk.Button(
            footer,
            text="Varsayılanlara dön",
            command=self.reset_hotkeys,
        ).pack(side="left")
        ttk.Label(
            footer,
            text="Esc: atamayı kaldır  •  Aynı tuş iki kez kullanılamaz",
            style="Hint.TLabel",
        ).pack(side="right", padx=(8, 0))

    def _refresh_hotkey_values(self) -> None:
        for action, variable in self.hotkey_vars.items():
            value = self._hotkey_display(
                self.hotkeys.get(action, DEFAULT_HOTKEYS[action])
            )
            if variable.get() != value:
                variable.set(value)
        for action, variable in getattr(self, "dashboard_hotkey_vars", {}).items():
            variable.set(self._hotkey_display(self.hotkeys[action]))

    def _update_hotkey_button_labels(self) -> None:
        if not hasattr(self, "record_button"):
            return
        recording = self.mouse_listener is not None or self.keyboard_listener is not None
        self.record_button.configure(
            text=(
                f"Kaydı bitir ({self._hotkey_display(self.hotkeys['record'])})"
                if recording
                else f"Kaydı başlat ({self._hotkey_display(self.hotkeys['record'])})"
            )
        )
        self.play_button.configure(
            text=f"Seçileni oynat ({self._hotkey_display(self.hotkeys['play_once'])})"
        )
        self.loop_button.configure(
            text=(
                f"Tekrarı durdur ({self._hotkey_display(self.hotkeys['play_loop'])})"
                if self.play_loop
                else f"Tekrarı başlat ({self._hotkey_display(self.hotkeys['play_loop'])})"
            )
        )
        self.stop_button.configure(
            text=f"Durdur ({self._hotkey_display(self.hotkeys['stop'])})"
        )
        if hasattr(self, "click_hotkey_label"):
            self.click_hotkey_label.configure(
                text=f"KISAYOL  {self._hotkey_display(self.hotkeys['click_loop'])}"
            )
        if hasattr(self, "click_start_button"):
            self.click_start_button.configure(
                text=(
                    f"Durdur ({self._hotkey_display(self.hotkeys['click_loop'])})"
                    if self.click_loop
                    else f"Başlat ({self._hotkey_display(self.hotkeys['click_loop'])})"
                )
            )
        self._refresh_hotkey_values()

    def _safe_status(self, message: str) -> None:
        if not self.root.winfo_exists():
            return
        try:
            self.status_var.set(message)
        except (AttributeError, tk.TclError):
            pass

    def _safe_button_text(self, widget: ttk.Button | None, text: str) -> None:
        if widget is None or not self.root.winfo_exists():
            return
        try:
            widget.configure(text=text)
        except tk.TclError:
            pass

    def _set_hotkey_capture_state(self, action: str, capturing: bool) -> None:
        button = self.hotkey_buttons.get(action)
        if button is None or not self.root.winfo_exists():
            return
        self._safe_button_text(
            button, "Bir tuşa bas..." if capturing else "Değiştir"
        )
        try:
            button.configure(style="Capture.TButton" if capturing else "TButton")
        except tk.TclError:
            pass

    def _start_hotkey_listener(self) -> None:
        try:
            self.hotkey_listener = keyboard.Listener(
                on_press=self._on_hotkey_press,
                on_release=self._on_hotkey_release,
            )
            self.hotkey_listener.start()
            self.hotkey_badge_var.set("●  GLOBAL KISAYOLLAR AKTİF")
            self.hotkey_badge.configure(style="HeaderBadge.TLabel")
        except Exception as exc:
            self.hotkey_listener = None
            self.hotkey_badge_var.set("●  GLOBAL KISAYOLLAR DEVRE DIŞI")
            self.hotkey_badge.configure(style="HeaderBadgeOff.TLabel")
            messagebox.showerror(
                "Kısayollar başlatılamadı",
                f"Global tuş dinleyicisi başlatılamadı.\n{exc}",
                parent=self.root,
            )

    def _on_hotkey_press(self, key: Key | KeyCode) -> None:
        name = key_name(key)
        if name is not None:
            self._hotkey_events.put(("press", name))

    def _on_hotkey_release(self, key: Key | KeyCode) -> None:
        name = key_name(key)
        if name is not None:
            self._hotkey_events.put(("release", name))

    def _process_hotkey_events(self) -> None:
        if self._closing or not self.root.winfo_exists():
            return
        while True:
            try:
                count = self._recording_count_events.get_nowait()
            except queue.Empty:
                break
            self._update_event_count(count)
        while True:
            try:
                event_type, name = self._hotkey_events.get_nowait()
            except queue.Empty:
                break
            if event_type == "release":
                self.pressed_keys.discard(name)
                continue
            if name in self.pressed_keys:
                continue
            self.pressed_keys.add(name)
            if self.capture_hotkey is not None:
                action = self.capture_hotkey
                self.capture_hotkey = None
                self._set_hotkey_capture_state(action, capturing=False)
                if name == "ESC":
                    self._remove_hotkey(action)
                else:
                    self._apply_hotkey(action, name)
                continue
            for action, assigned in self.hotkeys.items():
                if assigned != "-" and name == assigned:
                    self._run_hotkey_action(action)
                    break
        self.root.after(30, self._process_hotkey_events)

    def _run_hotkey_action(self, action: str) -> None:
        if action == "record":
            self.toggle_recording()
        elif action == "play_once":
            self.play_selected_once()
        elif action == "play_loop":
            self.toggle_playback_loop()
        elif action == "click_loop":
            self.toggle_clicking()
        elif action == "stop":
            self.stop_all()

    def begin_hotkey_capture(self, action: str) -> None:
        if self.capture_hotkey is not None:
            self._set_hotkey_capture_state(self.capture_hotkey, capturing=False)
        self.capture_hotkey = action
        self._set_hotkey_capture_state(action, capturing=True)
        self._safe_status(
            f"{HOTKEY_LABELS[action]} için bir tuşa bas. Esc, atamayı kaldırır."
        )

    def _remove_hotkey(self, action: str) -> None:
        self.hotkeys[action] = "-"
        self._refresh_hotkey_values()
        self._update_hotkey_button_labels()
        self._save_hotkeys()
        self._safe_status(f"{HOTKEY_LABELS[action]} kısayol ataması kaldırıldı.")

    def _apply_hotkey(self, action: str, name: str) -> None:
        if self.root is None or not self.root.winfo_exists():
            return
        normalized_name = name.upper()
        duplicates = [
            other_action
            for other_action, assigned in self.hotkeys.items()
            if other_action != action
            and assigned != "-"
            and assigned == normalized_name
        ]
        if duplicates:
            messagebox.showerror(
                "Tuş zaten atanmış",
                "Her işlem için farklı bir kısayol tuşu seçmelisin.",
                parent=self.root,
            )
            self._set_hotkey_capture_state(action, capturing=False)
            self._safe_status("Kısayol değiştirilmedi; bu tuş zaten kullanımda.")
            return
        self.hotkeys[action] = normalized_name
        self._refresh_hotkey_values()
        self._set_hotkey_capture_state(action, capturing=False)
        self._update_hotkey_button_labels()
        self._save_hotkeys()
        self._safe_status(f"{HOTKEY_LABELS[action]} kısayolu {normalized_name} olarak ayarlandı.")

    def reset_hotkeys(self) -> None:
        self.capture_hotkey = None
        self.hotkeys = DEFAULT_HOTKEYS.copy()
        for action in self.hotkey_vars:
            self._set_hotkey_capture_state(action, capturing=False)
        self._update_hotkey_button_labels()
        self._save_hotkeys()
        self._safe_status("Varsayılan kısayollar geri yüklendi.")

    def _refresh_recording_list(self, select: Path | None = None) -> None:
        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(
            RECORDINGS_DIR.glob("Kayıt *.json"),
            key=lambda path: int(path.stem.removeprefix("Kayıt "))
            if path.stem.removeprefix("Kayıt ").isdigit()
            else 0,
        )
        self.recording_files = files
        count = len(files)
        self.recording_count_var.set(f"{count} KAYIT" if count != 1 else "1 KAYIT")
        self._recalculate_macro_statistics()
        self.recording_list.delete(0, tk.END)
        for path in files:
            self.recording_list.insert(tk.END, path.stem)
        if files:
            self.empty_recordings_label.place_forget()
        else:
            self.empty_recordings_label.place(relx=0.5, rely=0.5, anchor="center")
        if select in files:
            index = files.index(select)
            self.recording_list.selection_set(index)
            self.recording_list.activate(index)
            self._select_recording()
        elif files and not self.recording_list.curselection():
            self.recording_list.selection_set(0)
            self._select_recording()
        if not files:
            self._select_recording()
            self.play_button.configure(state="disabled")
            self.loop_button.configure(state="disabled")

    def _selected_path(self) -> Path | None:
        selected = self.recording_list.curselection()
        if not selected:
            return None
        index = selected[0]
        if index >= len(self.recording_files):
            return None
        return self.recording_files[index]

    def _recalculate_macro_statistics(self) -> None:
        self.macro_event_total = 0
        self.invalid_macro_count = 0
        for path in self.recording_files:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                self.invalid_macro_count += 1
                continue
            events = data.get("events") if isinstance(data, dict) else None
            if not isinstance(events, list):
                self.invalid_macro_count += 1
                continue
            self.macro_event_total += len(events)

    def _select_recording(self, _event: tk.Event[Any] | None = None) -> None:
        path = self._selected_path()
        enabled = path is not None
        self.play_button.configure(state="normal" if enabled else "disabled")
        self.loop_button.configure(state="normal" if enabled else "disabled")
        self.selected_macro_event_count = None
        if path is not None:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = None
            if isinstance(data, dict) and isinstance(data.get("events"), list):
                self.selected_macro_event_count = len(data["events"])
        self._update_statistics_values()

    def toggle_recording(self) -> None:
        if self.mouse_listener is not None or self.keyboard_listener is not None:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self) -> None:
        if self.mouse_listener is not None or self.keyboard_listener is not None:
            return
        self.stop_playback()
        self.stop_clicking()
        with self.recording_lock:
            self.events = []
            self.event_counts = {"click": 0, "move": 0, "key": 0}
            self.recording_started = time.perf_counter()
            self.recording_duration = 0.0
            self.last_move_at = 0.0
            self.last_position = None
        try:
            self.mouse_listener = mouse.Listener(
                on_move=self._on_move,
                on_click=self._on_click,
            )
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release,
            )
            self.mouse_listener.start()
            self.keyboard_listener.start()
        except Exception as exc:
            self.stop_recording(save=False)
            messagebox.showerror("Kayıt başlatılamadı", str(exc), parent=self.root)
            return
        self._update_hotkey_button_labels()
        self.status_var.set(
            "Kayıt başladı. İşlemlerini yap; bitirmek için tekrar "
            f"{self.hotkeys['record']}'ya bas."
        )

    def _inside_window(self, x: int, y: int) -> bool:
        if self._window_bounds is None:
            return False
        left, top, width, height = self._window_bounds
        return (
            left <= x < left + width
            and top <= y < top + height
        )

    def _update_window_bounds(self, _event: tk.Event[Any] | None = None) -> None:
        self._window_bounds = (
            self.root.winfo_rootx(),
            self.root.winfo_rooty(),
            self.root.winfo_width(),
            self.root.winfo_height(),
        )

    def _append_event(self, event: dict[str, Any]) -> None:
        with self.recording_lock:
            event["time"] = max(0.0, time.perf_counter() - self.recording_started)
            self.events.append(event)
            event_type = event.get("type")
            if event_type in self.event_counts:
                self.event_counts[event_type] += 1
            count = len(self.events)
        self._recording_count_events.put(count)

    def _update_event_count(self, count: int) -> None:
        if count and (
            self.mouse_listener is not None or self.keyboard_listener is not None
        ):
            self.status_var.set(f"Kayıt sürüyor: {count} olay.")

    def _on_move(self, x: int, y: int) -> None:
        if self._inside_window(x, y):
            return
        now = time.perf_counter()
        position = (int(x), int(y))
        if position == self.last_position or now - self.last_move_at < 0.008:
            return
        self.last_position = position
        self.last_move_at = now
        self._append_event({"type": "move", "x": position[0], "y": position[1]})

    def _on_click(self, x: int, y: int, button: Button, pressed: bool) -> None:
        if not self._inside_window(x, y):
            self._append_event(
                {
                    "type": "click",
                    "x": int(x),
                    "y": int(y),
                    "button": button.name,
                    "pressed": pressed,
                }
            )

    @staticmethod
    def _serialize_key(key: Key | KeyCode) -> dict[str, str]:
        if isinstance(key, KeyCode) and key.char is not None:
            return {"kind": "char", "value": key.char}
        if isinstance(key, Key) and key.name is not None:
            return {"kind": "special", "value": key.name}
        raise ValueError(f"Desteklenmeyen klavye tuşu: {key!r}")

    def _is_hotkey(self, key: Key | KeyCode) -> bool:
        name = key_name(key)
        return name is not None and name in self.hotkeys.values()

    def _on_key_press(self, key: Key | KeyCode) -> None:
        if self._is_hotkey(key):
            return
        try:
            self._append_event(
                {
                    "type": "key",
                    "action": "press",
                    "key": self._serialize_key(key),
                }
            )
        except ValueError:
            return

    def _on_key_release(self, key: Key | KeyCode) -> None:
        if self._is_hotkey(key):
            return
        try:
            self._append_event(
                {
                    "type": "key",
                    "action": "release",
                    "key": self._serialize_key(key),
                }
            )
        except ValueError:
            return

    def stop_recording(self, save: bool = True) -> None:
        if self.mouse_listener is None and self.keyboard_listener is None:
            return
        for listener in (self.mouse_listener, self.keyboard_listener):
            if listener is not None:
                listener.stop()
        self.mouse_listener = None
        self.keyboard_listener = None
        with self.recording_lock:
            self.recording_duration = max(
                0.0, time.perf_counter() - self.recording_started
            )
            events = list(self.events)
            duration = self.recording_duration
        self._update_hotkey_button_labels()
        if not save:
            self.status_var.set("Kayıt iptal edildi.")
            return
        if not events:
            self.status_var.set("Kayıt tamamlandı; kaydedilecek olay yok.")
            return

        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        next_number = 1
        while (RECORDINGS_DIR / f"Kayıt {next_number}.json").exists():
            next_number += 1
        path = RECORDINGS_DIR / f"Kayıt {next_number}.json"
        try:
            path.write_text(
                json.dumps(
                    {
                        "format": "auto-clicker-macro",
                        "version": 1,
                        "duration": duration,
                        "events": events,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except OSError as exc:
            messagebox.showerror(
                "Kayıt saklanamadı",
                f"Makro dosyaya yazılamadı:\n{path}\n\n{exc}",
                parent=self.root,
            )
            self.status_var.set("Kayıt durdu ancak dosyaya kaydedilemedi.")
            return
        self._refresh_recording_list(select=path)
        self.status_var.set(f"Kayıt tamamlandı ve {path.name} olarak saklandı.")

    @staticmethod
    def _validate_macro(data: Any) -> tuple[list[dict[str, Any]], float]:
        if not isinstance(data, dict) or data.get("format") != "auto-clicker-macro":
            raise ValueError("Dosya geçerli bir Makro kaydı değil.")
        if data.get("version") != 1 or not isinstance(data.get("events"), list):
            raise ValueError("Makro dosyasının sürümü veya biçimi desteklenmiyor.")
        duration = data.get("duration", 0)
        if not isinstance(duration, (int, float)) or duration < 0:
            raise ValueError("Makro süresi geçersiz.")
        events = data["events"]
        for event in events:
            if not isinstance(event, dict):
                raise ValueError("Makroda geçersiz olay var.")
            timestamp = event.get("time")
            if not isinstance(timestamp, (int, float)) or timestamp < 0:
                raise ValueError("Makroda geçersiz olay zamanı var.")
            event_type = event.get("type")
            if event_type == "move":
                if not isinstance(event.get("x"), int) or not isinstance(
                    event.get("y"), int
                ):
                    raise ValueError("Makroda geçersiz fare konumu var.")
            elif event_type == "click":
                if (
                    not isinstance(event.get("x"), int)
                    or not isinstance(event.get("y"), int)
                    or event.get("button") not in ("left", "right", "middle")
                    or not isinstance(event.get("pressed"), bool)
                ):
                    raise ValueError("Makroda geçersiz fare tıklaması var.")
            elif event_type == "key":
                key_data = event.get("key")
                if (
                    event.get("action") not in ("press", "release")
                    or not isinstance(key_data, dict)
                    or key_data.get("kind") not in ("char", "special")
                    or not isinstance(key_data.get("value"), str)
                    or not key_data["value"]
                    or (key_data["kind"] == "char" and len(key_data["value"]) != 1)
                    or (
                        key_data["kind"] == "special"
                        and not hasattr(Key, key_data["value"])
                    )
                ):
                    raise ValueError("Makroda geçersiz klavye tuşu var.")
            else:
                raise ValueError("Makroda tanınmayan olay türü var.")
        return events, float(duration)

    def _load_selected_macro(self) -> bool:
        path = self._selected_path()
        if path is None:
            self.status_var.set("Önce listeden bir kayıt seç.")
            return False
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            events, duration = self._validate_macro(data)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            messagebox.showerror(
                "Kayıt açılamadı",
                f"{path.name} okunamadı:\n{exc}",
                parent=self.root,
            )
            return False
        if not events:
            self.status_var.set("Seçilen kayıt boş.")
            return False
        self.events = events
        self.event_counts = {"click": 0, "move": 0, "key": 0}
        for event in events:
            event_type = event.get("type")
            if event_type in self.event_counts:
                self.event_counts[event_type] += 1
        self.recording_duration = duration
        return True

    def play_selected_once(self) -> None:
        if self.mouse_listener is not None or self.keyboard_listener is not None:
            self.status_var.set(
                f"Oynatmadan önce {self.hotkeys['record']} ile kaydı bitir."
            )
            return
        if self._load_selected_macro():
            self._start_playback(loop=False)

    def toggle_playback_loop(self) -> None:
        if self.play_loop:
            self.stop_playback()
            return
        if self.mouse_listener is not None or self.keyboard_listener is not None:
            self.status_var.set(
                f"Oynatmadan önce {self.hotkeys['record']} ile kaydı bitir."
            )
            return
        if self._load_selected_macro():
            self._start_playback(loop=True)

    def _start_playback(self, loop: bool) -> None:
        self.stop_clicking()
        self.stop_playback()
        self.play_token += 1
        self.play_events = list(self.events)
        self.play_duration = max(
            self.recording_duration,
            max(float(event["time"]) for event in self.play_events),
        )
        self.play_loop = loop
        self.play_index = 0
        self.play_started = time.perf_counter()
        self._update_hotkey_button_labels()
        if loop:
            self.status_var.set(
                "Makro sürekli oynatılıyor; durdurmak için tekrar "
                f"{self.hotkeys['play_loop']} veya {self.hotkeys['stop']}."
            )
        else:
            self.status_var.set("Seçilen makro bir kez oynatılıyor.")
        self._schedule_next_play_event(self.play_token)

    def _schedule_next_play_event(self, token: int) -> None:
        if token != self.play_token or not self.root.winfo_exists():
            return
        if self.play_index >= len(self.play_events):
            if not self.play_loop:
                self._finish_playback("Makro oynatma tamamlandı.")
                return
            loop_end = self.play_started + self.play_duration
            self.root.after(
                max(0, round((loop_end - time.perf_counter()) * 1000)),
                self._begin_next_play_loop,
                token,
            )
            return
        event = self.play_events[self.play_index]
        due = self.play_started + float(event["time"])
        self.root.after(
            max(0, round((due - time.perf_counter()) * 1000)),
            self._play_next_event,
            token,
        )

    def _begin_next_play_loop(self, token: int) -> None:
        if token != self.play_token or not self.root.winfo_exists():
            return
        self.play_index = 0
        self.play_started = time.perf_counter()
        self._schedule_next_play_event(token)

    def _play_next_event(self, token: int) -> None:
        if (
            token != self.play_token
            or self.play_index >= len(self.play_events)
            or not self.root.winfo_exists()
        ):
            return
        try:
            self._execute_event(self.play_events[self.play_index])
        except Exception as exc:
            self._finish_playback("Oynatma hata nedeniyle durduruldu.")
            if self.root.winfo_exists():
                messagebox.showerror("Makro oynatılamadı", str(exc), parent=self.root)
            return
        self.play_index += 1
        self._schedule_next_play_event(token)

    def _execute_event(self, event: dict[str, Any]) -> None:
        if event["type"] == "move":
            mouse.Controller().position = (int(event["x"]), int(event["y"]))
        elif event["type"] == "click":
            controller = mouse.Controller()
            controller.position = (int(event["x"]), int(event["y"]))
            button = getattr(Button, event["button"])
            if event["pressed"]:
                controller.press(button)
                self.held_buttons[event["button"]] = button
            else:
                controller.release(button)
                self.held_buttons.pop(event["button"], None)
        elif event["type"] == "key":
            key_data = event["key"]
            key = (
                KeyCode.from_char(key_data["value"])
                if key_data["kind"] == "char"
                else key_from_name(key_data["value"])
            )
            token = f'{key_data["kind"]}:{key_data["value"]}'
            controller = keyboard.Controller()
            if event["action"] == "press":
                controller.press(key)
                self.held_keys[token] = key
            else:
                controller.release(key)
                self.held_keys.pop(token, None)

    def _release_held_inputs(self) -> None:
        if self.held_buttons:
            mouse_controller = mouse.Controller()
            for button in self.held_buttons.values():
                mouse_controller.release(button)
            self.held_buttons.clear()
        if self.held_keys:
            keyboard_controller = keyboard.Controller()
            for key in self.held_keys.values():
                keyboard_controller.release(key)
            self.held_keys.clear()

    def stop_playback(self) -> None:
        self.play_token += 1
        was_playing = bool(self.play_events)
        self.play_loop = False
        self.play_events = []
        self._release_held_inputs()
        self._update_hotkey_button_labels()
        if was_playing:
            self.status_var.set("Makro oynatma durduruldu.")

    def _finish_playback(self, status: str) -> None:
        self.play_token += 1
        self.play_loop = False
        self.play_events = []
        self._release_held_inputs()
        self._update_hotkey_button_labels()
        self.status_var.set(status)

    def toggle_clicking(self) -> None:
        if self.click_loop:
            self.stop_clicking()
            return
        self.start_clicking()

    def start_clicking(self) -> None:
        if self.click_loop:
            return
        if self.mouse_listener is not None or self.keyboard_listener is not None:
            self.status_var.set(
                f"Tıklamadan önce kaydı {self.hotkeys['record']} ile bitir."
            )
            return
        try:
            interval = int(self.interval_var.get().strip())
            if interval < 1 or interval > 60000:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Geçersiz aralık",
                "Tıklama aralığı 1 ile 60000 ms arasında tam sayı olmalı.",
                parent=self.root,
            )
            return
        self.stop_playback()
        self.click_button = Button.left if self.button_var.get() == "left" else Button.right
        self.click_loop = True
        self.click_token += 1
        self._update_hotkey_button_labels()
        self.status_var.set(
            f"Sürekli {self.button_var.get()} tıklama başladı. Durdurmak için "
            f"{self.hotkeys['click_loop']} veya {self.hotkeys['stop']}."
        )
        self._perform_click(self.click_token, interval)

    def _perform_click(self, token: int, interval: int) -> None:
        if (
            token != self.click_token
            or not self.click_loop
            or self.click_button is None
            or not self.root.winfo_exists()
        ):
            return
        try:
            mouse.Controller().click(self.click_button)
        except Exception as exc:
            self.stop_clicking()
            if self.root.winfo_exists():
                messagebox.showerror("Tıklama başarısız", str(exc), parent=self.root)
            return
        self.click_count += 1
        self.root.after(interval, self._perform_click, token, interval)

    def stop_clicking(self) -> None:
        was_clicking = self.click_loop
        self.click_token += 1
        self.click_loop = False
        self.click_button = None
        self._update_hotkey_button_labels()
        if was_clicking:
            self.status_var.set("Sürekli tıklama durduruldu.")

    def stop_all(self) -> None:
        if self.capture_hotkey is not None:
            self._set_hotkey_capture_state(self.capture_hotkey, capturing=False)
        self.capture_hotkey = None
        if self.mouse_listener is not None or self.keyboard_listener is not None:
            self.stop_recording()
        self.stop_playback()
        self.stop_clicking()
        self.status_var.set("Tüm işlemler durduruldu.")

    def _on_close(self) -> None:
        self._closing = True
        if self.capture_hotkey is not None:
            self._set_hotkey_capture_state(self.capture_hotkey, capturing=False)
        self.capture_hotkey = None
        if self.mouse_listener is not None or self.keyboard_listener is not None:
            self.stop_recording()
        self.stop_playback()
        self.stop_clicking()
        if self.hotkey_listener is not None:
            self.hotkey_listener.stop()
        self.root.destroy()


def main() -> None:
    if not getattr(sys, "frozen", False):
        settings = _load_settings()
        install_state = (
            settings.get("install", {}) if isinstance(settings, dict) else {}
        )
    else:
        install_state = {"completed": True}
    if not install_state.get("completed"):
        wizard = InstallerWizard()
        wizard.root.mainloop()
        if not wizard.completed:
            return

    root = tk.Tk()
    AutoClickerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
