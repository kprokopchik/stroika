"""Сборка сайта: python3 build.py → docs/ (публикуется через GitHub Pages из папки /docs)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))

from site_gen import build_site  # noqa: E402

if __name__ == "__main__":
    build_site(ROOT)
