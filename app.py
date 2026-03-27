"""
WallpaperRenamer — AI-powered wallpaper renaming tool
Uses local Moondream2 GGUF models to describe and rename images by content.
Drop your .gguf files in the /models folder next to this script.
"""

import os
import re
import sys
import base64
import threading
import tkinter as tk
from tkinter import filedialog, font
from pathlib import Path
from io import BytesIO

try:
    from PIL import Image, ImageTk
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "-q"])
    from PIL import Image, ImageTk

try:
    import easyocr
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "easyocr", "-q"])
    import easyocr

# ─── CONSTANTS ─────────────────────────────────────────────────────────────────

SUPPORTED_EXT  = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
RESIZE_MAX     = 512
N_CTX          = 2048
N_GPU_LAYERS   = 0
MAX_TOKENS     = 80

PROMPT_VISUAL = (
    "Describe this wallpaper in 10 words or fewer. "
    "Mention the main subject, art style, mood, and setting. "
    "Be specific: name characters, objects, colors, atmosphere. "
    "Reply with ONLY the description, no punctuation, no extra text."
)

# ─── COLORS ────────────────────────────────────────────────────────────────────

BG        = "#0e0e11"
BG2       = "#17171d"
BG3       = "#1f1f28"
BORDER    = "#2a2a38"
ACCENT    = "#7c6aff"
ACCENT2   = "#a78bfa"
TEXT      = "#e8e6f0"
TEXT_DIM  = "#6b6880"
SUCCESS   = "#4ade80"
WARNING   = "#facc15"
ERROR     = "#f87171"

# ───────────────────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.capitalize()
    # Trim at word boundary so we never cut mid-word
    if len(text) > 80:
        trimmed = text[:80]
        last_space = trimmed.rfind(" ")
        text = trimmed[:last_space] if last_space > 0 else trimmed
    return text


