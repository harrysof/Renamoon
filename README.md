# Image Describer & Renamer

**AI-powered image renaming tool — runs fully offline using local Moondream2 GGUF models.**

Tired of images named `scan_001.jpg` or `img_293.png`? Image Describer scans any folder, describes each image using a local vision AI, and renames every file to something human-readable like `Purple nebula galaxy night sky.jpg`.

No internet required. No API keys. Everything runs on your machine.

---

## ✨ Features

- **Local AI vision** — uses [Moondream2 GGUF](https://huggingface.co/ggml-org/moondream2-20250414-GGUF/tree/main) via `llama-cpp-python`, no cloud calls
- **OCR integration** — EasyOCR extracts visible text (titles, labels) and appends it to the name
- **Dry run mode** — preview all generated names before touching any files
- **Collision handling** — duplicate names automatically get a numeric suffix
- **Dark UI** — clean tkinter interface with live log and progress bar
- **Portable** — move the whole folder anywhere, just keep `models/` next to `app.py`

---

## Requirements

- **Python 3.10 – 3.12** (get it from [python.org](https://python.org) — check *Add Python to PATH* during install)
- **~4 GB free disk space** for the models
- Windows (`.bat` scripts included; Linux/macOS users can run `app.py` directly)

---

## Quick Start

### 1 — Download the models

Go to the HuggingFace repo: **[ggml-org/moondream2-20250414-GGUF](https://huggingface.co/ggml-org/moondream2-20250414-GGUF/tree/main)**

Download both files and place them in the `models/` folder:

```
models/
├── moondream2-mmproj-f16-20250414.gguf        ← Vision encoder  (910 MB)
└── moondream2-text-model-f16_ct-vicuna.gguf   ← Text model      (2.84 GB)
```

### 2 — Install dependencies

Double-click **`install_deps.bat`** (first time only).

This installs:
- `Pillow` — image loading and resizing
- `llama-cpp-python` — CPU-only pre-built wheel for running GGUF models
- `easyocr` — OCR engine (~100 MB download on first run)

### 3 — Run the app

Double-click **`run.bat`** — or from a terminal:

```bash
python app.py
```

---

## How to Use

1. The app auto-detects models from the `models/` folder on launch
2. Click **Browse** and select your image folder
3. Toggle **Dry run ON** (default) to preview names safely
4. Click **▶ Start Renaming** — watch the log for results
5. If names look good, uncheck Dry run and run again to apply

---

## Project Structure

```
ImageDescriber/
├── app.py               ← Main application
├── run.bat              ← Launch script (Windows)
├── install_deps.bat     ← Dependency installer (Windows)
├── README.md
└── models/              ← Place your .gguf files here
    ├── moondream2-mmproj-f16-20250414.gguf
    └── moondream2-text-model-f16_ct-vicuna.gguf
```

---

## How It Works

For each image in the selected folder:

1. **EasyOCR** scans for visible text (game titles, artist watermarks, labels)
2. **Moondream2** generates a visual description (subject, style, mood, setting)
3. Both are combined into a clean filename slug — max 80 characters, word-boundary trimmed
4. The file is renamed (or just previewed if dry run is active)

**Example output:**
```
scan_001.jpg    →  Purple nebula galaxy night sky.jpg
img_293.png     →  Snowy mountain peak sunrise.png
DSC_4821.jpg    →  Two people laughing at outdoor cafe.jpg
screenshot.webp →  Python code editor dark theme terminal.webp
```

---

## ⚙️ Configuration

At the top of `app.py` you can tweak:

| Constant | Default | Description |
|---|---|---|
| `RESIZE_MAX` | `512` | Max image dimension sent to the model |
| `N_CTX` | `2048` | Context window size |
| `N_GPU_LAYERS` | `0` | GPU layers (0 = CPU only) |
| `MAX_TOKENS` | `80` | Max tokens for model response |
| `SUPPORTED_EXT` | `.jpg .jpeg .png .webp .bmp` | File types to process |

To enable GPU acceleration, set `N_GPU_LAYERS` to a positive number and install a CUDA build of `llama-cpp-python`.

---

## Notes

- Original files are **only renamed**, never deleted or copied
- The app works **fully offline** after models are downloaded
- EasyOCR downloads its own models (~100 MB) on first use — this is automatic
- Low-confidence OCR fragments and garbled text are filtered out automatically

---

## Manual Dependency Install (non-Windows)

```bash
pip install Pillow easyocr
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

---

## 📄 License

MIT — do whatever you want with it.

---

*Built with [Moondream2](https://huggingface.co/ggml-org/moondream2-20250414-GGUF/tree/main) · [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) · [EasyOCR](https://github.com/JaidedAI/EasyOCR)*
