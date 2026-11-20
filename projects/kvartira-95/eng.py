"""Инженерные разделы: электрика, водопровод и канализация, слаботочка.

Проработан вариант 1. Координаты — сантиметры плана, как в layout.py.
Точка на стене: (x, y) на линии стены и d — направление в комнату (u, d, l, r).
build(n) отдаёт сайту для каждого раздела: слои поверх плана, легенду, таблицы,
страницы комнат и дополнительные страницы (щит, ИБП, коллектор, слаботочный шкаф).
"""
import math

import eng_svg as S
from eng_svg import C

RN = {
    "spalnya": "Спальня", "detskaya-1": "Детская 1", "detskaya-2": "Детская 2",
    "kuhnya-gostinaya": "Кухня-гостиная", "prihozhaya": "Прихожая", "sport": "Спорт-кладовая",
    "koridor": "Коридор", "su-1": "С/у 1", "su-2": "С/у 2",
}
ROOM_ORDER = list(RN)

TECH = (0, 826, 60, 886)   # техническая секция шкафа-купе у входа: щит, ИБП, слаботочный шкаф


def num(v):
    return f'<span class="num">{v}</span>'


def fmt(v, d=1):
    return f"{v:.{d}f}".replace(".", ",")


# ======================================================================== ЭЛЕКТРИКА
# №: (что питает, защита, кабель ВВГнг(А)-LS, кВт)
GROUPS = {
    1: ("Свет: спальня и детские", "автомат C10", "3×1,5", 0.3),
    2: ("Свет: кухня-гостиная", "автомат C10", "3×1,5", 0.3),
    3: ("Свет: прихожая, коридор, кладовая, санузлы, вентиляторы", "дифавтомат C10, 30 мА", "3×1,5", 0.3),
    4: ("Розетки: спальня", "дифавтомат C16, 30 мА", "3×2,5", 2.0),
    5: ("Розетки: детская 1", "дифавтомат C16, 30 мА", "3×2,5", 2.0),
    6: ("Розетки: детская 2", "дифавтомат C16, 30 мА", "3×2,5", 2.0),
    7: ("Розетки: прихожая, коридор, кладовая", "дифавтомат C16, 30 мА", "3×2,5", 1.5),
    8: ("Розетки: гостиная зона — ТВ, диван, стол", "дифавтомат C16, 30 мА", "3×2,5", 1.5),
    9: ("Розетки над столешницей и вытяжка", "дифавтомат C16, 30 мА", "3×2,5", 3.5),
    10: ("Холодильник и СВЧ", "дифавтомат C16, 30 мА", "3×2,5", 1.8),
    11: ("Духовой шкаф", "дифавтомат C16, 30 мА, тип A", "3×2,5", 3.5),
    12: ("Варочная панель", "дифавтомат C32, 30 мА, тип A", "3×6", 7.4),
    13: ("Посудомоечная машина", "дифавтомат C16, 30 мА, тип A", "3×2,5", 2.2),
    14: ("Стирально-сушильная машина", "дифавтомат C16, 30 мА, тип A", "3×2,5", 2.5),
    15: ("Санузлы: розетки у зеркал, полотенцесушители", "дифавтомат C16, 30 мА", "3×2,5", 2.0),
    16: ("Питание ИБП", "дифавтомат C16, 30 мА", "3×2,5", 0.6),
    17: ("Линия ИБП: оранжевые розетки, сеть, сервер, домофон, защита от протечек",
         "переключатель «ИБП — 0 — сеть» и дифавтомат C10, 30 мА", "3×2,5, свой ноль", 0.15),
}
RESERVE = [
    "тёплый пол в санузлах",
    "кондиционер в спальне",
    "кондиционер в гостиной",
    "водонагреватель на время летнего отключения горячей воды",
]

APPL = {
    "ПММ": "Посудомоечная машина", "Дух": "Духовой шкаф", "Вар": "Варочная панель", "Хол": "Холодильник",
    "СВЧ": "Встроенная СВЧ", "Выт": "Вытяжка", "Стир": "Стирально-сушильная машина",
    "ПС": "Полотенцесушитель", "ИБП": "Питание ИБП",
}

EL = []      # розетки и выводы
SW = []      # выключатели
LT = []      # светильники


def sock(room, x, y, d, kinds, h, g, where):
    EL.append(dict(t="sock", room=room, x=x, y=y, d=d, kinds=kinds, h=h, g=g, where=where))


def out(room, x, y, d, code, h, g, where):
    EL.append(dict(t="appl", room=room, x=x, y=y, d=d, code=code, h=h, g=g, where=where))


def fbox(room, x, y, kinds, lan, g, where):
    EL.append(dict(t="floor", room=room, x=x, y=y, d="u", kinds=kinds, lan=lan, h=0, g=g, where=where))


def sw(room, x, y, d, keys, h, g, where):
    SW.append(dict(room=room, x=x, y=y, d=d, keys=keys, h=h, g=g, where=where))


def lt(room, kind, x, y, c, g, where, d=None, pts=None):
    LT.append(dict(room=room, kind=kind, x=x, y=y, c=c, g=g, where=where, d=d, pts=pts))


CONTROL = {
    "sp_main": "основной свет спальни", "sp_bra_l": "бра слева", "sp_bra_r": "бра справа",
    "k1_main": "свет детской 1", "k1_bra": "бра у кровати", "k2_main": "свет детской 2", "k2_bra": "бра у кровати",
    "kg_spot": "споты над кухней", "kg_table": "подвес над столом", "kg_living": "свет гостиной",
    "kg_led": "подсветка столешницы", "h_main": "свет прихожей", "c_main": "свет коридора",
    "c_night": "ночная подсветка, по датчику", "st_main": "свет кладовой, по датчику",
    "s1_main": "свет и зеркало с/у 1", "s1_fan": "вентилятор с/у 1",
    "s2_main": "свет и зеркало с/у 2", "s2_fan": "вентилятор с/у 2",
}

# --- спальня
sock("spalnya", 446, 354, "u", ["std", "ups"], 70, 4, "у тумбочки слева")
sock("spalnya", 716, 354, "u", ["ups", "std"], 70, 4, "у тумбочки справа")
sock("spalnya", 572, 24, "d", ["std", "std"], 110, 4, "за ТВ на пилоне")
sock("spalnya", 770, 0, "d", ["std"], 30, 4, "у кресла, для торшера")
sock("spalnya", 306, 300, "r", ["std"], 30, 4, "у двери, для пылесоса")
fbox("spalnya", 835, 175, ["std", "std"], 2, 4, "лючок в полу под рабочим столом: 2 розетки и 2 LAN")
sw("spalnya", 418, 354, "u", [("pass", "sp_main")], 90, 1, "у двери, со стороны ручки")
sw("spalnya", 486, 354, "u", [("cross", "sp_main"), ("norm", "sp_bra_l")], 75, 1, "у кровати слева")
sw("spalnya", 676, 354, "u", [("pass", "sp_main"), ("norm", "sp_bra_r")], 75, 1, "у кровати справа")
lt("spalnya", "ceiling", 580, 190, "sp_main", 1, "потолочный светильник над кроватью")
lt("spalnya", "sconce", 467, 354, "sp_bra_l", 1, "бра слева, на 140 см", d="u")
lt("spalnya", "sconce", 695, 354, "sp_bra_r", 1, "бра справа, на 140 см", d="u")

# --- детские
sock("detskaya-1", 836, 672, "u", ["std", "std", "ups"], 85, 5, "у торца стола")
sock("detskaya-1", 565, 363, "d", ["std"], 70, 5, "у изголовья: ночник, зарядка")
sw("detskaya-1", 425, 522, "r", [("norm", "k1_main")], 90, 1, "у двери, со стороны ручки")
lt("detskaya-1", "ceiling", 640, 520, "k1_main", 1, "потолочный светильник")
lt("detskaya-1", "sconce", 545, 363, "k1_bra", 1, "бра у изголовья, выключатель на самом бра", d="d")
sock("detskaya-2", 836, 1008, "u", ["std", "std", "ups"], 85, 6, "у торца стола")
sock("detskaya-2", 592, 706, "d", ["std"], 70, 6, "у изголовья: ночник, зарядка")
sw("detskaya-2", 445, 706, "d", [("norm", "k2_main")], 90, 1, "у двери, со стороны ручки")
lt("detskaya-2", "ceiling", 630, 870, "k2_main", 1, "потолочный светильник")
lt("detskaya-2", "sconce", 572, 706, "k2_bra", 1, "бра у изголовья, выключатель на самом бра", d="d")

# --- кухня-гостиная
K = "kuhnya-gostinaya"
sw(K, 306, 1018, "d", [("norm", "kg_spot"), ("norm", "kg_table")], 90, 2, "у входа из прихожей")
sw(K, 328, 1018, "d", [("norm", "kg_living"), ("norm", "kg_led")], 90, 2, "у входа из прихожей")
for x, y in ((395, 1262), (515, 1262), (635, 1262), (382, 1150)):
    lt(K, "spot", x, y, "kg_spot", 2, "точечный светильник")
lt(K, "pendant", 510, 1103, "kg_table", 2, "подвес над столом")
lt(K, "ceiling", 755, 1190, "kg_living", 2, "светильник над диванной зоной")
lt(K, "strip", 0, 0, "kg_led", 2, "лента под верхними шкафами", pts=[(324, 1252), (324, 1332), (670, 1332)])
sock(K, 294, 1290, "r", ["std", "std"], 110, 9, "над столешницей в углу: чайник, кофемашина")
sock(K, 510, 1360, "u", ["std", "std"], 110, 9, "над столешницей между ПММ и варочной")
sock(K, 652, 1360, "u", ["std", "std"], 110, 9, "над столешницей справа от варочной")
out(K, 602, 1360, "u", "Выт", 210, 9, "над верхними шкафами")
out(K, 566, 1360, "u", "Вар", 15, 12, "вывод кабеля под варочной, за цоколем")
out(K, 533, 1360, "u", "ПММ", 30, 13, "в соседнем модуле справа от машины")
out(K, 294, 1150, "r", "Хол", 30, 10, "за холодильником")
out(K, 294, 1202, "r", "Дух", 30, 11, "в колонне под духовкой")
out(K, 294, 1230, "r", "СВЧ", 200, 10, "в колонне над СВЧ")
sock(K, 530, 1018, "d", ["std"], 90, 8, "над скамьёй: ноутбук, зарядка")
sock(K, 640, 1018, "d", ["std", "ups"], 30, 8, "у дивана слева")
sock(K, 860, 1045, "l", ["std"], 30, 8, "за подлокотником дивана, для торшера")
sock(K, 790, 1360, "u", ["std", "std"], 110, 8, "за ТВ на стене")
sock(K, 832, 1360, "u", ["std", "std"], 30, 8, "за ТВ-тумбой: приставка, консоль")