def image_to_data_uri(path: Path) -> str:
    with Image.open(path) as img:
        img = img.convert("RGB")
        img.thumbnail((RESIZE_MAX, RESIZE_MAX), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/jpeg;base64,{b64}"


def unique_path(folder: Path, stem: str, suffix: str) -> Path:
    candidate = folder / f"{stem}{suffix}"
    counter = 2
    while candidate.exists():
        candidate = folder / f"{stem} {counter}{suffix}"
        counter += 1
    return candidate


def find_gguf_files(models_dir: Path):
    """Auto-detect mmproj and text model from /models folder."""
    ggufs = list(models_dir.glob("*.gguf"))
    mmproj = next((f for f in ggufs if "mmproj" in f.name.lower()), None)
    text   = next((f for f in ggufs if "mmproj" not in f.name.lower()), None)
    return mmproj, text


# ─── GUI ───────────────────────────────────────────────────────────────────────

class WallpaperRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wallpaper Renamer")
        self.root.geometry("760x680")
        self.root.minsize(680, 580)
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.llm = None
        self.ocr = None
        self.running = False
        self.dry_run = tk.BooleanVar(value=True)
        self.folder_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0)

        self._setup_fonts()
        self._build_ui()
        self._auto_detect_models()

    def _setup_fonts(self):
        self.font_title  = font.Font(family="Segoe UI", size=20, weight="bold")
        self.font_sub    = font.Font(family="Segoe UI", size=9)
        self.font_label  = font.Font(family="Segoe UI", size=10, weight="bold")
        self.font_mono   = font.Font(family="Consolas", size=9)
        self.font_btn    = font.Font(family="Segoe UI", size=10, weight="bold")
        self.font_small  = font.Font(family="Segoe UI", size=8)

    def _build_ui(self):
        # ── Header
        header = tk.Frame(self.root, bg=BG, pady=0)
        header.pack(fill="x", padx=28, pady=(24, 0))

        title_row = tk.Frame(header, bg=BG)
        title_row.pack(fill="x")

        dot = tk.Canvas(title_row, width=10, height=10, bg=BG, highlightthickness=0)
        dot.pack(side="left", padx=(0, 10), pady=6)
        dot.create_oval(0, 0, 10, 10, fill=ACCENT, outline="")

        tk.Label(title_row, text="Wallpaper Renamer", font=self.font_title,
                 fg=TEXT, bg=BG).pack(side="left")

        tk.Label(header, text="AI-powered image renaming using local Moondream2",
                 font=self.font_sub, fg=TEXT_DIM, bg=BG).pack(anchor="w", pady=(2, 0))

        # ── Divider
        self._divider()

        # ── Model status card
        model_card = self._card()
        tk.Label(model_card, text="MODEL", font=self.font_small,
                 fg=TEXT_DIM, bg=BG2).pack(anchor="w")

        self.model_status = tk.Label(model_card, text="⟳  Detecting models...",
                                     font=self.font_mono, fg=WARNING, bg=BG2)
        self.model_status.pack(anchor="w", pady=(4, 0))

        self.mmproj_label = tk.Label(model_card, text="", font=self.font_mono,
                                     fg=TEXT_DIM, bg=BG2)
        self.mmproj_label.pack(anchor="w")

        self.text_label = tk.Label(model_card, text="", font=self.font_mono,
                                   fg=TEXT_DIM, bg=BG2)
        self.text_label.pack(anchor="w")

        # ── Folder picker
        folder_card = self._card()
        tk.Label(folder_card, text="WALLPAPER FOLDER", font=self.font_small,
                 fg=TEXT_DIM, bg=BG2).pack(anchor="w")

        row = tk.Frame(folder_card, bg=BG2)
        row.pack(fill="x", pady=(6, 0))

        self.folder_entry = tk.Entry(row, textvariable=self.folder_var,
                                     font=self.font_mono, bg=BG3, fg=TEXT,
                                     insertbackground=ACCENT, relief="flat",
                                     bd=0, highlightthickness=1,
                                     highlightbackground=BORDER,
                                     highlightcolor=ACCENT)
        self.folder_entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 8))

        self._btn(row, "Browse", self._browse_folder,
                  bg=BG3, fg=ACCENT2).pack(side="left")

        # ── Options row
        opts_card = self._card()
        opts_row = tk.Frame(opts_card, bg=BG2)
        opts_row.pack(fill="x")

        tk.Label(opts_row, text="OPTIONS", font=self.font_small,
                 fg=TEXT_DIM, bg=BG2).pack(anchor="w")

        dry_row = tk.Frame(opts_card, bg=BG2)
        dry_row.pack(fill="x", pady=(8, 0))

        self.dry_cb = tk.Checkbutton(dry_row, text="Dry run  (preview names without renaming)",
                                     variable=self.dry_run, font=self.font_sub,
                                     fg=TEXT, bg=BG2, selectcolor=BG3,
                                     activebackground=BG2, activeforeground=TEXT,
                                     relief="flat", bd=0,
                                     highlightthickness=0)
        self.dry_cb.pack(side="left")

        # ── Action button
        btn_frame = tk.Frame(self.root, bg=BG)
        btn_frame.pack(fill="x", padx=28, pady=(4, 0))

        self.run_btn = tk.Button(btn_frame, text="▶   Start Renaming",
                                 font=self.font_btn, bg=ACCENT, fg="white",
                                 relief="flat", bd=0, padx=20, pady=10,
                                 cursor="hand2", activebackground=ACCENT2,
                                 activeforeground="white",
                                 command=self._start)
        self.run_btn.pack(side="left")

        self.stop_btn = tk.Button(btn_frame, text="■   Stop",
                                  font=self.font_btn, bg=BG3, fg=TEXT_DIM,
                                  relief="flat", bd=0, padx=16, pady=10,
                                  cursor="hand2", activebackground=BORDER,
                                  activeforeground=TEXT,
                                  command=self._stop, state="disabled")
        self.stop_btn.pack(side="left", padx=(10, 0))

        # Status pill
        self.status_label = tk.Label(btn_frame, textvariable=self.status_var,
                                     font=self.font_small, fg=TEXT_DIM, bg=BG)
        self.status_label.pack(side="right", padx=(0, 4))

        # ── Progress bar (custom)
        pb_frame = tk.Frame(self.root, bg=BG)
        pb_frame.pack(fill="x", padx=28, pady=(10, 0))

        self.pb_bg = tk.Canvas(pb_frame, height=4, bg=BG3,
                               highlightthickness=0, relief="flat")
        self.pb_bg.pack(fill="x")
        self.pb_fill = None

        # ── Log
        log_frame = tk.Frame(self.root, bg=BG, pady=0)
        log_frame.pack(fill="both", expand=True, padx=28, pady=(14, 24))

        tk.Label(log_frame, text="LOG", font=self.font_small,
                 fg=TEXT_DIM, bg=BG).pack(anchor="w")

        log_wrap = tk.Frame(log_frame, bg=BORDER, bd=1)
        log_wrap.pack(fill="both", expand=True, pady=(4, 0))

        self.log = tk.Text(log_wrap, font=self.font_mono, bg=BG2, fg=TEXT,
                           relief="flat", bd=0, padx=14, pady=12,
                           wrap="word", state="disabled",
                           insertbackground=ACCENT,
                           selectbackground=ACCENT)
        self.log.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(log_wrap, command=self.log.yview, bg=BG2,
                                 troughcolor=BG2, relief="flat", bd=0)
        self.log.configure(yscrollcommand=scrollbar.set)

        # Tag colors
        self.log.tag_configure("accent",  foreground=ACCENT2)
        self.log.tag_configure("success", foreground=SUCCESS)
        self.log.tag_configure("warning", foreground=WARNING)
        self.log.tag_configure("error",   foreground=ERROR)
        self.log.tag_configure("dim",     foreground=TEXT_DIM)
        self.log.tag_configure("bold",    font=font.Font(family="Consolas", size=9, weight="bold"))

    # ── Helpers

    def _card(self):
        frame = tk.Frame(self.root, bg=BG2, bd=0, padx=16, pady=12,
                         highlightthickness=1, highlightbackground=BORDER)
        frame.pack(fill="x", padx=28, pady=(0, 10))
        return frame

    def _divider(self):
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(16, 14))

    def _btn(self, parent, text, cmd, bg=ACCENT, fg="white"):
        return tk.Button(parent, text=text, command=cmd, font=self.font_small,
                         bg=bg, fg=fg, relief="flat", bd=0, padx=12, pady=7,
                         cursor="hand2", activebackground=ACCENT2, activeforeground="white")

    def _log(self, msg, tag=None):
        self.log.configure(state="normal")
        if tag:
            self.log.insert("end", msg + "\n", tag)
        else:
            self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_status(self, msg, color=TEXT_DIM):
        self.status_var.set(msg)
        self.status_label.configure(fg=color)

    def _update_progress(self, done, total):
        self.pb_bg.update_idletasks()
        w = self.pb_bg.winfo_width()
        frac = done / total if total else 0
        fill_w = int(w * frac)
        self.pb_bg.delete("all")
        self.pb_bg.create_rectangle(0, 0, fill_w, 4, fill=ACCENT, outline="")

    # ── Logic

    def _auto_detect_models(self):
        script_dir = Path(__file__).parent
        models_dir = script_dir / "models"
        models_dir.mkdir(exist_ok=True)

        mmproj, text = find_gguf_files(models_dir)

        if mmproj and text:
            self.mmproj_path = mmproj
            self.text_path   = text
            self.model_status.configure(
                text=f"✓  Models found in /models", fg=SUCCESS)
            self.mmproj_label.configure(
                text=f"  Vision: {mmproj.name}", fg=TEXT_DIM)
            self.text_label.configure(
                text=f"  Text:   {text.name}", fg=TEXT_DIM)
            self._log("Models detected automatically from /models folder.", "success")
        else:
            self.mmproj_path = None
            self.text_path   = None
            self.model_status.configure(
                text="✗  No models found — place .gguf files in the /models folder", fg=ERROR)
            self._log("Put your Moondream2 .gguf files in the /models folder next to app.py.", "warning")

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select Wallpaper Folder")
        if folder:
            self.folder_var.set(folder)

    def _load_model(self):
        try:
            from llama_cpp import Llama
            from llama_cpp.llama_chat_format import MoondreamChatHandler
        except ImportError:
            self._log("llama-cpp-python not installed. Run: pip install llama-cpp-python", "error")
            return False

        self._log("Loading Moondream2...", "accent")
        self._set_status("Loading model...", WARNING)
        try:
            handler = MoondreamChatHandler(clip_model_path=str(self.mmproj_path))
            self.llm = Llama(
                model_path=str(self.text_path),
                chat_handler=handler,
                n_ctx=N_CTX,
                n_gpu_layers=N_GPU_LAYERS,
                verbose=False,
            )
            self._log("Model loaded.", "success")
            return True
        except Exception as e:
            self._log(f"Failed to load model: {e}", "error")
            return False

    def _init_ocr(self):
        if self.ocr is None:
            self._log("Loading EasyOCR (first run downloads ~100MB)...", "accent")
            self.ocr = easyocr.Reader(["en", "fr"], gpu=False, verbose=False)
            self._log("EasyOCR ready.", "success")

    def _extract_text(self, path: Path) -> str:
        """Use EasyOCR to extract visible text from the image."""
        try:
            self._init_ocr()
            results = self.ocr.readtext(str(path), detail=1, paragraph=False)

            pieces = []
            for (_, text, conf) in results:
                t = text.strip()
                # Skip low confidence
                if conf < 0.5:
                    continue
                # Skip very short fragments (likely OCR noise)
                if len(t) < 3:
                    continue
                # Skip all-caps single words that look like watermarks (e.g. DSAMAPOSTER)
                if t.isupper() and len(t.split()) == 1 and len(t) > 6:
                    continue
                # Skip words with mixed digits/letters that look garbled (e.g. Ire9)
                if re.search(r"[a-zA-Z]\d|\d[a-zA-Z]", t):
                    continue
                pieces.append(t)

            if not pieces:
                return ""
            combined = " ".join(pieces)
            combined = re.sub(r"\s+", " ", combined).strip()
            return combined[:50]
        except Exception as e:
            self._log(f"  OCR error: {e}", "warning")
            return ""

    def _describe(self, path: Path):
        try:
            # Step 1: OCR — extract visible text
            ocr_text = self._extract_text(path)
            has_text = len(ocr_text) > 2

            if has_text:
                self._log(f'  📝 OCR: "{ocr_text}"', "accent")

            # Step 2: Moondream — visual description
            data_uri = image_to_data_uri(path)
            response = self.llm.create_chat_completion(
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_uri}},
                        {"type": "text",      "text": PROMPT_VISUAL},
                    ],
                }],
                max_tokens=MAX_TOKENS,
                temperature=0.1,
            )
            visual = response["choices"][0]["message"]["content"].strip()

            # Step 3: combine
            if has_text:
                combined = f"{visual} {ocr_text}"
            else:
                combined = visual

            return combined

        except Exception as e:
            return None

    def _start(self):
        if not self.folder_var.get():
            self._log("Please select a wallpaper folder first.", "warning")
            return
        if not self.mmproj_path or not self.text_path:
            self._log("No models found. Place .gguf files in /models and restart.", "error")
            return

        self.running = True
        self.run_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        threading.Thread(target=self._run_rename, daemon=True).start()

    def _stop(self):
        self.running = False
        self._log("Stopping after current image...", "warning")
        self._set_status("Stopping...", WARNING)

    def _run_rename(self):
        folder = Path(self.folder_var.get())
        dry    = self.dry_run.get()

        images = [f for f in folder.iterdir()
                  if f.is_file() and f.suffix.lower() in SUPPORTED_EXT]

        if not images:
            self._log("No supported images found in that folder.", "warning")
            self._finish()
            return

        self._log(f"\n{'─'*48}", "dim")
        self._log(f"  Found {len(images)} image(s)  |  Dry run: {dry}", "accent")
        self._log(f"{'─'*48}", "dim")

        if not self.llm:
            if not self._load_model():
                self._finish()
                return

        renamed = skipped = 0

        for i, img_path in enumerate(images, 1):
            if not self.running:
                break

            self.root.after(0, self._update_progress, i, len(images))
            self._set_status(f"{i} / {len(images)}", ACCENT2)
            self._log(f"\n[{i}/{len(images)}]  {img_path.name}", "dim")

            desc = self._describe(img_path)
            if not desc:
                self._log("  ⚠  No description — skipped", "warning")
                skipped += 1
                continue

            slug = slugify(desc)
            if not slug:
                self._log("  ⚠  Empty name — skipped", "warning")
                skipped += 1
                continue

            new_path = unique_path(folder, slug, img_path.suffix.lower())

            if img_path.resolve() == new_path.resolve():
                self._log(f"  ✓  Already named correctly", "dim")
                skipped += 1
                continue

            self._log(f"  💬  {desc}", "accent")
            self._log(f"  →   {new_path.name}", "success")

            if not dry:
                img_path.rename(new_path)
            renamed += 1

        self._log(f"\n{'─'*48}", "dim")
        self._log(f"  Done.  Renamed: {renamed}  |  Skipped: {skipped}", "success")
        if dry:
            self._log("  ⚠  Dry run — no files were actually renamed.", "warning")
        self._log(f"{'─'*48}\n", "dim")

        self.root.after(0, self._update_progress, len(images), len(images))
        self._finish()

    def _finish(self):
        self.running = False
        self.root.after(0, lambda: self.run_btn.configure(state="normal"))
        self.root.after(0, lambda: self.stop_btn.configure(state="disabled"))
        self._set_status("Done", SUCCESS)


# ─── ENTRY ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    root.tk_setPalette(background=BG)
    try:
        root.iconbitmap(default="")
    except Exception:
        pass
    app = WallpaperRenamerApp(root)
    root.mainloop()
