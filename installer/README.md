# Monad-Ultron Installer

## Quick start

1. Plug your 128 GB USB into your desktop
2. Double-click **`install_to_usb.bat`**
3. Confirm the USB drive letter when prompted
4. Wait ~10–30 minutes (mostly model downloads)
5. Eject, plug into your laptop, double-click `monad.bat` on the USB

## Advanced (command line)

```bash
python install_to_usb.py --drive E:
python install_to_usb.py --drive E: --skip-models
python install_to_usb.py --drive E: --skip-python --skip-models  # code only
```

## What gets installed on the USB

```
E:/Monad-Ultron/
├── monad/                # Python source
├── config.yaml
├── models.yaml
├── models/               # GGUF files (~15 GB total)
│   ├── longcat2/longcat2-q4_k_m.gguf
│   ├── glm5/glm5-q4_k_m.gguf
│   └── llama2/llama2-7b-chat-q4_k_m.gguf
├── python_portable/      # Embeddable Python 3.12 (~4 GB with deps)
├── memory_data/
├── workspace/
├── logs/
├── cache/
├── monad.bat             # ⭐ Double-click to start
└── monad-cli.bat         # CLI mode
```

## Troubleshooting

**"Python is not installed"** — install Python 3.12 from https://python.org on your desktop first.

**Model 404 errors** — LongCat 2 and GLM-5 URLs are best-effort placeholders. Edit `models.yaml` with the correct Hugging Face URL, or manually drop the GGUF into `models/<id>/`.

**pip install fails inside embeddable Python** — the embeddable distribution has a quirky pip bootstrap. If it fails, use a regular Python venv on the USB instead (see `docs/INSTALL.md`).
