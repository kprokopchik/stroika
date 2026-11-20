"""Готовит рендеры для сайта: сжимает и подписывает комнаты на виде сверху.

  python3 tools/post3d.py tmp/renders projects/kvartira-95/renders projects/kvartira-95
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SRC = Path(sys.argv[1])
DST = Path(sys.argv[2])
DST.mkdir(parents=True, exist_ok=True)
FONT_B = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
FONT_R = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"

# вид сверху: ортокамера над центром квартиры, кадр TOP_ORTHO м по высоте 1300 px
PROJECT = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(__file__).resolve().parent.parent / "projects" / "kvartira-95"
sys.path.insert(0, str(PROJECT))
import scene_cfg as CFG  # noqa: E402

CX, CY = CFG.DOLL["top"][0][0], CFG.DOLL["top"][0][1]
PX_PER_CM = 1300 / (CFG.TOP_ORTHO * 100)
LABELS = CFG.TOP_LABELS


def to_px(x, y):
    return 500 + (x - CX) * PX_PER_CM, 650 + (y - CY) * PX_PER_CM


for f in sorted(SRC.glob("v*-*.jpg")):
    im = Image.open(f).convert("RGB")
    if f.stem.endswith("-top"):
        d = ImageDraw.Draw(im, "RGBA")
        fb = ImageFont.truetype(FONT_B, 21)
        fr = ImageFont.truetype(FONT_R, 17)
        for x, y, name, area in LABELS[int(f.stem[1])]:
            px, py = to_px(x, y)
            w1 = d.textlength(name, font=fb)
            w2 = d.textlength(area, font=fr)
            w = max(w1, w2) + 18
            d.rounded_rectangle((px - w / 2, py - 26, px + w / 2, py + 24), 8, fill=(255, 255, 255, 215))
            d.text((px, py - 12), name, font=fb, fill=(28, 42, 47), anchor="mm")
            d.text((px, py + 11), area, font=fr, fill=(74, 89, 96), anchor="mm")
        im.thumbnail((900, 1170))
    else:
        im.thumbnail((1200, 800))
    im.save(DST / f.name, quality=80, optimize=True, progressive=True)
    print(f.name, im.size, (DST / f.name).stat().st_size // 1024, "KB")