# --- прихожая, кладовая, коридор
sw("prihozhaya", 14, 707, "d", [("norm", "h_main"), ("pass", "c_main")], 90, 3, "у входной двери")
for y in (775, 885, 995, 1080):
    lt("prihozhaya", "spot", 125, y, "h_main", 3, "точечный светильник")
sock("prihozhaya", 200, 706, "d", ["std"], 30, 7, "у обувницы: сушилка для обуви")
sock("prihozhaya", 250, 1118, "u", ["std"], 15, 7, "база робота-пылесоса")
lt("sport", "ceiling", 330, 925, "st_main", 3, "светильник")
lt("sport", "motion", 368, 880, "st_main", 3, "датчик движения: свет включается сам")
sock("sport", 416, 925, "l", ["std"], 110, 7, "зарядка самоката, фар, аккумуляторов")
sw("koridor", 416, 640, "l", [("pass", "c_main")], 90, 3, "у дверей детских")
for x, y in ((361, 415), (361, 545), (361, 660), (350, 756)):
    lt("koridor", "spot", x, y, "c_main", 3, "точечный светильник")
lt("koridor", "motion", 330, 605, "c_night", 3, "датчик движения ночной подсветки")
lt("koridor", "step", 306, 405, "c_night", 3, "подсветка на 30 см", d="r")
lt("koridor", "step", 416, 470, "c_night", 3, "подсветка на 30 см", d="l")
lt("koridor", "step", 416, 690, "c_night", 3, "подсветка на 30 см", d="l")
sock("koridor", 306, 445, "r", ["std"], 30, 7, "для пылесоса")

# --- санузлы
sw("su-1", 192, 534, "r", [("norm", "s1_main"), ("norm", "s1_fan")], 90, 3, "снаружи, в коридоре у двери")
lt("su-1", "spot", 90, 506, "s1_main", 3, "точечный над ванной, IP65")
lt("su-1", "spot", 95, 612, "s1_main", 3, "точечный, IP44")
lt("su-1", "mirror", 0, 592, "s1_main", 3, "подсветка зеркала на 200 см", d="r")
lt("su-1", "fan", 40, 662, "s1_fan", 3, "вентилятор в вентканал, с таймером", d="r")
sock("su-1", 0, 634, "r", ["std"], 110, 15, "у зеркала: фен, бритва; с крышкой IP44")
out("su-1", 183, 505, "l", "ПС", 110, 15, "электрический полотенцесушитель над краем ванны")
sw("su-2", 110, 1118, "u", [("norm", "s2_main"), ("norm", "s2_fan")], 90, 3, "снаружи, в прихожей у двери")
lt("su-2", "spot", 172, 1172, "s2_main", 3, "точечный, IP44")
lt("su-2", "spot", 212, 1266, "s2_main", 3, "точечный над душем, IP65")
lt("su-2", "mirror", 284, 1163, "s2_main", 3, "подсветка зеркала на 200 см", d="l")
lt("su-2", "fan", 67, 1292, "s2_fan", 3, "вентилятор в вентканал, с таймером", d="r")
sock("su-2", 284, 1140, "l", ["std"], 115, 15, "у зеркала: фен; с крышкой IP44")
out("su-2", 67, 1198, "r", "Стир", 110, 14, "сбоку от машины, с крышкой IP44")
out("su-2", 67, 1232, "r", "ПС", 110, 15, "электрический полотенцесушитель")

# внутри технической секции (на плане — одним прямоугольником)
TECH_EL = [
    ("prihozhaya", "Щит квартиры на 54 модуля", "техническая секция шкафа-купе у входа", "140–200", "—"),
    ("prihozhaya", "Розетка питания ИБП", "техническая секция, внизу", "30", 16),
    ("prihozhaya", "Блок розеток линии ИБП: оптический терминал, роутер, коммутатор, сервер", "техническая секция, в стойке", "90", 17),
    ("prihozhaya", "Питание контроллера защиты от протечек и монитора домофона", "техническая секция", "120", 17),
]


def kinds_text(kinds):
    s, u = kinds.count("std"), kinds.count("ups")
    parts = []
    if s:
        parts.append("розетка" if s == 1 else f"{s} розетки")
    if u:
        parts.append(("розетка" if u == 1 else f"{u} розетки") + " ИБП")
    t = " + ".join(parts)
    return t[0].upper() + t[1:]


def keys_text(keys):
    n = len(keys)
    k = "одноклавишный" if n == 1 else "двухклавишный"
    kinds = {"pass": "проходной", "cross": "перекрёстный"}
    extra = [kinds[x[0]] for x in keys if x[0] in kinds]
    ctl = ", ".join(CONTROL[x[1]] for x in keys)
    return f"Выключатель {k}{', ' + extra[0] if extra else ''}: {ctl}"


LAMP = {"ceiling": "Потолочный светильник", "spot": "Точечный светильник", "pendant": "Подвесной светильник",
        "sconce": "Бра", "mirror": "Подсветка зеркала", "step": "Ночная подсветка", "fan": "Вытяжной вентилятор",
        "motion": "Датчик движения", "strip": "Светодиодная лента"}


def el_overlay():
    o = S.Overlay(["links", "light", "power", "groups"])
    x1, y1, x2, y2 = TECH
    o.add("power", S.zone(x1, y1, x2, y2, "#343A40", None, fill_op=0.06))
    o.add("power", S.panel(3, 832, 11, 48))
    o.add("power", S.txt(36, 846, "щит", fs=7, weight=700, font=S.SANS) + S.txt(36, 858, "ИБП", fs=7, weight=700, font=S.SANS, fill=C["ups"]))
    o.add("groups", S.badge(36, 872, "16") + S.badge(47, 872, "17"))
    for p in EL:
        x, y, d = p["x"], p["y"], p["d"]
        if p["t"] == "sock":
            s, w = S.socket(x, y, d, p["kinds"])
            o.add("power", s)
            lx, ly = S.label_pos(x, y, d, 14.5)
            o.add("power", S.txt(lx, ly, p["h"], fs=6.6))
            ax, ay = S.along(d)
            o.add("groups", S.badge(lx + ax * 10, ly + ay * 10, p["g"]))
        elif p["t"] == "appl":
            s, w = S.appl(x, y, d, p["code"])
            o.add("power", s)
            lx, ly = S.label_pos(x, y, d, 16 if d in "ud" else 14)
            o.add("power", S.txt(lx, ly, p["h"], fs=6.6))
            ax, ay = S.along(d)
            o.add("groups", S.badge(lx + ax * 10, ly + ay * 10, p["g"]))
        elif p["t"] == "floor":
            o.add("power", S.floorbox(x, y))
            o.add("power", S.txt(x, y + 15, "лючок", fs=6.4, font=S.SANS))
            o.add("groups", S.badge(x + 13, y - 7, p["g"]))
    for s in SW:
        o.add("light", S.switch(s["x"], s["y"], s["d"], s["keys"]))
        if s["h"] != 90:
            lx, ly = S.label_pos(s["x"], s["y"], s["d"], 18)
            o.add("light", S.txt(lx, ly, s["h"], fs=6.2))
        nx, ny = S.N[s["d"]]
        o.add("groups", S.badge(s["x"] + nx * 5 - 9 * (1 if s["d"] in "ud" else 0), s["y"] + ny * 5 - 9 * (1 if s["d"] in "lr" else 0), s["g"]))
    for l in LT:
        if l["kind"] == "strip":
            o.add("light", S.strip(l["pts"]))
        else:
            o.add("light", S.lamp(l["x"], l["y"], l["kind"], l["d"]))
    # связи «выключатель — светильники»
    by_c = {}
    for l in LT:
        pt = l["pts"][0] if l["kind"] == "strip" else (l["x"], l["y"])
        by_c.setdefault(l["c"], []).append(pt)
    for s in SW:
        nx, ny = S.N[s["d"]]
        sx, sy = s["x"] + nx * 5, s["y"] + ny * 5
        for _, c in s["keys"]:
            pts = by_c.get(c, [])
            if not pts:
                continue
            chain, cur, left = [(sx, sy)], (sx, sy), list(pts)
            while left:
                nxt = min(left, key=lambda p: math.hypot(p[0] - cur[0], p[1] - cur[1]))
                left.remove(nxt)
                chain.append(nxt)
                cur = nxt
            o.add("links", S.path(chain, C["light"], 0.8, dash="2 2.2", opacity=0.9))
    return o.svg()


def el_room_rows(room):
    rows = []
    for p in EL:
        if p["room"] != room:
            continue
        if p["t"] == "sock":
            what = kinds_text(p["kinds"])
        elif p["t"] == "appl":
            what = APPL[p["code"]]
        else:
            what = "Лючок в полу: 2 розетки и 2 LAN"
        rows.append([what, p["where"], num(p["h"] or "в полу"), num(p["g"])])
    for r, what, where, h, g in TECH_EL:
        if r == room:
            rows.append([what, where, num(h), num(g)])
    return rows


def el_light_rows(room):
    rows = []
    for s in SW:
        if s["room"] == room:
            rows.append([keys_text(s["keys"]), s["where"], num(s["h"]), num(s["g"])])
    for l in LT:
        if l["room"] == room:
            rows.append([LAMP[l["kind"]], l["where"], "—", num(l["g"])])
    return rows


