# Installing Monad-Ultron

## Prerequisites (desktop)

- **Windows 11** (installer is Windows-only for now)
- **Python 3.12+** ([download](https://python.org/downloads))
- **128 GB USB 3.2 drive** (empty or with ~40 GB free)
- **Stable internet** (needs to download ~15 GB of models)

## One-click install (recommended)

1. Download this repo (green "Code" button → Download ZIP)
2. Extract anywhere on your desktop
3. Plug in your USB drive
4. Double-click `installer/install_to_usb.bat`
5. Confirm the USB drive letter when prompted
6. Wait 10–30 minutes
7. Eject USB, plug into laptop, double-click `monad.bat` at the USB root

## Command-line install (advanced)

```powershell
cd Monad-Ultron
python installer\install_to_usb.py --drive E:
```

Skip flags for partial installs:
- `--skip-python` — don't download portable Python
- `--skip-models` — don't download GGUFs (dev workflow)
- `--skip-requirements` — don't `pip install`

## Manual install (fully manual)

1. Copy the whole `Monad-Ultron/` folder to the USB
2. Download & extract Python 3.12 embeddable ZIP to `USB\Monad-Ultron\python_portable\`
   - Enable `import site` in `python312._pth`
   - Bootstrap pip: `python.exe get-pip.py`
3. Install deps: `python.exe -m pip install -r requirements.txt`
4. Download the 3 GGUF models to `USB\Monad-Ultron\models\<id>\<filename>`
5. Copy `launcher\monad.bat` to `USB\Monad-Ultron\monad.bat`

## Verifying install

Plug USB into laptop, open Command Prompt at the USB root, and run:

```cmd
monad-cli.bat doctor
monad-cli.bat models
monad-cli.bat plugins
```

If `doctor` shows all green ticks, you're ready. Run `monad.bat` (or `monad-cli.bat chat`) to start chatting.

## Model files not downloading?

LongCat 2 and GLM-5 URLs in `models.yaml` are best-effort. If they 404:

1. Search Hugging Face for the current GGUF quantization
2. Update `models.yaml` with the correct URL
3. Re-run: `python installer\download_models.py`

Or drop the GGUF file manually at `models/<id>/<filename>` — the installer will detect it on next boot.
