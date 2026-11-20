"""Условные обозначения инженерных разделов поверх плана.

Координаты — сантиметры плана (как в plan_svg.py). Точка на стене задаётся
координатой на линии стены и направлением в комнату d: u (вверх), d (вниз), l, r.
Каждый символ — строка SVG; Overlay раскладывает их по слоям <g class="lyr lyr-КЛЮЧ">,
которые на сайте включаются и выключаются кнопками над планом.
"""
import math

from plan_svg import esc

MONO = "'JetBrains Mono', 'DejaVu Sans Mono', monospace"
SANS = "'Golos Text', Inter, Arial, sans-serif"

C = {
    "power": "#1F5FBF",     # обычные розетки
    "ups": "#E8590C",       # линия ИБП
    "appl": "#6741D9",      # выводы под технику
    "light": "#C98500",
    "light_fill": "#FFE066",
    "sw": "#1F2A30",
    "lan": "#0B8A6B",
    "lan_fill": "#E6FCF5",
    "cold": "#1C7ED6",
    "hot": "#E03131",
    "sewer": "#8A5A35",
    "leak": "#0C8599",
    "ink": "#1F2A30",
    "muted": "#5C6B70",
    "group": "#495057",
}

N = {"u": (0, -1), "d": (0, 1), "l": (-1, 0), "r": (1, 0)}


def along(d):
    return (1, 0) if d in "ud" else (0, 1)


def txt(x, y, s, fs=7, fill=None, weight=600, anchor="middle", font=MONO, halo=True, rot=0):
    fill = fill or C["ink"]
    h = ' paint-order="stroke" stroke="#FFFFFF" stroke-width="2.2" stroke-linejoin="round"' if halo else ""
    tr = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{fs}" font-family="{font}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" dominant-baseline="central"{h}{tr}>{esc(str(s))}</text>')


def line(x1, y1, x2, y2, stroke, sw=1, dash=None, cap="round"):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="{cap}"{d}/>'


def path(pts, stroke, sw=1.4, dash=None, opacity=1, join="round"):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    o = f' stroke-opacity="{opacity}"' if opacity != 1 else ""
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<polyline points="{p}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="{join}" stroke-linecap="round"{d}{o}/>'


def path_len(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def label_pos(x, y, d, dist):
    nx, ny = N[d]
    return x + nx * dist, y + ny * dist


def badge(x, y, g):
    """Номер группы щита в кружке."""
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.4" fill="{C["group"]}"/>'
            + txt(x, y + 0.2, g, fs=5.4, fill="#FFFFFF", weight=700, halo=False))


# ---------------------------------------------------------------- электрика
def socket(x, y, d, kinds, r=5.2, gap=1.2):
    """Блок розеток: полукруги на стене. kinds: std — обычная, ups — от ИБП."""
    nx, ny = N[d]
    ax, ay = along(d)
    n = len(kinds)
    step = 2 * r + gap
    sweep = 1 if (-ax * ny + ay * nx) > 0 else 0
    out = []
    for i, k in enumerate(kinds):
        off = (i - (n - 1) / 2) * step
        cx, cy = x + ax * off + nx * 0.8, y + ay * off + ny * 0.8
        x1, y1, x2, y2 = cx - ax * r, cy - ay * r, cx + ax * r, cy + ay * r
        fill, stroke = ("#FFFFFF", C["power"]) if k == "std" else (C["ups"], "#A63C06")
        out.append(f'<path d="M{x1:.1f},{y1:.1f} A{r},{r} 0 0 {sweep} {x2:.1f},{y2:.1f} Z" fill="{fill}" stroke="{stroke}" stroke-width="1.3"/>')
        tx, ty = cx + nx * r, cy + ny * r
        out.append(line(tx, ty, tx + nx * 3.2, ty + ny * 3.2, stroke, 1.3))
    return "".join(out), n * step


def appl(x, y, d, code, color=None):
    """Вывод под технику: квадрат с подписью (ПММ, Дух, Вар…)."""
    nx, ny = N[d]
    color = color or C["appl"]
    w = max(12, len(code) * 4.3 + 4)
    h = 9.5
    cx, cy = x + nx * (h / 2 + 0.8), y + ny * (h / 2 + 0.8)
    if d in "lr":
        w, h = h, w
    s = (f'<rect x="{cx - w / 2:.1f}" y="{cy - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="1.5" fill="#F3F0FF" stroke="{color}" stroke-width="1.2"/>'
         + txt(cx, cy, code, fs=5.2, fill=color, weight=700, halo=False, font=SANS, rot=-90 if d in "lr" else 0))
    return s, (w if d in "ud" else h)