def el_counts():
    rows = []
    tot = [0, 0, 0, 0, 0]
    for r in ROOM_ORDER:
        socks = sum(len(p["kinds"]) for p in EL if p["room"] == r and p["t"] in ("sock", "floor"))
        ups = sum(p["kinds"].count("ups") for p in EL if p["room"] == r and p["t"] == "sock")
        outs = sum(1 for p in EL if p["room"] == r and p["t"] == "appl")
        lamps = sum(1 for l in LT if l["room"] == r and l["kind"] not in ("motion", "fan"))
        sws = sum(1 for s in SW if s["room"] == r)
        vals = [socks, ups, outs, lamps, sws]
        tot = [a + b for a, b in zip(tot, vals)]
        rows.append([RN[r]] + [num(v or "—") for v in vals])
    rows.append(["<b>Всего</b>"] + [f"<b>{num(v)}</b>" for v in tot])
    return rows, tot


def el_legend():
    def ic(inner, vb=(-10, -10, 20, 20)):
        return S.icon(inner, vb)
    return [
        (ic(S.socket(0, -4, "d", ["std"])[0]), "Розетка, рядом высота в см"),
        (ic(S.socket(0, -4, "d", ["ups"])[0]), "Розетка от ИБП (оранжевая)"),
        (ic(S.appl(0, -5, "d", "ПММ")[0], (-12, -10, 24, 20)), "Вывод под технику"),
        (ic(S.floorbox(0, 0)), "Лючок в полу"),
        (ic(S.switch(0, -5, "d", [("norm", "")])), "Выключатель"),
        (ic(S.switch(0, -5, "d", [("norm", ""), ("norm", "")])), "Двухклавишный"),
        (ic(S.switch(0, -5, "d", [("pass", "")])), "Проходной"),
        (ic(S.lamp(0, 0, "ceiling")), "Потолочный светильник"),
        (ic(S.lamp(0, 0, "spot")), "Точечный"),
        (ic(S.lamp(0, 0, "pendant"), (-11, -11, 22, 22)), "Подвес"),
        (ic(S.lamp(0, -4, "sconce", "d")), "Бра"),
        (ic(S.lamp(-8, 0, "step", "r")), "Подсветка у пола"),
        (ic(S.lamp(0, 0, "motion")), "Датчик движения"),
        (ic(S.strip([(-9, 0), (9, 0)])), "Светодиодная лента"),
        (ic(S.lamp(0, -6, "fan", "d")), "Вентилятор"),
        (ic(S.path([(-9, 4), (9, -4)], C["light"], 0.9, dash="2 2.2")), "Что каким выключателем"),
        (ic(S.badge(0, 0, "4")), "Номер группы в щите"),
    ]


PANEL_SHORT = {
    3: "Свет: холл, коридор, с/у", 4: "Розетки спальня", 5: "Розетки детская 1", 6: "Розетки детская 2",
    7: "Розетки холл, кладовая", 8: "Розетки гостиная", 9: "Розетки столешница", 10: "Холод. и СВЧ",
    11: "Духовка", 12: "Варочная", 13: "ПММ", 14: "Стир.-суш.", 15: "Санузлы", 16: "Питание ИБП",
}
RESERVE_SHORT = ["тёплый пол", "конд. спальня", "конд. гостиная", "водонагр."]


def panel_svg():
    """Раскладка модулей в щите: 3 ряда по 18 модулей, 1 модуль = 18 мм."""
    M = 18
    rows = [
        [("QS", "63 А", "Вводной выкл.", 2, "in"), ("KV", "63 А", "Реле напряжения", 2, "in"),
         ("FV", "тип 2", "УЗИП", 2, "in"), ("QD", "100 мА", "Пожарное УЗО", 2, "in"),
         ("SA", "1-0-2", "ИБП — 0 — сеть", 3, "ups"), ("1", "C10", "свет комнат", 1, "mcb"),
         ("2", "C10", "свет кухни", 1, "mcb"), ("17", "C10 30 мА", "Линия ИБП", 2, "ups"),
         (None, "", "свободно", 3, "free")],
        [(str(g), "C10 30 мА" if g == 3 else "C16 30 мА", PANEL_SHORT[g], 2, "rcd") for g in range(3, 12)],
        [(str(g), "C32 30 мА" if g == 12 else "C16 30 мА", PANEL_SHORT[g], 2, "rcd") for g in range(12, 17)]
        + [(None, "", "Резерв: " + r, 2, "free") for r in RESERVE_SHORT],
    ]
    fills = {"in": ("#E9ECEF", "#495057"), "mcb": ("#FFFFFF", "#495057"), "rcd": ("#E7F0FF", "#1F5FBF"),
             "ups": ("#FFE8CC", "#E8590C"), "free": ("#FFFFFF", "#ADB5BD")}
    W = 18 * M
    rh = 118
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-14 -34 {W + 28} {3 * rh + 64}" role="img" aria-label="Раскладка модулей в щите">',
           f'<rect x="-14" y="-34" width="{W + 28}" height="{3 * rh + 64}" fill="#FFFFFF"/>',
           f'<rect x="-8" y="-8" width="{W + 16}" height="{3 * rh + 10}" rx="6" fill="#F8F9FA" stroke="#343A40" stroke-width="1.6"/>',
           S.txt(W / 2, -21, "Щит квартиры: 3 ряда по 18 модулей, примерно 50×65 см", fs=8.5, font=S.SANS, weight=700, halo=False)]
    for ri, row in enumerate(rows):
        y0 = ri * rh + 6
        out.append(f'<rect x="0" y="{y0 + 38}" width="{W}" height="10" fill="#CED4DA"/>')
        x = 0
        for code, rating, label, mods, kind in row:
            f, st = fills[kind]
            w = mods * M
            dash = ' stroke-dasharray="4 3"' if kind == "free" else ""
            out.append(f'<rect x="{x + 1}" y="{y0}" width="{w - 2}" height="86" rx="3" fill="{f}" stroke="{st}" stroke-width="1.2"{dash}/>')
            if code:
                c = f"Гр.{code}" if code.isdigit() else code
                out.append(S.txt(x + w / 2, y0 + 10, c, fs=7.6 if mods > 1 else 6.4, fill=st, weight=700, font=S.SANS, halo=False))
                out.append(S.txt(x + w / 2, y0 + 21, rating, fs=5.6 if mods > 1 else 5, fill="#343A40", weight=600, halo=False))
            words = label.split()
            lines, cur = [], ""
            lim = 9 if mods >= 2 else 5
            for wd in words:
                if len(cur) + len(wd) + 1 > lim and cur:
                    lines.append(cur)
                    cur = wd
                else:
                    cur = (cur + " " + wd).strip()
            if cur:
                lines.append(cur)
            for li, ln in enumerate(lines[:5]):
                out.append(S.txt(x + w / 2, y0 + 50 + li * 7.4, ln, fs=5.6 if mods > 1 else 4.8, fill="#343A40", weight=500, font=S.SANS, halo=False))
            x += w
    out.append(S.txt(W / 2, 3 * rh + 14, "Шины N и PE — отдельно, на изоляторах. Каждый автомат подписан номером группы.", fs=7, font=S.SANS, weight=500, halo=False, fill="#495057"))
    out.append("</svg>")
    return "".join(out)


def ups_svg():
    """Схема линии ИБП сверху вниз."""
    W = 380
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 560" role="img" aria-label="Схема линии ИБП">',
           f'<rect width="{W}" height="560" fill="#FFFFFF"/>']

    def box(x, y, w, h, title, sub="", col="#495057", fill="#F8F9FA"):
        s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="{col}" stroke-width="1.6"/>'
        s += S.txt(x + w / 2, y + (h / 2 if not sub else h / 2 - 7), title, fs=10, font=S.SANS, weight=700, fill=col, halo=False)
        if sub:
            s += S.txt(x + w / 2, y + h / 2 + 8, sub, fs=8, font=S.SANS, weight=500, fill="#343A40", halo=False)
        return s

    def arrow(x1, y1, x2, y2, col="#343A40", dash=None, label=None, lx=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        s = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2 - 6}" stroke="{col}" stroke-width="2"{d}/>'
        s += f'<polygon points="{x2 - 5},{y2 - 8} {x2 + 5},{y2 - 8} {x2},{y2}" fill="{col}"/>'
        if label:
            s += S.txt(lx if lx is not None else x1 + 8, (y1 + y2) / 2, label, fs=7.6, font=S.SANS, weight=500, anchor="start", fill="#495057")
        return s

    U = C["ups"]
    out.append(box(110, 10, 160, 36, "Сеть 230 В", "от этажного щита"))
    out.append(arrow(190, 46, 190, 72))
    out.append(box(90, 72, 200, 40, "Щит: группа 16", "дифавтомат C16, 30 мА"))
    out.append(arrow(190, 112, 190, 138, label="кабель 3×2,5", lx=198))
    out.append(box(90, 138, 200, 52, "ИБП 1 кВА", "чистая синусоида, ≈ 700–800 Вт", U, "#FFF4E6"))
    out.append(f'<line x1="290" y1="164" x2="318" y2="164" stroke="{U}" stroke-width="2"/>')
    out.append(f'<rect x="300" y="120" width="72" height="88" rx="7" fill="#FFF4E6" stroke="{U}" stroke-width="1.6"/>')
    out.append(S.txt(336, 138, "АКБ", fs=10, font=S.SANS, weight=700, fill=U, halo=False))
    out.append(S.txt(336, 160, "LiFePO4", fs=8, font=S.SANS, weight=600, halo=False))
    out.append(S.txt(336, 172, "24 В 50 А·ч", fs=7.4, font=S.SANS, weight=500, halo=False))
    out.append(S.txt(336, 184, "≈ 1,2 кВт·ч", fs=7.4, font=S.SANS, weight=500, halo=False))
    out.append(arrow(190, 190, 190, 230, U, label="выход ИБП обратно в щит", lx=198))
    out.append(box(70, 230, 240, 48, "Щит: переключатель SA", "ИБП — 0 — сеть", U, "#FFF4E6"))
    out.append(f'<path d="M110,28 H30 V254 H64" stroke="#343A40" stroke-width="2" stroke-dasharray="6 4" fill="none"/>')
    out.append(f'<polygon points="62,249 70,254 62,259" fill="#343A40"/>')
    out.append(S.txt(24, 175, "сеть в обход ИБП", fs=7.6, font=S.SANS, weight=500, fill="#495057", rot=-90))
    out.append(arrow(190, 278, 190, 304, U))
    out.append(box(90, 304, 200, 40, "Щит: группа 17", "дифавтомат C10, 30 мА", U, "#FFF4E6"))
    out.append(arrow(190, 344, 190, 372, U, label="своя линия, ноль не смешивать", lx=198))
    items = [
        ("Слаботочный шкаф", "терминал провайдера, роутер, коммутатор с PoE"),
        ("", "→ две точки доступа Wi-Fi на потолке"),
        ("", "домашний сервер (USB-кабель от ИБП — выключится сам)"),
        ("", "контроллер защиты от протечек, монитор домофона"),
        ("Оранжевые розетки", "спальня у кровати ×2, детские у стола ×2,"),
        ("", "гостиная у дивана ×1 — зарядка телефонов"),
    ]
    out.append(f'<rect x="12" y="372" width="356" height="132" rx="8" fill="#FFF4E6" stroke="{U}" stroke-width="1.6"/>')
    yy = 392
    for t, d in items:
        if t:
            out.append(S.txt(24, yy, t, fs=9, font=S.SANS, weight=700, anchor="start", fill=U, halo=False))
            yy += 13
        out.append(S.txt(30, yy, d, fs=8.2, font=S.SANS, weight=500, anchor="start", fill="#343A40", halo=False))
        yy += 13
    out.append(S.txt(190, 528, "Нагрузка ≈ 90 Вт → батареи хватает примерно на 8 часов", fs=9, font=S.SANS, weight=700, halo=False))
    out.append(S.txt(190, 545, "Чайник, фен и обогреватель в оранжевые розетки не включаем", fs=8, font=S.SANS, weight=500, fill="#495057", halo=False))
    out.append("</svg>")
    return "".join(out)


