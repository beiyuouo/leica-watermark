from cairosvg import svg2png
import os
from pathlib import Path


ICONS_DIR = Path(__file__).parent / "asset" / "icons"


if __name__ == "__main__":
    for icon in ICONS_DIR.glob("*.svg"):
        svg2png(url=str(icon), write_to=str(icon.with_suffix(".png")), dpi=300)