def floorbox(x, y, label=None):
    s = (f'<rect x="{x - 8:.1f}" y="{y - 8:.1f}" width="16" height="16" rx="1.5" fill="#FFFFFF" stroke="{C["power"]}" stroke-width="1.3"/>'
         + line(x - 8, y - 8, x + 8, y + 8, C["power"], 0.9) + line(x + 8, y - 8, x - 8, y + 8, C["power"], 0.9))
    return s


def switch(x, y, d, keys):
    """Выключатель: кружок у стены и клавиши-черточки. keys: [(kind, ...)], kind: norm, pass, cross."""
    nx, ny = N[d]
    cx, cy = x + nx * 4.6, y + ny * 4.6
    base = math.atan2(ny, nx)
    out = [f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3.3" fill="#FFFFFF" stroke="{C["sw"]}" stroke-width="1.3"/>']
    kinds = [k[0] for k in keys]
    angles = [base + math.radians(a) for a in ([40] if len(keys) == 1 else [28, 58])]
    for a, kind in zip(angles, kinds):
        ex, ey = cx + math.cos(a) * 10, cy + math.sin(a) * 10
        out.append(line(cx + math.cos(a) * 3.3, cy + math.sin(a) * 3.3, ex, ey, C["sw"], 1.2))
        tx, ty = math.cos(a + math.pi / 2) * 2.6, math.sin(a + math.pi / 2) * 2.6
        out.append(line(ex, ey, ex + tx, ey + ty, C["sw"], 1.2))
        if kind in ("pass", "cross"):
            b = a - math.radians(80)
            fx, fy = cx + math.cos(b) * 9, cy + math.sin(b) * 9
            out.append(line(cx + math.cos(b) * 3.3, cy + math.sin(b) * 3.3, fx, fy, C["sw"], 1.2))
            out.append(line(fx, fy, fx - tx, fy - ty, C["sw"], 1.2))
        if kind == "cross":
            out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="1.2" fill="{C["sw"]}"/>')
    return "".join(out)


def lamp(x, y, kind, d=None):
    """Светильники: ceiling — потолочный, spot — точечный, pendant — подвес, sconce — бра,
    mirror — подсветка зеркала, step — подсветка у пола, fan — вытяжной вентилятор."""
    L, F = C["light"], C["light_fill"]
    if kind == "ceiling":
        r = 7.5
        k = r * 0.7
        return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{F}" stroke="{L}" stroke-width="1.4"/>'
                + line(x - k, y - k, x + k, y + k, L, 1.1) + line(x + k, y - k, x - k, y + k, L, 1.1))
    if kind == "spot":
        return f'<circle cx="{x}" cy="{y}" r="4.2" fill="{F}" stroke="{L}" stroke-width="1.3"/><circle cx="{x}" cy="{y}" r="1.3" fill="{L}"/>'
    if kind == "pendant":
        return (f'<circle cx="{x}" cy="{y}" r="9" fill="{F}" stroke="{L}" stroke-width="1.4"/>'
                f'<circle cx="{x}" cy="{y}" r="3.4" fill="{L}"/>')
    if kind == "motion":
        return (f'<circle cx="{x}" cy="{y}" r="4.6" fill="#FFFFFF" stroke="{L}" stroke-width="1.3"/>'
                + txt(x, y + 0.2, "ДД", fs=3.8, fill=L, weight=700, halo=False, font=SANS))
    nx, ny = N[d]
    ax, ay = along(d)
    if kind in ("sconce", "mirror"):
        r = 5.6 if kind == "sconce" else 4.4
        sweep = 1 if (-ax * ny + ay * nx) > 0 else 0
        x1, y1, x2, y2 = x - ax * r + nx * 0.6, y - ay * r + ny * 0.6, x + ax * r + nx * 0.6, y + ay * r + ny * 0.6
        s = f'<path d="M{x1:.1f},{y1:.1f} A{r},{r} 0 0 {sweep} {x2:.1f},{y2:.1f} Z" fill="{F}" stroke="{L}" stroke-width="1.3"/>'
        if kind == "mirror":
            w = 13
            s = (f'<rect x="{x - ax * w / 2 + nx * 0.6 - (1.6 if d in "ud" else 0):.1f}" y="{y - ay * w / 2 + ny * 0.6:.1f}" '
                 f'width="{(w if d in "ud" else 3.2):.1f}" height="{(3.2 if d in "ud" else w):.1f}" fill="{F}" stroke="{L}" stroke-width="1.2"/>')
        return s
    if kind == "step":
        cx, cy = x + nx * 2.2, y + ny * 2.2
        w, h = (10, 4.4) if d in "ud" else (4.4, 10)
        return f'<rect x="{cx - w / 2:.1f}" y="{cy - h / 2:.1f}" width="{w}" height="{h}" rx="1" fill="{F}" stroke="{L}" stroke-width="1.1"/>'
    if kind == "fan":
        cx, cy = x + nx * 6, y + ny * 6
        out = [f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5.6" fill="#FFFFFF" stroke="{C["muted"]}" stroke-width="1.2"/>']
        for i in range(3):
            a = i * 2 * math.pi / 3
            out.append(line(cx, cy, cx + math.cos(a) * 4.4, cy + math.sin(a) * 4.4, C["muted"], 1.1))
        return "".join(out)
    raise ValueError(kind)


def strip(pts):
    return path(pts, C["light"], 2.4, dash="5 2.5")


def panel(x, y, w, h, label="ЩК"):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="1.5" fill="#343A40" stroke="#1F2A30" stroke-width="1"/>'
            + txt(x + w / 2, y + h / 2, label, fs=6, fill="#FFFFFF", weight=700, halo=False, font=SANS, rot=-90 if h > w else 0))