UPS_LOADS = [
    ("Оптический терминал провайдера", "6"),
    ("Роутер", "10"),
    ("Коммутатор с PoE и две точки доступа Wi-Fi", "25"),
    ("Домашний сервер: мини-ПК или NAS на 2 диска, в простое", "20"),
    ("Контроллер защиты от протечек и монитор домофона", "7"),
    ("Зарядка 2–4 телефонов", "20"),
    ("<b>Итого обычно</b>", "<b>≈ 90</b>"),
]
UPS_OPTIONS = [
    ("Минимум", "обычный ИБП 1 кВА со встроенной батареей 2×12 В 9 А·ч", "≈ 0,15", "≈ 1 час"),
    ("Средний", "ИБП с внешней батареей AGM 12 В 100 А·ч, разряжать до половины", "≈ 0,6", "≈ 4–5 часов"),
    ("<b>Рекомендую</b>", "ИБП с внешней батареей LiFePO4 24 В 50 А·ч, ≈ 26×17×21 см, 12 кг", "≈ 1,1", "<b>≈ 8 часов</b>"),
]


# ======================================================================== ВОДОПРОВОД И КАНАЛИЗАЦИЯ
# Трубы от коллектора: (вид c/h, куда, комната, путь). Порядок — сверху вниз по выходу из узла.
PIPES = [
    ("c", "Стирально-сушильная машина", "su-2", [(67, 1142), (85, 1142), (85, 1132)]),
    ("c", "С/у 1: унитаз", "su-1", [(67, 1156), (140, 1156), (140, 688), (62, 688), (62, 693)]),
    ("h", "С/у 1: раковина", "su-1", [(67, 1162), (146, 1162), (146, 636), (8, 636), (8, 600), (4, 600)]),
    ("c", "С/у 1: раковина", "su-1", [(67, 1168), (152, 1168), (152, 630), (14, 630), (14, 584), (4, 584)]),
    ("h", "С/у 1: ванна", "su-1", [(67, 1174), (158, 1174), (158, 566), (8, 566), (8, 514), (4, 514)]),
    ("c", "С/у 1: ванна", "su-1", [(67, 1180), (164, 1180), (164, 560), (14, 560), (14, 498), (4, 498)]),
    ("h", "С/у 2: раковина", "su-2", [(67, 1196), (262, 1196), (262, 1155), (280, 1155)]),
    ("c", "С/у 2: раковина", "su-2", [(67, 1202), (270, 1202), (270, 1171), (280, 1171)]),
    ("h", "Кухня: мойка", K, [(67, 1210), (333, 1210), (333, 1339), (402, 1339), (402, 1356)]),
    ("c", "Кухня: мойка и посудомойка", K, [(67, 1216), (327, 1216), (327, 1345), (386, 1345), (386, 1356)]),
    ("h", "С/у 2: душ", "su-2", [(67, 1226), (186, 1226), (186, 1307)]),
    ("c", "С/у 2: душ", "su-2", [(67, 1232), (174, 1232), (174, 1307)]),
    ("c", "С/у 2: унитаз", "su-2", [(67, 1240), (95, 1240), (95, 1307)]),
]

# Выводы: (комната, прибор, x, y, d, виды, высота воды, канализация, высота канализации, стояк, точка выпуска)
FIXTURES = [
    (K, "Мойка, посудомойка через кран-тройник под мойкой", 394, 1360, "u", ["c", "h"], "55", "Ø50", "45", "К3", (394, 1360, "u")),
    ("su-2", "Стирально-сушильная машина", 85, 1128, "d", ["c"], "70, за машиной", "Ø40, сифон в стене", "60", "К2", (108, 1128, "d")),
    ("su-2", "Раковина", 284, 1163, "l", ["h", "c"], "55", "Ø50", "50", "К3", (284, 1163, "l")),
    ("su-2", "Унитаз подвесной с инсталляцией", 95, 1311, "u", ["c"], "100, внутри рамы", "Ø110", "23, по раме", "К2", None),
    ("su-2", "Душ без поддона: скрытый смеситель-термостат", 180, 1311, "u", ["c", "h"], "105, лейка сверху 210", "линейный трап у стены, Ø50", "в полу", "К3", None),
    ("su-1", "Ванна 180×80", 0, 506, "r", ["c", "h"], "80, на 20 выше борта", "Ø50", "у пола, ванна на ножках", "К1", None),
    ("su-1", "Раковина", 0, 592, "r", ["c", "h"], "55", "Ø50", "50", "К1", (0, 592, "r")),
    ("su-1", "Унитаз подвесной с инсталляцией", 62, 697, "u", ["c"], "100, внутри рамы", "Ø110", "23, по раме", "К1", None),
]

RISERS_W = [("В1", 14, 1146, C["cold"], "холодная вода"), ("Т3", 14, 1166, C["hot"], "горячая вода"), ("Т4", 14, 1186, "#C2255C", "циркуляция горячей")]
RISERS_K = [("К1", 16, 672), ("К2", 29, 1295), ("К3", 249, 1339)]

# канализация: (откуда, Ø, уклон %, путь)
SEWER = [
    ("С/у 1: ванна", 50, 3, [(30, 530), (22, 530), (22, 672), (16, 672)]),
    ("С/у 1: раковина", 50, 3, [(4.5, 592), (22, 592)]),
    ("С/у 1: унитаз", 110, 2, [(78, 678), (16, 678), (16, 672)]),
    ("С/у 2: унитаз", 110, 2, [(110, 1296), (29, 1296), (29, 1295)]),
    ("С/у 2: стиральная машина", 40, 3, [(108, 1132), (73, 1132), (73, 1290), (29, 1290)]),
    ("С/у 2: душ", 50, 2, [(274, 1300), (274, 1330), (249, 1330), (249, 1339)]),
    ("С/у 2: раковина", 50, 3, [(279.5, 1163), (279.5, 1330), (274, 1330)]),
    ("Кухня: мойка", 50, 3, [(394, 1355.5), (394, 1351), (249, 1351), (249, 1339)]),
]
DRAIN_PTS = [(30, 530), (78, 678), (110, 1296), (274, 1300)]

LEAK = [  # датчики протечки: (комната, x, y, где)
    ("su-1", 45, 535, "под ванной у слива"),
    ("su-1", 104, 668, "у инсталляции унитаза"),
    ("su-2", 97, 1196, "перед стиральной машиной"),
    ("su-2", 258, 1166, "под раковиной"),
    (K, 394, 1325, "в шкафу под мойкой"),
    (K, 464, 1342, "под посудомойкой, в цоколе"),
]


def water_overlay(leak_wires=False):
    o = S.Overlay(["supply", "sewer", "leak"])
    # узел ввода и коллекторы в шахте у с/у 2
    o.add("supply", f'<rect x="31" y="1134" width="27" height="114" rx="2" fill="#E7F5FF" stroke="{C["cold"]}" stroke-width="1.2"/>')
    o.add("supply", S.txt(44.5, 1191, "узел ввода и коллекторы", fs=6.2, font=S.SANS, weight=700, fill=C["cold"], rot=-90))
    o.add("supply", S.zone(58, 1134, 67, 1188, "#495057", None, fill_op=0.25, dash="3 2"))
    o.add("supply", S.txt(108, 1118 - 7, "люк над стиральной машиной", fs=6.2, font=S.SANS, weight=700, fill="#495057"))
    for code, x, y, col, _ in RISERS_W:
        o.add("supply", S.riser(x, y, code, col))
    o.add("supply", S.path([(20.4, 1146), (31, 1146)], C["cold"], 1.6) + S.path([(20.4, 1166), (31, 1166)], C["hot"], 1.6))
    o.add("leak", S.valve(25.5, 1146, motor=True) + S.valve(25.5, 1166, motor=True))
    for kind, _, _, pts in PIPES:
        o.add("supply", S.path(pts, C["cold"] if kind == "c" else C["hot"], 1.5))
    for room, name, x, y, d, kinds, *_ in FIXTURES:
        gap = 16 if len(kinds) == 2 else 8
        if name.startswith("Душ"):
            gap = 12
        o.add("supply", S.water_out(x, y, d, kinds, gap)[0])
    # канализация
    for name, dia, slope, pts in SEWER:
        o.add("sewer", S.path(pts, C["sewer"], 3.4 if dia == 110 else 2.4, opacity=0.9))
    for room, name, x, y, d, kinds, hw, sd, sh, riser, dp in FIXTURES:
        if dp:
            o.add("sewer", S.drain(dp[0], dp[1], dp[2]))
    for x, y in DRAIN_PTS:
        o.add("sewer", S.drain(x, y))
    for code, x, y in RISERS_K:
        o.add("sewer", S.riser(x, y, code, C["sewer"]))
    # подписи диаметров
    o.add("sewer", S.txt(330, 1351 - 7, "Ø50, 3 %", fs=6.4, fill=C["sewer"]))
    o.add("sewer", S.txt(52, 1296 + 8, "Ø110", fs=6.4, fill=C["sewer"]))
    o.add("sewer", S.txt(46, 678 - 7, "Ø110", fs=6.4, fill=C["sewer"]))
    o.add("sewer", S.txt(31, 620, "Ø50", fs=6.4, fill=C["sewer"], rot=-90))
    for _, x, y, _ in LEAK:
        o.add("leak", S.leak_sensor(x, y))
    return o.svg()


