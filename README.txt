
 WALLPAPER RENAMER
 AI-powered wallpaper renaming using local Moondream2
═══════════════════════════════════════════════════════

 FIRST TIME SETUP (do this once)
─────────────────────────────────
 1. Install Python from https://python.org
    → During install, check "Add Python to PATH" ✓

 2. Drop your Moondream2 .gguf files into the /models folder:
      models/moondream2-mmproj-f16-20250414.gguf
      models/moondream2-text-model-f16_ct-vicuna.gguf

 3. Double-click install_deps.bat
    → This installs the required packages (one time only)

 RUNNING THE APP
─────────────────
 Double-click run.bat

 HOW TO USE
─────────────
 1. The app auto-detects your models from /models
 2. Click Browse and select your wallpaper folder
 3. Toggle "Dry run" ON first to preview names safely
 4. Click Start — watch the log for results
 5. If names look good, uncheck Dry run and run again

 OUTPUT FORMAT
───────────────
 Files are renamed to clean human-readable names:
   wallpaper_001.jpg  →  Purple nebula galaxy night sky.jpg
   img_293.png        →  Snowy mountain peak sunrise.png

 NOTES
───────
 - Original files are only renamed, never deleted or copied
 - Duplicate names get a number suffix automatically
 - The app works fully offline — no internet needed
 - Models stay in /models, move the whole folder freely

═══════════════════════════════════════════════════════
