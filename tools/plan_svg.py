"""Чертёж квартиры: стены сняты с плана застройщика (1 px = 0,92 см),
мебель расставляется по вариантам. Все координаты в сантиметрах,
начало — внутренний угол прихожей слева (x) и линия окон спальни сверху (y)."""
import math

F = "'Golos Text', Inter, 'Helvetica Neue', Arial, sans-serif"
MONO = "'JetBrains Mono', 'DejaVu Sans Mono', monospace"

WALL = "#2E3F47"
NEW = "#E07A2E"
DEMO = "#D64545"
WIN = "#6FB1DE"
INK = "#25333A"
CLEAR = "#147A82"

CAT = {
    "sleep": ("#BCD5F2", "#4F7DB8"),
    "store": ("#EBD3B1", "#A87A42"),
    "seat": ("#C6E3BA", "#4F8F48"),
    "table": ("#F7DE98", "#B8902A"),
    "kitchen": ("#F5C6AC", "#BA6A45"),
    "appl": ("#F4F6F7", "#6F7980"),
    "plumb": ("#D3ECF7", "#3E8DB5"),
    "play": ("#E4DAF7", "#7A5BBE"),
    "plant": ("#A6D38A", "#5E9446"),
}

FLOOR = {"dry": "#FBF8F2", "wet": "#EEF5F9", "hall": "#F5F2EC"}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Plan:
    def __init__(self):
        self.L = {k: [] for k in ["floor", "rug", "furn", "detail", "walls", "openings", "dims", "labels"]}
        self.storage_cm = 0  # погонные см шкафов глубиной 50–60
        self.items = []  # то же, что нарисовано, для 3D-модели

    def rec(self, kind, **kw):
        kw["kind"] = kind
        self.items.append(kw)

    # ---------- primitives ----------
    def add(self, layer, s):
        self.L[layer].append(s)

    def rect(self, x, y, w, h, fill, stroke="none", sw=1.2, rx=0, layer="furn", dash=None, extra=""):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(layer, f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}{extra}/>')

    def line(self, x1, y1, x2, y2, stroke, sw=1, layer="detail", dash=None, cap="round"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(layer, f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="{cap}"{d}/>')

    def circle(self, cx, cy, r, fill, stroke="none", sw=1.2, layer="furn", dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(layer, f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def poly(self, pts, fill, stroke="none", sw=1.2, layer="furn", dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(layer, f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, lines, fs=15, weight=500, fill=INK, rot=0, layer="labels", halo=True, anchor="middle", font=F):
        if isinstance(lines, str):
            lines = [lines]
        n = len(lines)
        lh = fs * 1.12
        tr = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot else ""
        h = ' paint-order="stroke" stroke="#FFFFFF" stroke-width="4" stroke-linejoin="round"' if halo else ""
        spans = []
        for i, ln in enumerate(lines):
            yy = y + (i - (n - 1) / 2) * lh
            f2 = fs if i == 0 else fs * 0.86
            w2 = weight if i == 0 else 400
            spans.append(f'<tspan x="{x:.1f}" y="{yy:.1f}" font-size="{f2:.1f}" font-weight="{w2}">{esc(ln)}</tspan>')
        self.add(layer, f'<text text-anchor="{anchor}" dominant-baseline="central" font-family="{font}" fill="{fill}"{h}{tr}>{"".join(spans)}</text>')

    # ---------- furniture ----------
    def box(self, x, y, w, h, cat, label=None, fs=14, rot=None, rx=3, layer="furn", k3=None):
        self.rec("box", x=x, y=y, w=w, h=h, cat=cat, label=label, k3=k3)
        f, s = CAT[cat]
        self.rect(x, y, w, h, f, s, 1.3, rx, layer)
        if label:
            if rot is None:
                rot = -90 if h > w * 1.25 and w < 90 else 0
            self.text(x + w / 2, y + h / 2, label, fs=fs, rot=rot, halo=False)

    def wardrobe(self, x, y, w, h, front, label=None, fs=14, count=True):
        self.rec("wardrobe", x=x, y=y, w=w, h=h, front=front)
        f, s = CAT["store"]
        self.rect(x, y, w, h, f, s, 1.3, 2)
        # штанга посередине глубины и линия фасада
        if front in ("top", "bottom"):
            fy = y if front == "top" else y + h
            self.line(x + 2, fy + (4 if front == "top" else -4), x + w - 2, fy + (4 if front == "top" else -4), s, 1.4)
            self.line(x + 6, y + h / 2, x + w - 6, y + h / 2, s, 0.9, dash="7 5")
            length = w
        else:
            fx = x if front == "left" else x + w
            self.line(fx + (4 if front == "left" else -4), y + 2, fx + (4 if front == "left" else -4), y + h - 2, s, 1.4)
            self.line(x + w / 2, y + 6, x + w / 2, y + h - 6, s, 0.9, dash="7 5")
            length = h
        if count:
            self.storage_cm += length
        if label:
            rot = -90 if front in ("left", "right") else 0
            off = 0
            if front in ("left", "right"):
                cx = x + w / 2 + (w * 0.22 if front == "left" else -w * 0.22)
                self.text(cx, y + h / 2, label, fs=fs, rot=rot, halo=True)
            else:
                cy = y + h / 2 + (h * 0.22 if front == "top" else -h * 0.22)
                self.text(x + w / 2, cy, label, fs=fs, halo=True)

    def shelf(self, x, y, w, h, label=None, fs=13, along="x"):
        self.rec("shelf", x=x, y=y, w=w, h=h, along=along)
        f, s = CAT["store"]
        self.rect(x, y, w, h, f, s, 1.2, 2)
        if along == "x":
            n = max(2, int(w // 45))
            for i in range(1, n):
                xx = x + w * i / n
                self.line(xx, y + 3, xx, y + h - 3, s, 0.7)
        else:
            n = max(2, int(h // 45))
            for i in range(1, n):
                yy = y + h * i / n
                self.line(x + 3, yy, x + w - 3, yy, s, 0.7)
        if label:
            rot = -90 if along == "y" else 0
            self.text(x + w / 2, y + h / 2, label, fs=fs, rot=rot)

    def bed(self, x, y, w, h, head, label=None, fs=15, lift=0, drawers=False):
        self.rec("bed", x=x, y=y, w=w, h=h, head=head, lift=lift, drawers=drawers)
        if lift:
            self.rect(x - 6, y - 4, w + 12, h + 8, "none", "#4F7DB8", 1.2, 4, "labels", dash="6 4")
        f, s = CAT["sleep"]
        self.rect(x, y, w, h, f, s, 1.4, 4)
        hb = 9
        if head == "bottom":
            self.rect(x, y + h - hb, w, hb, s, s, 1, 2, "detail")
            n = 2 if w > 120 else 1
            pw = (w - 18 - (n - 1) * 8) / n
            for i in range(n):
                self.rect(x + 9 + i * (pw + 8), y + h - hb - 40, pw, 32, "#FFFFFF", s, 1, 7, "detail")
            self.rect(x + 4, y + 4, w - 8, h - hb - 52, "#A9C7EC", s, 0.8, 3, "detail")
            self.line(x + 4, y + h - hb - 66, x + w - 4, y + h - hb - 66, s, 0.8)
        elif head == "top":
            self.rect(x, y, w, hb, s, s, 1, 2, "detail")
            n = 2 if w > 120 else 1
            pw = (w - 18 - (n - 1) * 8) / n
            for i in range(n):
                self.rect(x + 9 + i * (pw + 8), y + hb + 8, pw, 32, "#FFFFFF", s, 1, 7, "detail")
            self.rect(x + 4, y + hb + 48, w - 8, h - hb - 52, "#A9C7EC", s, 0.8, 3, "detail")
            self.line(x + 4, y + hb + 62, x + w - 4, y + hb + 62, s, 0.8)
        elif head == "left":
            self.rect(x, y, hb, h, s, s, 1, 2, "detail")
            n = 2 if h > 120 else 1
            ph = (h - 18 - (n - 1) * 8) / n
            for i in range(n):
                self.rect(x + hb + 8, y + 9 + i * (ph + 8), 32, ph, "#FFFFFF", s, 1, 7, "detail")
            self.rect(x + hb + 48, y + 4, w - hb - 52, h - 8, "#A9C7EC", s, 0.8, 3, "detail")
            self.line(x + hb + 62, y + 4, x + hb + 62, y + h - 4, s, 0.8)
        elif head == "right":
            self.rect(x + w - hb, y, hb, h, s, s, 1, 2, "detail")
            n = 2 if h > 120 else 1
            ph = (h - 18 - (n - 1) * 8) / n
            for i in range(n):
                self.rect(x + w - hb - 40, y + 9 + i * (ph + 8), 32, ph, "#FFFFFF", s, 1, 7, "detail")
            self.rect(x + 4, y + 4, w - hb - 52, h - 8, "#A9C7EC", s, 0.8, 3, "detail")
            self.line(x + w - hb - 66, y + 4, x + w - hb - 66, y + h - 4, s, 0.8)
        if label:
            if head in ("top", "bottom"):
                cy = y + (h - hb - 52) / 2 + (0 if head == "bottom" else hb + 48)
                rot = -90 if w < 110 else 0
                self.text(x + w / 2, cy, label, fs=fs, rot=rot, halo=False)
            else:
                cx = x + (w - hb - 52) / 2 + (hb + 48 if head == "left" else 0)
                self.text(cx, y + h / 2, label, fs=fs, rot=0 if h >= 110 else 0, halo=False)

    def sofa(self, x, y, w, h, back, label=None, fs=15, arms=True):
        self.rec("sofa", x=x, y=y, w=w, h=h, back=back, arms=arms)
        f, s = CAT["seat"]
        self.rect(x, y, w, h, f, s, 1.4, 7)
        bt, at = 20, 16
        if back == "top":
            self.rect(x, y, w, bt, "#A2CF93", s, 1, 6, "detail")
            if arms:
                self.rect(x, y, at, h, "#A2CF93", s, 1, 6, "detail")
                self.rect(x + w - at, y, at, h, "#A2CF93", s, 1, 6, "detail")
            n = max(2, round((w - 2 * at) / 70))
            for i in range(1, n):
                xx = x + at + (w - 2 * at) * i / n
                self.line(xx, y + bt + 3, xx, y + h - 4, s, 0.8)
            cy = y + bt + (h - bt) / 2
            if label:
                self.text(x + w / 2, cy, label, fs=fs, halo=False)
        elif back == "bottom":
            self.rect(x, y + h - bt, w, bt, "#A2CF93", s, 1, 6, "detail")
            if arms:
                self.rect(x, y, at, h, "#A2CF93", s, 1, 6, "detail")
                self.rect(x + w - at, y, at, h, "#A2CF93", s, 1, 6, "detail")
            if label:
                self.text(x + w / 2, y + (h - bt) / 2, label, fs=fs, halo=False)
        elif back == "left":
            self.rect(x, y, bt, h, "#A2CF93", s, 1, 6, "detail")
            if label:
                self.text(x + bt + (w - bt) / 2, y + h / 2, label, fs=fs, rot=-90, halo=False)
        elif back == "right":
            self.rect(x + w - bt, y, bt, h, "#A2CF93", s, 1, 6, "detail")
            if label:
                self.text(x + (w - bt) / 2, y + h / 2, label, fs=fs, rot=-90, halo=False)

    def bench(self, x, y, w, h, back, label=None, fs=13):
        self.rec("bench", x=x, y=y, w=w, h=h, back=back)
        f, s = CAT["seat"]
        self.rect(x, y, w, h, f, s, 1.3, 6)
        if back == "top":
            self.rect(x, y, w, 12, "#A2CF93", s, 1, 5, "detail")
            if label:
                self.text(x + w / 2, y + 12 + (h - 12) / 2, label, fs=fs, halo=False)
        elif back == "left":
            self.rect(x, y, 12, h, "#A2CF93", s, 1, 5, "detail")
            if label:
                self.text(x + 12 + (w - 12) / 2, y + h / 2, label, fs=fs, rot=-90, halo=False)
        else:
            if label:
                self.text(x + w / 2, y + h / 2, label, fs=fs, halo=False)

    def chair(self, cx, cy, facing, size=42, guest=False):
        """facing — куда смотрит сидящий: up/down/left/right"""
        self.rec("chair", cx=cx, cy=cy, facing=facing, size=size, guest=guest)
        f, s = CAT["seat"]
        x, y = cx - size / 2, cy - size / 2
        if guest:
            self.rect(x, y, size, size, "#FFFFFF", s, 1.1, 8, dash="4 3")
            return
        self.rect(x, y, size, size, f, s, 1.1, 8)
        b = 8
        if facing == "up":
            self.rect(x + 3, y + size - b - 1, size - 6, b, s, "none", 0, 3, "detail")
        elif facing == "down":
            self.rect(x + 3, y + 1, size - 6, b, s, "none", 0, 3, "detail")
        elif facing == "left":
            self.rect(x + size - b - 1, y + 3, b, size - 6, s, "none", 0, 3, "detail")
        elif facing == "right":
            self.rect(x + 1, y + 3, b, size - 6, s, "none", 0, 3, "detail")

    def office_chair(self, cx, cy, r=24):
        self.rec("office_chair", cx=cx, cy=cy, r=r)
        f, s = CAT["seat"]
        self.circle(cx, cy, r, f, s, 1.2)
        self.circle(cx, cy, r * 0.45, "#A2CF93", s, 0.8, "detail")

    def stool(self, cx, cy, r=17):
        self.rec("stool", cx=cx, cy=cy, r=r)
        f, s = CAT["seat"]
        self.circle(cx, cy, r, f, s, 1.2)

    def desk(self, x, y, w, h, label=None, fs=14, k3="desk"):
        self.box(x, y, w, h, "table", label, fs=fs, rx=3, k3=k3)

    def rug(self, x, y, w, h, label=None, fs=14, rx=22):
        self.rec("rug", x=x, y=y, w=w, h=h)
        f, s = CAT["play"]
        self.rect(x, y, w, h, f, s, 1.2, rx, "rug", dash="7 5")
        if label:
            self.text(x + w / 2, y + h / 2, label, fs=fs, fill="#5B4596", halo=False, weight=500)

    def plant(self, cx, cy, r=13):
        self.rec("plant", cx=cx, cy=cy, r=r)
        f, s = CAT["plant"]
        self.circle(cx, cy, r, f, s, 1)
        for k in range(6):
            a = k * math.pi / 3 + 0.3
            self.line(cx, cy, cx + r * 0.85 * math.cos(a), cy + r * 0.85 * math.sin(a), s, 0.9)

    def tv(self, x, y, w, h, label=None, lx=None, ly=None, fs=12):
        self.rec("tv", x=x, y=y, w=w, h=h)
        self.rect(x, y, w, h, "#2F3A40", "none", 0, 1.5, "detail")
        if label:
            self.text(lx if lx is not None else x + w / 2, ly if ly is not None else y - 10, label, fs=fs)

    def nightstand(self, x, y, w=45, h=40):
        self.rec("nightstand", x=x, y=y, w=w, h=h)
        f, s = CAT["store"]
        self.rect(x, y, w, h, f, s, 1.2, 3)
        self.circle(x + w / 2, y + h / 2, 7, "#FFF4C7", "#C49B2A", 0.9, "detail")

    # кухня
    def counter(self, x, y, w, h):
        self.rec("counter", x=x, y=y, w=w, h=h)
        f, s = CAT["kitchen"]
        self.rect(x, y, w, h, f, s, 1.3, 1)

    def sink(self, x, y, w, h, label="Мойка", fs=12, vertical=False):
        self.rec("ksink", x=x, y=y, w=w, h=h)
        s = CAT["kitchen"][1]
        self.rect(x + 8, y + 8, w - 16, h - 16, "#FFFFFF", s, 1.1, 6, "detail")
        self.circle(x + w / 2, y + h / 2, 3, s, "none", 0, "detail")
        if label:
            self.text(x + w / 2, y + h / 2 + (0 if vertical else 0), label, fs=fs, rot=-90 if vertical else 0)

    def cooktop(self, x, y, w, h, label="Варочная", fs=12, lpos=None):
        self.rec("cooktop", x=x, y=y, w=w, h=h)
        self.rect(x + 4, y + 5, w - 8, h - 10, "#3B4045", "none", 0, 3, "detail")
        for dx in (0.3, 0.7):
            for dy in (0.3, 0.7):
                self.circle(x + w * dx, y + h * dy, 8, "none", "#E6E6E6", 1, "detail")
        if label:
            lx, ly = lpos if lpos else (x + w / 2, y - 12)
            self.text(lx, ly, label, fs=fs)

    def appliance(self, x, y, w, h, label, fs=12, rot=None, dash=None, k3=None):
        self.rec("appliance", x=x, y=y, w=w, h=h, k3=k3)
        f, s = CAT["appl"]
        self.rect(x, y, w, h, f, s, 1.3, 2, dash=dash)
        if label:
            if rot is None:
                rot = -90 if h > w * 1.3 else 0
            self.text(x + w / 2, y + h / 2, label, fs=fs, rot=rot, halo=False)

    def hood(self, x, y, w, h):
        self.rect(x, y, w, h, "none", "#6F7980", 1, 2, "detail", dash="4 3")

    def upper(self, x1, y1, x2, y2):
        self.line(x1, y1, x2, y2, "#BA6A45", 1, dash="3 4")

    # сантехника
    def bath(self, x, y, w, h, label="Ванна", fs=13):
        self.rec("bath", x=x, y=y, w=w, h=h)
        f, s = CAT["plumb"]
        self.rect(x, y, w, h, f, s, 1.3, 4)
        self.rect(x + 6, y + 6, w - 12, h - 12, "#FFFFFF", s, 1, min(w, h) / 3, "detail")
        if label:
            rot = -90 if h > w else 0
            self.text(x + w / 2, y + h / 2, label, fs=fs, rot=rot, halo=False)

    def shower(self, x, y, w, h, label="Душ", fs=13):
        f, s = CAT["plumb"]
        self.rect(x, y, w, h, f, s, 1.3, 3)
        self.line(x + 4, y + 4, x + w - 4, y + h - 4, s, 0.7)
        self.line(x + w - 4, y + 4, x + 4, y + h - 4, s, 0.7)
        self.circle(x + w / 2, y + h / 2, 5, "#FFFFFF", s, 1, "detail")
        if label:
            self.text(x + w / 2, y + h / 2 - 20, label, fs=fs)

    def walkin(self, x, y, w, h, glass, drain, label=None, fs=12, head="bottom"):
        """Душ без поддона: glass — отрезок стекла (x1,y1,x2,y2), drain — линия трапа, head — стена с лейкой."""
        self.rec("walkin", x=x, y=y, w=w, h=h, glass=glass, drain=drain, head=head)
        f, s = CAT["plumb"]
        self.rect(x, y, w, h, "#E3F2FA", s, 1.1, 2, dash="5 3")
        gx1, gy1, gx2, gy2 = glass
        self.line(gx1, gy1, gx2, gy2, "#3E8DB5", 3.4, "furn", cap="butt")
        dx1, dy1, dx2, dy2 = drain
        self.line(dx1, dy1, dx2, dy2, "#3E8DB5", 2.2, "detail", dash="3 2", cap="butt")
        self.circle(x + 18, y + h / 2, 8, "#FFFFFF", s, 1.1, "detail")
        if label:
            self.text(x + w / 2 + 6, y + h / 2, label, fs=fs, halo=False)

    def wc(self, x, y, w, h, back):
        self.rec("wc", x=x, y=y, w=w, h=h, back=back)
        f, s = CAT["plumb"]
        if back == "bottom":
            self.rect(x, y + h - 16, w, 16, f, s, 1.2, 2)
            self.add("furn", f'<ellipse cx="{x + w / 2:.1f}" cy="{y + (h - 16) / 2 + 2:.1f}" rx="{w / 2 - 1:.1f}" ry="{(h - 16) / 2 + 2:.1f}" fill="#FFFFFF" stroke="{s}" stroke-width="1.3"/>')
        elif back == "left":
            self.rect(x, y, 16, h, f, s, 1.2, 2)
            self.add("furn", f'<ellipse cx="{x + 16 + (w - 16) / 2 - 2:.1f}" cy="{y + h / 2:.1f}" rx="{(w - 16) / 2 + 2:.1f}" ry="{h / 2 - 1:.1f}" fill="#FFFFFF" stroke="{s}" stroke-width="1.3"/>')
        elif back == "top":
            self.rect(x, y, w, 16, f, s, 1.2, 2)
            self.add("furn", f'<ellipse cx="{x + w / 2:.1f}" cy="{y + 16 + (h - 16) / 2 - 2:.1f}" rx="{w / 2 - 1:.1f}" ry="{(h - 16) / 2 + 2:.1f}" fill="#FFFFFF" stroke="{s}" stroke-width="1.3"/>')
        elif back == "right":
            self.rect(x + w - 16, y, 16, h, f, s, 1.2, 2)
            self.add("furn", f'<ellipse cx="{x + (w - 16) / 2 + 2:.1f}" cy="{y + h / 2:.1f}" rx="{(w - 16) / 2 + 2:.1f}" ry="{h / 2 - 1:.1f}" fill="#FFFFFF" stroke="{s}" stroke-width="1.3"/>')

    def basin(self, x, y, w, h, back, label=None, fs=12):
        self.rec("basin", x=x, y=y, w=w, h=h, back=back)
        f, s = CAT["plumb"]
        self.rect(x, y, w, h, f, s, 1.3, 3)
        self.add("detail", f'<ellipse cx="{x + w / 2:.1f}" cy="{y + h / 2:.1f}" rx="{w / 2 - 7:.1f}" ry="{h / 2 - 7:.1f}" fill="#FFFFFF" stroke="{s}" stroke-width="1"/>')
        if label:
            self.text(x + w / 2, y + h / 2, label, fs=fs, rot=-90 if h > w else 0)

    def washer(self, x, y, w, h, label=None, fs=11):
        self.rec("washer", x=x, y=y, w=w, h=h)
        f, s = CAT["appl"]
        self.rect(x, y, w, h, f, s, 1.3, 3)
        self.circle(x + w / 2, y + h / 2, min(w, h) * 0.3, "#EAF4FA", s, 1.1, "detail")
        if label:
            self.text(x + w / 2, y + h / 2, label, fs=fs)

    # ---------- спорт и прочее ----------
    def bike(self, cx, ywall, length, kid=False):
        """Велосипед на крюке за переднее колесо у стены ywall (снизу): сверху это узкая полоса."""
        self.rec("bike", cx=cx, ywall=ywall, length=length, kid=kid)
        f, s = "#E4DAF7", "#7A5BBE"
        y1 = ywall - length
        self.rect(cx - 5, y1, 10, length, f, s, 1.2, 5, "furn")
        self.line(cx - (20 if kid else 27), ywall - 22, cx + (20 if kid else 27), ywall - 22, s, 2.4, "detail")
        self.circle(cx, y1 + length * 0.55, 6, "#FFFFFF", s, 1, "detail")

    def slide_door(self, x1, y1, x2, y2, ox1, oy1, ox2, oy2):
        """Дверь-купе: полотно закрыто (x1..y2) и открыто (пунктир, ox1..oy2)."""
        self.rec("slide", x1=x1, y1=y1, x2=x2, y2=y2, ox1=ox1, oy1=oy1, ox2=ox2, oy2=oy2)
        self.rect(x1, y1, x2 - x1, y2 - y1, "#FFFFFF", "#56656C", 1.6, 1, "openings")
        self.rect(ox1, oy1, ox2 - ox1, oy2 - oy1, "none", "#56656C", 1.1, 1, "openings", dash="4 3")

    def bridge(self, x, y, w, h, label="полка-мост над кроватью", fs=9):
        """Полка-мост на высоте 190–230 см."""
        self.rec("bridge", x=x, y=y, w=w, h=h)
        self.rect(x, y, w, h, "none", "#A87A42", 1.2, 2, "labels", dash="5 4")
        if label:
            self.text(x + w / 2, y + h / 2, label, fs=fs, fill="#8A6234")

    def swedish(self, x, y, w, h, label="Шведская стенка", fs=10, rot=-90):
        self.rec("swedish", x=x, y=y, w=w, h=h)
        f, s = CAT["play"]
        self.rect(x, y, w, h, f, s, 1.3, 2)
        n = 6
        for i in range(1, n):
            if h > w:
                yy = y + h * i / n
                self.line(x + 2, yy, x + w - 2, yy, s, 0.8)
            else:
                xx = x + w * i / n
                self.line(xx, y + 2, xx, y + h - 2, s, 0.8)
        if label:
            if h > w:
                self.text(x - 13, y + h / 2, label, fs=fs, rot=rot)
            else:
                self.text(x + w / 2, y + h + 12, label, fs=fs)

    def mat(self, x, y, w, h, label="мат", fs=10.5):
        self.rec("mat", x=x, y=y, w=w, h=h)
        self.rect(x, y, w, h, "none", "#7A5BBE", 1.2, 10, "rug", dash="6 4")
        if label:
            self.text(x + w / 2, y + h / 2, label, fs=fs, fill="#5B4596", halo=False)

    # ---------- architecture ----------
    def wall(self, x1, y1, x2, y2, color=WALL):
        self.rec("wall", x1=x1, y1=y1, x2=x2, y2=y2, new=(color == NEW))
        self.rect(x1, y1, x2 - x1, y2 - y1, color, "none", 0, 0, "walls")

    def new_wall(self, x1, y1, x2, y2):
        self.wall(x1, y1, x2, y2, NEW)

    def demo(self, x1, y1, x2, y2):
        self.rect(x1, y1, x2 - x1, y2 - y1, "#FFFFFF", DEMO, 1.6, 0, "rug", dash="5 3")

    def window(self, x1, y1, x2, y2, room=None):
        """room — сторона, где комната: bottom/top для окна в горизонтальной стене, left/right — в вертикальной.
        По умолчанию bottom и left, как в квартире 95."""
        self.rec("window", x1=x1, y1=y1, x2=x2, y2=y2, room=room)
        self.rect(x1, y1, x2 - x1, y2 - y1, "#FFFFFF", WALL, 1, 0, "openings")
        if x2 - x1 > y2 - y1:
            for f in (0.38, 0.62):
                yy = y1 + (y2 - y1) * f
                self.line(x1, yy, x2, yy, WIN, 1.8, "openings", cap="butt")
        else:
            for f in (0.38, 0.62):
                xx = x1 + (x2 - x1) * f
                self.line(xx, y1, xx, y2, WIN, 1.8, "openings", cap="butt")

    def door(self, hinge, closed, opened, color="#56656C"):
        hx, hy = hinge
        cx, cy = closed
        ox, oy = opened
        self.rec("door", hinge=hinge, closed=closed, opened=opened)
        r = math.hypot(cx - hx, cy - hy)
        cross = (cx - hx) * (oy - hy) - (cy - hy) * (ox - hx)
        sweep = 1 if cross > 0 else 0
        self.add("openings", f'<path d="M{cx:.1f},{cy:.1f} A{r:.1f},{r:.1f} 0 0 {sweep} {ox:.1f},{oy:.1f}" fill="none" stroke="{color}" stroke-width="1.1" stroke-dasharray="5 4"/>')
        self.line(hx, hy, ox, oy, color, 3.2, "openings")

    def shaft(self, x1, y1, x2, y2, label=None):
        self.rec("shaft", x1=x1, y1=y1, x2=x2, y2=y2)
        self.rect(x1, y1, x2 - x1, y2 - y1, "#ECEEEF", "#8D979C", 1, 0, "walls")
        self.line(x1, y1, x2, y2, "#A2ABAF", 0.8, "walls")
        self.line(x2, y1, x1, y2, "#A2ABAF", 0.8, "walls")
        if label:
            self.text((x1 + x2) / 2, (y1 + y2) / 2, label, fs=10, fill="#5F6B70")

    def floor(self, pts, kind="dry"):
        self.rec("floor", pts=pts, fk=kind)
        self.poly(pts, FLOOR[kind], layer="floor")

    # ---------- размеры ----------
    def dim(self, x1, y1, x2, y2, label=None, fs=15, color="#3E4F57", layer="dims", tick=True):
        horiz = abs(y2 - y1) < abs(x2 - x1)
        self.line(x1, y1, x2, y2, color, 1, layer)
        if tick:
            for (px, py) in ((x1, y1), (x2, y2)):
                self.line(px - 5, py + 5, px + 5, py - 5, color, 1.6, layer)
                if horiz:
                    self.line(px, py - 8, px, py + 8, color, 0.8, layer)
                else:
                    self.line(px - 8, py, px + 8, py, color, 0.8, layer)
        n = label if label is not None else str(round(math.hypot(x2 - x1, y2 - y1)))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        self.text(mx, my, n, fs=fs, weight=600, fill=color, rot=0 if horiz else -90, layer=layer, font=MONO)

    def clear(self, x1, y1, x2, y2, label=None, fs=13):
        """Размер свободного прохода (бирюзовый, со стрелками)."""
        horiz = abs(y2 - y1) < abs(x2 - x1)
        self.line(x1, y1, x2, y2, CLEAR, 1.2, "dims", dash="4 3")
        ang = math.atan2(y2 - y1, x2 - x1)
        for (px, py, a) in ((x1, y1, ang), (x2, y2, ang + math.pi)):
            p1 = (px + 9 * math.cos(a + 0.45), py + 9 * math.sin(a + 0.45))
            p2 = (px + 9 * math.cos(a - 0.45), py + 9 * math.sin(a - 0.45))
            self.poly([(px, py), p1, p2], CLEAR, layer="dims")
        n = label if label is not None else str(round(math.hypot(x2 - x1, y2 - y1)))
        self.text((x1 + x2) / 2, (y1 + y2) / 2, n, fs=fs, weight=700, fill=CLEAR, rot=0 if horiz else -90, layer="dims", font=MONO)

    def room_label(self, x, y, name, area, fs=19):
        self.text(x, y - fs * 0.55, name, fs=fs, weight=700, fill="#1D2A30", layer="labels")
        self.text(x, y + fs * 0.62, area, fs=fs * 0.82, weight=500, fill="#4A5960", layer="labels", font=MONO)

    def render(self, vb, overlay_href=None, title="", img_box=None):
        """img_box — где лежит план застройщика в сантиметрах: (x, y, ширина, высота)."""
        x, y, w, h = vb
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" role="img" aria-label="{esc(title)}">',
                 f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FFFFFF"/>']
        for k in ["floor", "rug", "furn", "detail", "walls", "openings", "dims", "labels"]:
            parts.append(f'<g class="ly-{k}">' + "".join(self.L[k]) + "</g>")
        if overlay_href:
            ix, iy, iw, ih = img_box or (-166 * 0.92, -70 * 0.92, 1206 * 0.92, 1618 * 0.92)
            parts.append(f'<image class="orig" href="{overlay_href}" x="{ix:.2f}" y="{iy:.2f}" width="{iw:.2f}" height="{ih:.2f}" preserveAspectRatio="none"/>')
        parts.append("</svg>")
        return "".join(parts)