def water_legend():
    ic = S.icon
    return [
        (ic(S.water_out(0, -4, "d", ["c"])[0]), "Вывод холодной воды"),
        (ic(S.water_out(0, -4, "d", ["h"])[0]), "Вывод горячей воды"),
        (ic(S.path([(-9, 0), (9, 0)], C["cold"], 1.5) + S.path([(-9, 5), (9, 5)], C["hot"], 1.5), (-10, -8, 20, 18)), "Трубы от коллектора в стяжке"),
        (ic(S.drain(0, 0)), "Выпуск в канализацию"),
        (ic(S.path([(-9, 0), (9, 0)], C["sewer"], 2.6)), "Канализация"),
        (ic(S.riser(0, 0, "К1", C["sewer"])), "Стояк"),
        (ic(S.leak_sensor(0, 0)), "Датчик протечки"),
        (ic(S.valve(0, 2, motor=True)), "Кран с электроприводом"),
    ]


def water_rows(room=None):
    rows = []
    for r, name, x, y, d, kinds, hw, sd, sh, riser, dp in FIXTURES:
        if room and r != room:
            continue
        w = " + ".join({"c": "холодная", "h": "горячая"}[k] for k in kinds)
        rows.append(([RN[r]] if not room else []) + [name, w, num(hw), f"{sd}, {num(sh)}", riser])
    return rows


def pipe_len(pts):
    return S.path_len(pts) / 100 + 1.2   # подъёмы к выводу и в узле


def collector_rows():
    rows, n_c, n_h = [], 0, 0
    for kind, dest, room, pts in PIPES:
        if kind == "c":
            n_c += 1
            no = f"ХВС-{n_c}"
        else:
            n_h += 1
            no = f"ГВС-{n_h}"
        rows.append([no, dest, num(fmt(pipe_len(pts)))])
    return rows, n_c, n_h


def sewer_rows(room_filter=None):
    rows = []
    for name, dia, slope, pts in SEWER:
        L = S.path_len(pts) / 100
        drop = L * slope
        rows.append([name, f"Ø{dia}", num(fmt(L)), num(f"{slope} %"), num(f"{max(1, round(drop))} см")])
    return rows


def collector_svg():
    """Узел ввода и коллекторы: сверху ХВС, снизу ГВС."""
    W = 380
    chain = [("Кран", "отсечной"), ("Фильтр", "грубой"), ("Счётчик", ""), ("Обратный", "клапан"), ("Редуктор", "3 бар"), ("Электро-", "кран")]
    c_out = [dest for kind, dest, _, _ in PIPES if kind == "c"]
    h_out = [dest for kind, dest, _, _ in PIPES if kind == "h"]
    H = 70 + 52 + len(c_out) * 19 + 70 + 52 + len(h_out) * 19 + 40
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Узел ввода и коллекторы">',
           f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']

    def section(y0, title, col, outs, riser):
        s = [S.txt(14, y0 + 8, title, fs=11, font=S.SANS, weight=700, fill=col, anchor="start", halo=False)]
        yl = y0 + 42
        s.append(f'<circle cx="22" cy="{yl}" r="10" fill="#FFFFFF" stroke="{col}" stroke-width="2"/>')
        s.append(S.txt(22, yl, riser, fs=7.6, font=S.SANS, weight=700, fill=col, halo=False))
        s.append(f'<line x1="32" y1="{yl}" x2="352" y2="{yl}" stroke="{col}" stroke-width="3"/>')
        for i, (a, b) in enumerate(chain):
            x = 58 + i * 50
            if a == "Кран":
                s.append(S.valve(x, yl, color="#343A40").replace("4.2", "6"))
            elif a == "Фильтр":
                s.append(f'<path d="M{x - 7},{yl - 6} L{x + 7},{yl - 6} L{x},{yl + 9} Z" fill="#FFFFFF" stroke="#343A40" stroke-width="1.4"/>')
            elif a == "Счётчик":
                s.append(f'<circle cx="{x}" cy="{yl}" r="8" fill="#FFFFFF" stroke="#343A40" stroke-width="1.4"/>' + S.txt(x, yl, "м³", fs=6, font=S.SANS, halo=False))
            elif a == "Обратный":
                s.append(f'<rect x="{x - 8}" y="{yl - 6}" width="16" height="12" fill="#FFFFFF" stroke="#343A40" stroke-width="1.4"/><path d="M{x - 4},{yl - 4} L{x + 4},{yl} L{x - 4},{yl + 4}" fill="none" stroke="#343A40" stroke-width="1.4"/>')
            elif a == "Редуктор":
                s.append(f'<rect x="{x - 8}" y="{yl - 8}" width="16" height="16" rx="2" fill="#FFFFFF" stroke="#343A40" stroke-width="1.4"/><circle cx="{x}" cy="{yl - 15}" r="5" fill="#FFFFFF" stroke="#343A40" stroke-width="1.2"/>')
            else:
                s.append(S.valve(x, yl, motor=True))
            s.append(S.txt(x, yl + 18, a, fs=7.2, font=S.SANS, weight=600, halo=False))
            if b:
                s.append(S.txt(x, yl + 27, b, fs=6.6, font=S.SANS, weight=500, fill="#495057", halo=False))
        # коллектор
        yc = yl + 52
        s.append(f'<line x1="352" y1="{yl}" x2="352" y2="{yc - 10}" stroke="{col}" stroke-width="3"/>')
        s.append(f'<rect x="40" y="{yc - 10}" width="320" height="10" rx="3" fill="{col}" fill-opacity=".18" stroke="{col}" stroke-width="1.6"/>')
        s.append(S.txt(200, yc - 17, f"коллектор на {len(outs)} выходов, на каждом кран", fs=7.4, font=S.SANS, weight=600, fill=col, halo=False))
        for i, dest in enumerate(outs):
            yy = yc + 14 + i * 19
            x = 60 + (i % 8) * 0
            s.append(f'<path d="M{x},{yc} V{yy} H{x + 22}" fill="none" stroke="{col}" stroke-width="1.6"/>' if i == 0 else
                     f'<path d="M{x},{yy - 19} V{yy} H{x + 22}" fill="none" stroke="{col}" stroke-width="1.6"/>')
            s.append(S.valve(x + 30, yy, color=col))
            s.append(S.txt(x + 44, yy, f"{'ХВС' if col == C['cold'] else 'ГВС'}-{i + 1}  {dest}", fs=8, font=S.SANS, weight=500, anchor="start", halo=False))
        return "".join(s), yc + 14 + len(outs) * 19

    sec, y = section(8, "Холодная вода", C["cold"], c_out, "В1")
    out.append(sec)
    sec, y = section(y + 18, "Горячая вода", C["hot"], h_out, "Т3")
    out.append(sec)
    out.append(S.txt(W / 2, y + 16, "Трубы к точкам — сшитый полиэтилен 16 мм в гофре, целыми кусками без соединений в полу", fs=7.2, font=S.SANS, weight=500, fill="#495057", halo=False))
    out.append("</svg>")
    return "".join(out).replace(f'viewBox="0 0 {W} {H}"', f'viewBox="0 0 {W} {y + 30}"').replace(f'height="{H}" fill', f'height="{y + 30}" fill')


# ======================================================================== СЛАБОТОЧКА
# Порты патч-панели: (комната, что, путь кабеля)
TRUNK_N = [(60, 852), (200, 852), (200, 760)]
TRUNK_S = [(60, 866), (200, 866), (200, 1080), (620, 1080)]
PORTS = [
    ("spalnya", "Стол, лючок в полу — 1", TRUNK_N + [(385, 760), (385, 330), (835, 330), (835, 183)]),
    ("spalnya", "Стол, лючок в полу — 2", TRUNK_N + [(385, 760), (385, 330), (835, 330), (835, 183)]),
    ("spalnya", "ТВ на пилоне", TRUNK_N + [(385, 760), (385, 330), (600, 330), (600, 32)]),
    ("spalnya", "Запасная точка доступа AP-3 на потолке", TRUNK_N + [(385, 760), (385, 330), (700, 330), (700, 120)]),
    ("detskaya-1", "Стол — 1", TRUNK_N + [(361, 760), (361, 575), (806, 575), (806, 664)]),
    ("detskaya-1", "Стол — 2", TRUNK_N + [(361, 760), (361, 575), (806, 575), (806, 664)]),
    ("detskaya-2", "Стол — 1", TRUNK_N + [(806, 760), (806, 1000)]),
    ("detskaya-2", "Стол — 2", TRUNK_N + [(806, 760), (806, 1000)]),
    (K, "ТВ на стене", TRUNK_S + [(765, 1080), (765, 1352)]),
    (K, "ТВ-тумба: приставка, консоль", TRUNK_S + [(742, 1080), (742, 1352)]),
    ("koridor", "Точка доступа AP-1 на потолке", TRUNK_N + [(361, 760), (361, 490)]),
    (K, "Точка доступа AP-2 на потолке", TRUNK_S + [(620, 1190)]),
]
LAN_PTS = [  # розетки LAN на стене: (комната, x, y, d, n, h, где)
    ("spalnya", 600, 24, "d", 1, 110, "за ТВ на пилоне"),
    ("detskaya-1", 806, 672, "u", 2, 85, "у торца стола"),
    ("detskaya-2", 806, 1008, "u", 2, 85, "у торца стола"),
    (K, 765, 1360, "u", 1, 110, "за ТВ на стене"),
    (K, 742, 1360, "u", 1, 30, "за ТВ-тумбой"),
]
APS = [("koridor", 361, 480, "AP-1", False), (K, 620, 1200, "AP-2", False), ("spalnya", 700, 110, "AP-3 запас", True)]


