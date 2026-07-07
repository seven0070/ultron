"""
Download all models listed in models.yaml to the target directory.

If a URL 404s (common for placeholder LongCat 2 / GLM-5 links), the installer
skips that model with a clear message. You can manually place the correct
GGUF file at models/<id>/<filename> later.
"""

from __future__ import annotations

import hashlib
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _download_with_progress(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"    → {url}")

    def _hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(100, downloaded * 100 // total_size)
            bar = "#" * (pct // 4) + "-" * (25 - pct // 4)
            mb = downloaded / (1024**2)
            total_mb = total_size / (1024**2)
            sys.stdout.write(f"\r      [{bar}] {pct:3d}%  {mb:7.1f} / {total_mb:.1f} MB")
            sys.stdout.flush()

    urllib.request.urlretrieve(url, dest, reporthook=_hook)
    print()


def download_all(manifest_path: Path, models_dir: Path) -> None:
    with manifest_path.open("r", encoding="utf-8") as fh:
        manifest = yaml.safe_load(fh) or {}

    models = manifest.get("models", [])
    if not models:
        print("[!] No models in models.yaml — nothing to download.")
        return

    print(f"[i] Downloading {len(models)} model(s) to {models_dir}")
    successes, failures = 0, []

    for m in models:
        mid = m["id"]
        filename = m["filename"]
        url = m.get("url", "")
        expected_sha = m.get("sha256", "").strip()
        target = models_dir / mid / filename

        print(f"\n[{mid}]  ({m.get('size_gb', '?')} GB)")

        if target.exists():
            print(f"    ✓ already present at {target}")
            successes += 1
            continue

        if not url:
            print(f"    [!] no URL for {mid} — skip. Place file manually at {target}")
            failures.append(mid)
            continue

        try:
            _download_with_progress(url, target)
        except urllib.error.HTTPError as e:
            print(f"    [X] HTTP {e.code} — URL may be wrong or model not released yet")
            print(f"        Fix: edit models.yaml with the correct URL, or drop the GGUF file at")
            print(f"        {target}")
            failures.append(mid)
            continue
        except Exception as e:
            print(f"    [X] download failed: {e}")
            failures.append(mid)
            continue

        if expected_sha:
            actual = _sha256(target)
            if actual.lower() != expected_sha.lower():
                print(f"    [X] SHA256 mismatch! expected {expected_sha}, got {actual}")
                target.unlink()
                failures.append(mid)
                continue
            print("    ✓ SHA256 verified")

        successes += 1
        print(f"    ✓ saved to {target}")

    print()
    print("=" * 60)
    print(f"  Model downloads: {successes}/{len(models)} succeeded")
    if failures:
        print(f"  Failed / skipped: {', '.join(failures)}")
        print("  → You can retry with: python installer/download_models.py")
        print("  → Or manually download and place at models/<id>/<filename>")
    print("=" * 60)


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[1]
    manifest = repo / "models.yaml"
    models_dir = repo / "models"
    download_all(manifest, models_dir)