def zone(x1, y1, x2, y2, color, label=None, fs=7.5, dash="4 3", fill_op=0.10, rot=0):
    s = (f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" rx="2" fill="{color}" fill-opacity="{fill_op}" '
         f'stroke="{color}" stroke-width="1.3" stroke-dasharray="{dash}"/>')
    if label:
        s += txt((x1 + x2) / 2, (y1 + y2) / 2, label, fs=fs, fill=color, weight=700, font=SANS, rot=rot)
    return s


# ---------------------------------------------------------------- слаботочка
def rj45(x, y, d, n=1, size=9.5):
    """Розетки LAN: треугольники остриём в комнату."""
    nx, ny = N[d]
    ax, ay = along(d)
    out = []
    step = size + 1.4
    for i in range(n):
        off = (i - (n - 1) / 2) * step
        bx, by = x + ax * off + nx * 0.8, y + ay * off + ny * 0.8
        p1 = (bx - ax * size / 2, by - ay * size / 2)
        p2 = (bx + ax * size / 2, by + ay * size / 2)
        p3 = (bx + nx * size * 0.85, by + ny * size * 0.85)
        pts = " ".join(f"{px:.1f},{py:.1f}" for px, py in (p1, p2, p3))
        out.append(f'<polygon points="{pts}" fill="{C["lan"]}" stroke="#06604A" stroke-width="0.9"/>')
    return "".join(out), n * step


def ap(x, y, label="AP", reserve=False):
    """Точка доступа Wi-Fi на потолке."""
    st = C["lan"]
    dash = ' stroke-dasharray="3 2"' if reserve else ""
    s = [f'<circle cx="{x}" cy="{y}" r="10" fill="{C["lan_fill"] if not reserve else "#FFFFFF"}" stroke="{st}" stroke-width="1.5"{dash}/>']
    for r in (3.4, 6.2):
        s.append(f'<path d="M{x - r * 0.8:.1f},{y + 1.6 - r * 0.6:.1f} A{r},{r} 0 0 1 {x + r * 0.8:.1f},{y + 1.6 - r * 0.6:.1f}" fill="none" stroke="{st}" stroke-width="1.2"/>')
    s.append(f'<circle cx="{x}" cy="{y + 2}" r="1.3" fill="{st}"/>')
    if label:
        s.append(txt(x, y + 16, label, fs=6.5, fill=st, weight=700, font=SANS))
    return "".join(s)


def device(x, y, d, code, color=None, fill="#FFFFFF"):
    """Прибор на стене (домофон, контроллер): квадрат с буквой."""
    color = color or C["lan"]
    nx, ny = N[d]
    cx, cy = x + nx * 6, y + ny * 6
    return (f'<rect x="{cx - 5.5:.1f}" y="{cy - 5.5:.1f}" width="11" height="11" rx="1.5" fill="{fill}" stroke="{color}" stroke-width="1.3"/>'
            + txt(cx, cy + 0.2, code, fs=6, fill=color, weight=700, halo=False, font=SANS))


def cable(pts, color=None, sw=1.2, dash=None):
    return path(pts, color or C["lan"], sw, dash=dash)


# ---------------------------------------------------------------- вода
def water_out(x, y, d, kinds, gap=8):
    """Выводы воды на стене: c — холодная (синяя), h — горячая (красная)."""
    nx, ny = N[d]
    ax, ay = along(d)
    out = []
    n = len(kinds)
    for i, k in enumerate(kinds):
        off = (i - (n - 1) / 2) * gap
        cx, cy = x + ax * off + nx * 3.6, y + ay * off + ny * 3.6
        col = C["cold"] if k == "c" else C["hot"]
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3.3" fill="{col}" stroke="#FFFFFF" stroke-width="0.9"/>')
    return "".join(out), n * gap