def lan_len(pts, ceiling=False):
    return S.path_len(pts) / 100 + (3.6 if ceiling else 2.0)   # подъёмы по стене, запас в шкафу и в точке


LEAK_WIRES = [
    [(45, 535), (170, 535), (170, 880), (62, 880)],
    [(104, 668), (170, 668)],
    [(97, 1196), (150, 1196), (150, 880)],
    [(258, 1166), (150, 1166)],
    [(48, 1134), (48, 1124), (150, 1124)],
    [(394, 1325), (340, 1325), (340, 1222), (150, 1222), (150, 1196)],
    [(464, 1342), (464, 1325), (394, 1325)],
]


def lan_overlay():
    o = S.Overlay(["cables", "lan", "leak", "other"])
    x1, y1, x2, y2 = TECH
    o.add("lan", S.zone(x1, y1, x2, y2, C["lan"], None, fill_op=0.12))
    o.add("lan", S.txt(30, 846, "шкаф", fs=7, font=S.SANS, weight=700, fill=C["lan"]))
    o.add("lan", S.txt(30, 857, "роутер", fs=6.2, font=S.SANS, weight=500, fill=C["lan"]))
    o.add("lan", S.txt(30, 867, "сервер", fs=6.2, font=S.SANS, weight=500, fill=C["lan"]))
    seen = set()
    for room, what, pts in PORTS:
        key = tuple(pts)
        if key in seen:
            continue
        seen.add(key)
        o.add("cables", S.cable(pts))
    o.add("cables", S.txt(130, 846, "12 кабелей", fs=6.6, font=S.SANS, weight=700, fill=C["lan"]))
    o.add("cables", S.txt(272, 752, "8", fs=6.6, font=S.SANS, weight=700, fill=C["lan"]))
    o.add("cables", S.txt(392, 545, "4", fs=6.6, font=S.SANS, weight=700, fill=C["lan"]))
    o.add("cables", S.txt(300, 1072, "4", fs=6.6, font=S.SANS, weight=700, fill=C["lan"]))
    for room, x, y, d, n, h, where in LAN_PTS:
        s, w = S.rj45(x, y, d, n)
        o.add("lan", s)
        lx, ly = S.label_pos(x, y, d, 15)
        o.add("lan", S.txt(lx, ly, h, fs=6.6, fill=C["lan"]))
    o.add("lan", S.floorbox(835, 175).replace(C["power"], C["lan"]))
    o.add("lan", S.txt(835, 190, "лючок", fs=6.4, font=S.SANS, fill=C["lan"]))
    for room, x, y, label, reserve in APS:
        o.add("lan", S.ap(x, y, label, reserve))
    # домофон и ввод провайдера
    o.add("other", S.cable([(-46, 711), (40, 711), (40, 713)], "#7048E8", 1.3))
    o.add("other", S.device(40, 707, "d", "Д", "#7048E8"))
    o.add("other", S.txt(-50, 724, "домофон", fs=6.4, font=S.SANS, weight=700, fill="#7048E8", anchor="end"))
    o.add("other", S.cable([(-46, 846), (2, 846)], "#495057", 2.2, dash="5 3") + S.cable([(-46, 853), (2, 853)], "#495057", 2.2, dash="5 3"))
    o.add("other", S.txt(-50, 838, "оптика из этажного щита", fs=6.4, font=S.SANS, weight=700, fill="#495057", anchor="end"))
    o.add("other", S.txt(-50, 860, "2 трубы Ø25", fs=6.2, font=S.SANS, fill="#495057", anchor="end"))
    for w in LEAK_WIRES:
        o.add("leak", S.cable(w, C["leak"], 0.9, dash="2.5 2"))
    for _, x, y, _ in LEAK:
        o.add("leak", S.leak_sensor(x, y))
    o.add("leak", S.valve(25.5, 1146, motor=True) + S.valve(25.5, 1166, motor=True))
    o.add("leak", S.txt(92, 1124 - 7, "краны с приводом", fs=6, font=S.SANS, weight=700, fill=C["leak"]))
    return o.svg()


def lan_legend():
    ic = S.icon
    return [
        (ic(S.rj45(0, -5, "d", 1)[0]), "Розетка LAN, рядом высота"),
        (ic(S.ap(0, 0, None), (-12, -12, 24, 24)), "Точка доступа Wi-Fi на потолке"),
        (ic(S.ap(0, 0, None, True), (-12, -12, 24, 24)), "Запасная точка: кабель есть"),
        (ic(S.cable([(-9, 0), (9, 0)])), "Витая пара Cat6"),
        (ic(S.device(0, -6, "d", "Д", "#7048E8")), "Монитор домофона"),
        (ic(S.leak_sensor(0, 0)), "Датчик протечки"),
        (ic(S.cable([(-9, 0), (9, 0)], C["leak"], 0.9, dash="2.5 2")), "Провод датчика"),
    ]


def cabinet_svg():
    """Вид спереди на техническую секцию шкафа-купе: 60 см шириной, ниже антресоли."""
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-30 -18 300 290" role="img" aria-label="Техническая секция шкафа">',
           '<rect x="-30" y="-18" width="300" height="290" fill="#FFFFFF"/>']
    Y = lambda h: 240 - h   # noqa: E731  высота от пола → y

    def item(x, h0, w, hh, title, col, fill, label_y=None, lines=()):
        s = f'<rect x="{x}" y="{Y(h0 + hh)}" width="{w}" height="{hh}" rx="2" fill="{fill}" stroke="{col}" stroke-width="1.2"/>'
        s += S.txt(x + w / 2, Y(h0 + hh / 2), title, fs=6.2 if w < 30 else 7, font=S.SANS, weight=700, fill=col, halo=False)
        if lines:
            ly = label_y if label_y is not None else Y(h0 + hh / 2)
            s += f'<line x1="{x + w}" y1="{Y(h0 + hh / 2)}" x2="{92}" y2="{ly}" stroke="#ADB5BD" stroke-width="0.7"/>'
            for i, ln in enumerate(lines):
                s += S.txt(96, ly + i * 9 - (len(lines) - 1) * 4.5, ln, fs=7 if i == 0 else 6.4, font=S.SANS, weight=700 if i == 0 else 500,
                           anchor="start", fill="#1F2A30" if i == 0 else "#495057", halo=False)
        return s

    out.append(f'<rect x="0" y="{Y(240)}" width="60" height="240" fill="#FBF8F2" stroke="#495057" stroke-width="1.6"/>')
    out.append(f'<rect x="0" y="{Y(240)}" width="60" height="30" fill="#EBD3B1" stroke="#A87A42" stroke-width="1"/>')
    out.append(S.txt(30, Y(225), "антресоль", fs=6.4, font=S.SANS, halo=False, fill="#8A6234"))
    out.append(item(5, 145, 50, 62, "ЩК", "#343A40", "#E9ECEF", Y(176), ["Щит квартиры", "54 модуля, 140–207 см"]))
    out.append(item(6, 118, 22, 16, "", C["leak"], "#E3FAFC", Y(130), ["Контроллер протечек", "и блок питания домофона"]))
    out.append(item(32, 118, 22, 16, "", "#7048E8", "#F3F0FF"))
    out.append(item(5, 82, 50, 27, "19″ 6U", C["lan"], "#E6FCF5", Y(98), ["Стойка 19″ на 6 юнитов", "патч-панель 24, коммутатор 16 с PoE,", "роутер, терминал, блок розеток ИБП"]))
    for i in range(1, 6):
        out.append(f'<line x1="6" y1="{Y(82 + i * 4.5)}" x2="54" y2="{Y(82 + i * 4.5)}" stroke="{C["lan"]}" stroke-width="0.5"/>')
    out.append(f'<rect x="2" y="{Y(48)}" width="56" height="2" fill="#A87A42"/>')
    out.append(item(8, 50, 26, 20, "сервер", "#1F2A30", "#F1F3F5", Y(60), ["Домашний сервер", "мини-ПК или NAS на 2 диска"]))
    out.append(item(4, 0, 16, 36, "ИБП", C["ups"], "#FFF4E6", Y(26), ["ИБП 1 кВА и батарея", "LiFePO4 24 В 50 А·ч на полу"]))
    out.append(item(24, 0, 30, 21, "АКБ", C["ups"], "#FFF4E6"))
    # вентиляция
    for x in (14, 30, 46):
        out.append(f'<path d="M{x},{Y(-6)} V{Y(8)}" stroke="#4DABF7" stroke-width="1.4" marker-end="none"/><polygon points="{x - 3},{Y(5)} {x + 3},{Y(5)} {x},{Y(10)}" fill="#4DABF7"/>')
        out.append(f'<path d="M{x},{Y(210)} V{Y(222)}" stroke="#FA5252" stroke-width="1.4"/><polygon points="{x - 3},{Y(219)} {x + 3},{Y(219)} {x},{Y(224)}" fill="#FA5252"/>')
    out.append(S.txt(30, Y(-12), "решётка в цоколе — холодный воздух", fs=6.2, font=S.SANS, fill="#1C7ED6", halo=False))
    out.append(S.txt(140, Y(214), "щель под антресолью — тёплый воздух наружу", fs=6.2, font=S.SANS, fill="#E03131", halo=False))
    # размеры
    out.append(f'<line x1="-14" y1="{Y(0)}" x2="-14" y2="{Y(240)}" stroke="#495057" stroke-width="0.8"/>')
    for h in (0, 50, 82, 118, 145, 210, 240):
        out.append(f'<line x1="-18" y1="{Y(h)}" x2="-10" y2="{Y(h)}" stroke="#495057" stroke-width="0.8"/>' + S.txt(-20, Y(h), h, fs=6, anchor="end", halo=False))
    out.append(f'<line x1="0" y1="{Y(-4) + 8}" x2="60" y2="{Y(-4) + 8}" stroke="#495057" stroke-width="0.8"/>')
    out.append(S.txt(30, Y(-4) + 16, "60 см", fs=6.4, halo=False))
    out.append("</svg>")
    return "".join(out)


