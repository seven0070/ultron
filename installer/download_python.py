"""Download and extract Windows embeddable Python distribution."""

from __future__ import annotations

import io
import urllib.request
import zipfile
from pathlib import Path

import yaml


def _load_python_manifest() -> dict:
    manifest_path = Path(__file__).resolve().parents[1] / "models.yaml"
    with manifest_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data.get("python_portable", {})


def download_and_extract(target_dir: Path) -> None:
    manifest = _load_python_manifest()
    url = manifest.get("url")
    if not url:
        raise RuntimeError("No python_portable.url set in models.yaml")

    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"[i] Downloading Python from {url}")
    with urllib.request.urlopen(url) as resp:
        buf = io.BytesIO(resp.read())
    with zipfile.ZipFile(buf) as zf:
        zf.extractall(target_dir)
    print(f"[OK] Extracted to {target_dir}")

    # Enable site-packages by fixing python312._pth
    for pth in target_dir.glob("python*._pth"):
        content = pth.read_text(encoding="utf-8")
        if "#import site" in content:
            pth.write_text(content.replace("#import site", "import site"), encoding="utf-8")
            print(f"[OK] Enabled site-packages in {pth.name}")


if __name__ == "__main__":
    import sys
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "python_portable"
    download_and_extract(target)