def drain(x, y, d=None, r=4.2):
    """Выпуск канализации."""
    if d:
        nx, ny = N[d]
        x, y = x + nx * 4.5, y + ny * 4.5
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#FFFFFF" stroke="{C["sewer"]}" stroke-width="1.8"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.3" fill="{C["sewer"]}"/>')


def riser(x, y, code, color):
    return (f'<circle cx="{x}" cy="{y}" r="6.4" fill="#FFFFFF" stroke="{color}" stroke-width="1.8"/>'
            + txt(x, y + 0.2, code, fs=4.6, fill=color, weight=700, halo=False, font=SANS))


def valve(x, y, horiz=True, color=None, motor=False):
    """Кран: два треугольника вершинами друг к другу; motor — с электроприводом."""
    color = color or C["ink"]
    s = 4.2
    if horiz:
        pts1 = f"{x - s},{y - s * 0.75} {x - s},{y + s * 0.75} {x},{y}"
        pts2 = f"{x + s},{y - s * 0.75} {x + s},{y + s * 0.75} {x},{y}"
    else:
        pts1 = f"{x - s * 0.75},{y - s} {x + s * 0.75},{y - s} {x},{y}"
        pts2 = f"{x - s * 0.75},{y + s} {x + s * 0.75},{y + s} {x},{y}"
    out = f'<polygon points="{pts1}" fill="#FFFFFF" stroke="{color}" stroke-width="1.1"/><polygon points="{pts2}" fill="#FFFFFF" stroke="{color}" stroke-width="1.1"/>'
    if motor:
        mx, my = (x, y - 7) if horiz else (x - 7, y)
        out += line(x, y, mx, my, color, 1) + f'<rect x="{mx - 3:.1f}" y="{my - 3:.1f}" width="6" height="6" fill="{C["leak"]}" stroke="{color}" stroke-width="0.8"/>'
    return out


def leak_sensor(x, y):
    s = 4.6
    return (f'<polygon points="{x},{y - s} {x + s},{y} {x},{y + s} {x - s},{y}" fill="#C5F6FA" stroke="{C["leak"]}" stroke-width="1.3"/>'
            f'<circle cx="{x}" cy="{y}" r="1.2" fill="{C["leak"]}"/>')


def offset_poly(pts, d):
    """Параллельная ломаная на расстоянии d (для пар труб)."""
    out = []
    n = len(pts)
    for i in range(n):
        if i == 0:
            (x1, y1), (x2, y2) = pts[0], pts[1]
            nx, ny = -(y2 - y1), x2 - x1
            L = math.hypot(nx, ny) or 1
            out.append((pts[0][0] + nx / L * d, pts[0][1] + ny / L * d))
        elif i == n - 1:
            (x1, y1), (x2, y2) = pts[-2], pts[-1]
            nx, ny = -(y2 - y1), x2 - x1
            L = math.hypot(nx, ny) or 1
            out.append((pts[-1][0] + nx / L * d, pts[-1][1] + ny / L * d))
        else:
            (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
            n1 = (-(y1 - y0), x1 - x0)
            n2 = (-(y2 - y1), x2 - x1)
            l1, l2 = math.hypot(*n1) or 1, math.hypot(*n2) or 1
            n1 = (n1[0] / l1, n1[1] / l1)
            n2 = (n2[0] / l2, n2[1] / l2)
            bx, by = n1[0] + n2[0], n1[1] + n2[1]
            bl = math.hypot(bx, by) or 1
            bx, by = bx / bl, by / bl
            cos = bx * n1[0] + by * n1[1]
            k = d / (cos if abs(cos) > 0.2 else 0.2)
            out.append((x1 + bx * k, y1 + by * k))
    return out


# ---------------------------------------------------------------- слои
class Overlay:
    def __init__(self, order):
        self.order = list(order)
        self.g = {k: [] for k in self.order}

    def add(self, key, s):
        if key not in self.g:
            self.order.append(key)
            self.g[key] = []
        self.g[key].append(s)

    def svg(self):
        return "".join(f'<g class="lyr lyr-{k}">{"".join(self.g[k])}</g>' for k in self.order if self.g.get(k))


def icon(inner, vb=(-10, -10, 20, 20), size=26):
    x, y, w, h = vb
    return f'<svg class="sym" viewBox="{x} {y} {w} {h}" width="{size}" height="{size}" aria-hidden="true">{inner}</svg>'