CABINET_ITEMS = [
    ("Стойка 19″ на 6 юнитов, открытая, на стене", "крепится к стене секции на 82–109 см"),
    ("Патч-панель Cat6 на 24 порта", "12 кабелей сейчас, 12 портов в запасе"),
    ("Коммутатор на 16 портов 1 Гбит, 4 порта PoE+", "питает точки доступа по кабелю"),
    ("Роутер", "Wi-Fi в нём не нужен: раздают точки доступа"),
    ("Оптический терминал провайдера", "ставит провайдер"),
    ("Блок розеток в стойку, 4–6 мест", "от линии ИБП"),
    ("Домашний сервер: мини-ПК или NAS на 2 диска", "на полке 50 см, USB-кабель к ИБП"),
    ("Две точки доступа Wi-Fi 6 на потолке", "коридор и кухня-гостиная, одна сеть по всей квартире"),
    ("ИБП 1 кВА и батарея LiFePO4 24 В 50 А·ч", "на полу секции, общая линия ИБП"),
    ("Контроллер защиты от протечек", "6 датчиков и 2 крана с приводом, от линии ИБП"),
]


# ======================================================================== СБОРКА РАЗДЕЛОВ
def blocks_tables(title, head, rows, note=None):
    return ("table", title, head, rows, note)


def build(n):
    if n != 1:
        return {}
    # --- электрика
    counts, tot = el_counts()
    gr_rows = [[num(g), a, b, c, num(fmt(p))] for g, (a, b, c, p) in GROUPS.items()]
    gr_rows += [["—", "Резерв: " + r, "место в щите", "—", "—"] for r in RESERVE]
    total_kw = sum(v[3] for v in GROUPS.values())
    rooms_el = {}
    for r in ROOM_ORDER:
        bl = []
        rows = el_room_rows(r)
        if rows:
            bl.append(("table", "Розетки и выводы", ["Что", "Где", "Высота, см", "Группа"], rows, None))
        rows = el_light_rows(r)
        if rows:
            bl.append(("table", "Свет и выключатели", ["Что", "Где", "Высота, см", "Группа"], rows, None))
        rooms_el[r] = bl
    elektrika = {
        "lede": ("Розетки, выводы под технику, свет и выключатели, 17 групп в щите и отдельная линия от ИБП. "
                 "Оранжевые розетки, Wi-Fi, сервер и домофон работают и при отключении света."),
        "layers": [("light", "Свет и выключатели", True), ("links", "Связи", True), ("power", "Розетки", True),
                   ("groups", "Номера групп", False), ("furn", "Мебель", True)],
        "overlay": el_overlay(),
        "legend": el_legend(),
        "blocks": [
            ("cards", [
                ("Щит и ИБП", "у входа", [
                    "Щит на 54 модуля, ИБП и слаботочный шкаф стоят в технической секции шкафа-купе у входной двери. Кабель от этажного щита заходит через стену рядом.",
                    "17 групп: свет отдельно от розеток, каждая мощная техника на своём автомате. Розетки и мокрые зоны через дифавтоматы 30 мА.",
                    "Четыре места в щите оставлены в резерве: тёплый пол, кондиционеры, водонагреватель.",
                ]),
                ("Линия ИБП", "5 оранжевых розеток", [
                    "Оранжевые розетки: у кровати в спальне с двух сторон, у столов в детских, у дивана в гостиной. В них заряжаются телефоны, когда нет света.",
                    "От той же линии работают роутер, Wi-Fi, сервер, домофон и защита от протечек.",
                    "Батарея на ≈ 1 кВт·ч держит всё это около 8 часов.",
                ]),
                ("Высоты", "от чистового пола", [
                    f"Выключатели {num(90)} см, у двери со стороны ручки. Розетки у пола {num(30)}, у кровати {num(70)}, у стола {num(85)}, за ТВ и над столешницей {num(110)}.",
                    "Свет в спальне включается от двери и с обеих сторон кровати. Свет коридора — от входа и у детских.",
                    "Ночью в коридоре подсветка у пола по датчику движения. В кладовой свет включается сам.",
                ]),
            ]),
            ("table", "Группы щита", ["№", "Что питает", "Защита", "Кабель", "кВт"], gr_rows,
             f"Сумма мощностей {fmt(total_kw)} кВт, но одновременно включено обычно не больше 8–10 кВт. Ввод 50 А на одну фазу — уточнить выделенную мощность у застройщика."),
            ("table", "Сколько точек", ["Комната", "Розетки", "из них ИБП", "Выводы под технику", "Светильники", "Выключатели"], counts,
             "Лючок в полу спальни посчитан как 2 розетки. Щит, розетки ИБП и сеть в технической секции — в таблице прихожей."),
            ("cards", [
                ("Уточнить у застройщика", None, [
                    "Выделенную мощность и число фаз: от этого зависит вводной автомат.",
                    "Где этажный щит и счётчик, ставит ли застройщик свой щиток в квартире.",
                    "Какие стены монолитные: их не штробят, кабели идут в полу и над потолком.",
                    "Высоту стяжки: для лючка в полу под столом в спальне нужно 7–8 см.",
                ]),
                ("Решить до черновых работ", None, [
                    "Кондиционеры: если будут, трассы и кабель закладываем сейчас.",
                    "Тёплый пол в санузлах и водонагреватель на время летнего отключения горячей воды.",
                    "Полотенцесушители: здесь электрические. Если застройщик поставит водяные от стояка, электрика к ним не нужна.",
                ]),
            ]),
        ],
        "rooms": rooms_el,
        "extras": {
            "shchit": {
                "lede": "Щит на 54 модуля в технической секции шкафа-купе у входа, на высоте 140–207 см. Вводной выключатель, реле напряжения, защита от скачков, пожарное УЗО и 17 групп.",
                "blocks": [
                    ("diagram", "Раскладка модулей", panel_svg(), "Синие — дифавтоматы, оранжевые — линия ИБП, пунктир — свободные места."),
                    ("table", "Группы", ["№", "Что питает", "Защита", "Кабель", "кВт"], gr_rows, None),
                    ("cards", [
                        ("Ввод", None, [
                            "Вводной выключатель нагрузки 63 А отключает всю квартиру.",
                            "Реле напряжения 63 А отключает квартиру при скачке выше 250 В или просадке ниже 180 В и включает обратно само.",
                            "УЗИП второго типа защищает технику от перенапряжений в сети дома.",
                            "Пожарное УЗО 100 мА стоит перед всеми группами.",
                        ]),
                        ("Как собирать", None, [
                            "Кабель медный ВВГнг(А)-LS. Свет — 3×1,5, розетки — 3×2,5, варочная — 3×6.",
                            "У каждой группы свой ноль, ноли разных дифавтоматов не объединять.",
                            "Линию ИБП подключить через переключатель SA, её ноль не соединять с другими группами.",
                            "Подписать каждый автомат, схему положить в дверцу щита.",
                        ]),
                    ]),
                ],
            },
            "ibp": {
                "lede": ("Небольшой ИБП с внешней батареей держит отдельную линию: оранжевые розетки для зарядки телефонов, роутер, Wi-Fi, "
                         "сервер, домофон и защиту от протечек. Свет погас — эта линия продолжает работать без перерыва."),
                "blocks": [
                    ("diagram", "Как подключено", ups_svg(), "Переключатель SA в щите: «ИБП» — обычный режим, «сеть» — если ИБП сломался или его меняют, «0» — линия выключена."),
                    ("table", "Что работает от ИБП", ["Потребитель", "Вт"], [[a, num(b)] for a, b in UPS_LOADS], None),
                    ("table", "Сколько продержится", ["Вариант", "ИБП и батарея", "Полезный запас, кВт·ч", "Время при 90 Вт"],
                     [[a, b, num(c), d] for a, b, c, d in UPS_OPTIONS],
                     "В расчёте учтён собственный расход ИБП ≈ 20 Вт и потери ≈ 15 %."),
                    ("cards", [
                        ("Что купить", None, [
                            "ИБП 1 кВА (700–800 Вт) с чистой синусоидой и входом для внешней батареи 24 В. В паспорте должна быть зарядка литиевых батарей или настройка тока и напряжения заряда.",
                            "Батарея LiFePO4 24 В 50 А·ч со встроенной платой защиты.",
                            "Оранжевые розетки той же серии, что и остальные, с USB. Если оранжевых нет — наклейка «ИБП».",
                        ]),
                        ("Правила", None, [
                            "В оранжевые розетки не включаем чайник, фен, обогреватель и пылесос: ИБП на 700–800 Вт.",
                            "Сервер подключить к ИБП USB-кабелем: при долгом отключении он сам корректно выключится.",
                            "Раз в год проверять: выключить вводной автомат и посмотреть, сколько держит батарея.",
                            "Если нужен только интернет, хватит мини-ИБП на 12 В для роутера, но розеток для зарядки он не даст.",
                        ]),
                    ]),
                ],
            },
        },
    }

    # --- водопровод
    coll_rows, n_c, n_h = collector_rows()
    pex = sum(pipe_len(p[3]) for p in PIPES)
    rooms_w = {}
    for r in ROOM_ORDER:
        rows = water_rows(r)
        if rows:
            bl = [("table", "Точки подключения", ["Прибор", "Вода", "Высота выводов, см", "Канализация, высота", "Стояк"], rows, None)]
            ls = [[where] for rr, x, y, where in LEAK if rr == r]
            if ls:
                bl.append(("table", "Датчики протечки", ["Где"], ls, None))
            rooms_w[r] = bl
    santehnika = {
        "lede": ("Узел ввода и коллекторы в шахте у с/у 2, к каждому прибору своя труба без соединений в полу. "
                 "Канализация к трём стоякам короткими линиями. На вводе краны с приводом и 6 датчиков протечки."),
        "layers": [("supply", "Вода", True), ("sewer", "Канализация", True), ("leak", "Протечки", True), ("furn", "Мебель", True)],
        "overlay": water_overlay(),
        "legend": water_legend(),
        "blocks": [
            ("cards", [
                ("Ввод и коллекторы", "шахта у с/у 2", [
                    "Стояки холодной и горячей воды, по плану застройщика, в большой шахте слева от с/у 2. Узел ввода и коллекторы — там же, за люком над стиральной машиной.",
                    f"Коллектор холодной воды на {n_c} выходов, горячей — на {n_h}. У каждого прибора свой кран на коллекторе.",
                    f"Трубы из сшитого полиэтилена 16 мм в гофре, в стяжке пола, целыми кусками. Всего около {num(round(pex))} м.",
                ]),
                ("Канализация", "3 стояка", [
                    "К1 в шахте с/у 1: ванна, раковина и унитаз рядом со стояком.",
                    "К2 у унитаза с/у 2: унитаз и стиральная машина.",
                    "К3 в шахте за душем: трап душа, раковина с/у 2 и кухонная мойка. Мойка у стояка — линия всего 1,5 м.",
                ]),
                ("Защита от протечек", "6 датчиков", [
                    "Датчики под ванной, у унитаза, у стиральной машины, под раковиной с/у 2, под мойкой и под посудомойкой.",
                    "Сработал датчик — краны с приводом на вводе перекрывают холодную и горячую воду.",
                    "Контроллер в технической секции у входа, питается от линии ИБП.",
                ]),
            ]),
            ("table", "Точки подключения", ["Помещение", "Прибор", "Вода", "Высота выводов, см", "Канализация, высота", "Стояк"], water_rows(),
             "Высоты от чистового пола. Точные высоты для инсталляций и скрытого смесителя — по инструкции выбранной модели."),
            ("table", "Канализация", ["Откуда", "Диаметр", "Длина, м", "Уклон", "Перепад"], sewer_rows(),
             "Минимальный уклон для труб 50 мм — 2 %, для 110 мм — 1 %. Взяли с запасом."),
            ("cards", [
                ("Уточнить у застройщика", None, [
                    "Где стояки холодной и горячей воды и счётчики: в квартире или в общем коридоре. От этого зависит место узла ввода.",
                    "Какие шахты — канализация, какие — вентиляция.",
                    "Давление в сети: редуктор ставим в любом случае, настройка 3 бар.",
                    "Будет ли водяной полотенцесушитель на стояке горячей воды.",
                ]),
                ("Решить до черновых работ", None, [
                    "Фильтр питьевой воды под мойкой: нужна розетка рядом, если фильтр с насосом.",
                    "Водонагреватель на время летнего отключения горячей воды: место и вывод.",
                    "Высота трапа душа без поддона: пол в душе с уклоном 1–2 % к стене, трап с низким сифоном.",
                ]),
            ]),
        ],
        "rooms": rooms_w,
        "extras": {
            "kollektor": {
                "lede": ("Узел ввода и коллекторы в большой шахте слева от с/у 2, доступ через люк над стиральной машиной. "
                         "Холодная и горячая вода проходят одну и ту же цепочку: кран, фильтр, счётчик, обратный клапан, редуктор, кран с приводом, коллектор."),
                "blocks": [
                    ("diagram", "Схема узла", collector_svg(), "Счётчики обычно ставит застройщик. Кран с приводом закрывает воду по сигналу датчика протечки."),
                    ("table", "Выходы коллекторов", ["Выход", "Куда", "Длина трубы, м"], coll_rows,
                     f"Всего около {fmt(pex, 0)} м трубы 16 мм. С/у 1 далеко — около 9–10 м: горячая вода дойдёт за 10–15 секунд."),
                    ("cards", [
                        ("Доступ", None, [
                            "Люк 60×60 см в стене шахты над стиральной машиной, за дверцей навесного шкафчика.",
                            "Все краны коллектора подписаны: какой прибор, холодная или горячая.",
                            "Фильтры промывные, их видно и можно промыть без разборки.",
                        ]),
                    ]),
                ],
            },
        },
    }

    # --- слаботочка
    port_rows = []
    total_lan = 0
    for i, (room, what, pts) in enumerate(PORTS, 1):
        L = lan_len(pts, ceiling="точка доступа" in what.lower())
        total_lan += L
        port_rows.append([num(i), RN[room], what, num(fmt(L, 0))])
    port_rows.append([num("13–24"), "—", "свободно", "—"])
    rooms_lan = {}
    for r in ROOM_ORDER:
        rows = [[num(i), what, num(fmt(lan_len(pts, 'точка доступа' in what.lower()), 0))] for i, (room, what, pts) in enumerate(PORTS, 1) if room == r]
        bl = []
        if rows:
            bl.append(("table", "Кабели в этой комнате", ["Порт", "Куда", "Длина, м"], rows, None))
        ls = [[where] for rr, x, y, where in LEAK if rr == r]
        if ls:
            bl.append(("table", "Датчики протечки", ["Где"], ls, None))
        if r == "prihozhaya":
            bl.append(("cards", [("Техническая секция", "у входной двери", [
                "Здесь сходятся все кабели: шкаф со стойкой, роутер, коммутатор, сервер, ИБП.",
                "Монитор домофона у входной двери на 150 см, питание от линии ИБП.",
            ])]))
        if bl:
            rooms_lan[r] = bl
    slabotochka = {
        "lede": ("Каждая сетевая розетка и точка доступа — свой кабель Cat6 до шкафа в прихожей. "
                 "Wi-Fi раздают две точки доступа на потолке, роутер и домашний сервер стоят в шкафу и работают от ИБП."),
        "layers": [("cables", "Кабели", True), ("lan", "Розетки и Wi-Fi", True), ("leak", "Протечки", True),
                   ("other", "Домофон и ввод", True), ("furn", "Мебель", True)],
        "overlay": lan_overlay(),
        "legend": lan_legend(),
        "blocks": [
            ("cards", [
                ("Wi-Fi", "2 точки доступа", [
                    "Шкаф у входа далеко от спален, поэтому Wi-Fi раздаёт не роутер, а две точки доступа на потолке: в коридоре и в кухне-гостиной.",
                    "Точки питаются по тому же кабелю (PoE) и работают одной сетью: телефон переключается между ними сам.",
                    "Кабель к третьей точке на потолке спальни заложен про запас.",
                ]),
                ("Розетки LAN", "12 кабелей", [
                    "По 2 розетки у столов в детских, 2 в лючке под столом в спальне, за ТВ в спальне и в гостиной.",
                    "Кабели идут в стяжке пола в гофре, к точкам доступа — по стене и над натяжным потолком.",
                    f"Всего около {num(round(total_lan))} м кабеля: хватит одной коробки 305 м.",
                ]),
                ("Сервер и роутер", "в шкафу у входа", [
                    "Стойка 19″ на 6 юнитов в технической секции шкафа-купе: патч-панель, коммутатор, роутер, терминал провайдера.",
                    "Домашний сервер на полке ниже, ИБП и батарея на полу.",
                    "Всё от линии ИБП: при отключении света интернет и Wi-Fi работают около 8 часов.",
                ]),
            ]),
            ("table", "Порты патч-панели", ["Порт", "Комната", "Куда", "Длина, м"], port_rows,
             "Длина — по трассе на плане, с подъёмами по стене и запасом 1 м в шкафу."),
            ("cards", [
                ("Ещё в разделе", None, [
                    "Домофон: кабель из общего коридора к монитору у входной двери.",
                    "Ввод провайдера: 2 трубы Ø25 из этажного слаботочного щита в шкаф, одна про запас для второго провайдера.",
                    "Защита от протечек: 6 датчиков на проводах и 2 крана с приводом, контроллер в шкафу.",
                    "Пожарные датчики — автономные, на батарейках, их ставит застройщик. Проводов не нужно.",
                ]),
                ("Уточнить у застройщика", None, [
                    "Какие провайдеры заходят в дом и где этажный слаботочный щит.",
                    "Какой домофон в доме и какой монитор к нему подходит.",
                ]),
            ]),
        ],
        "rooms": rooms_lan,
        "extras": {
            "shkaf": {
                "lede": "Техническая секция шкафа-купе у входной двери, 60 см шириной: щит, стойка с сетевым оборудованием, сервер, ИБП и батарея. Секция проветривается снизу вверх.",
                "blocks": [
                    ("diagram", "Вид спереди", cabinet_svg(), "Высоты в сантиметрах от пола. Купе-дверь закрывает секцию, решётка в цоколе и щель под антресолью дают воздух."),
                    ("table", "Что стоит в секции", ["Что", "Зачем и где"], [list(x) for x in CABINET_ITEMS], None),
                    ("cards", [
                        ("Почему здесь", None, [
                            "Кабель провайдера и силовой кабель заходят рядом, у входной двери.",
                            "Всё оборудование в одном месте, рядом с ИБП: короткие провода, одна линия ИБП.",
                            "Сервер и ИБП шумят тихо, а за дверью шкафа их не слышно.",
                        ]),
                        ("Что учесть", None, [
                            "Перегородку секции от одежды сделать сплошной, полки — металлическими или из ЛДСП 18 мм.",
                            "Тепла немного, около 100 Вт, но воздух должен идти: снизу решётка, сверху щель.",
                            "Свободное место на патч-панели — для камер, второго ТВ и будущих точек.",
                        ]),
                    ]),
                ],
            },
        },
    }
    return {"elektrika": elektrika, "santehnika": santehnika, "slabotochka": slabotochka}
