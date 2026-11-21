"""Инженерные разделы: электрика, водопровод и канализация, слаботочка.

Проработан вариант 1. Координаты — сантиметры плана, как в layout.py.
Точка на стене: (x, y) на линии стены и d — направление в комнату (u, d, l, r).
build(n) отдаёт сайту для каждого раздела: слои поверх плана, легенду, таблицы,
страницы комнат и дополнительные страницы (щит, коллектор, техническая секция).
"""
import math

import eng_svg as S
from eng_svg import C
from panel_wiring import wiring_blocks
from panel_model import GROUPS, GROUP_MERGES, BANKS, BANK_OF, BRANCHES, DEV, PANEL_ROWS
from panel_readable import overview_svg, circuit_pages, supply_svg
from power_budget import blocks as power_blocks
from load_priority import CONTROLLED, blocks as priority_blocks
from electrical_docs import build as build_electrical, image_block
from renovation_model import CLEAR_HEIGHT as PLAN_CLEAR_HEIGHT

RN = {
    "spalnya": "Спальня", "detskaya-1": "Детская 1", "detskaya-2": "Детская 2",
    "kuhnya-gostinaya": "Кухня-гостиная", "prihozhaya": "Прихожая", "sport": "Спорт-кладовая",
    "koridor": "Коридор", "su-1": "С/у 1", "su-2": "С/у 2",
}
ROOM_ORDER = list(RN)

TECH = (0, 826, 60, 886)   # техническая секция шкафа-купе у входа: щит, сеть, сервер


def num(v):
    return f'<span class="num">{v}</span>'


def fmt(v, d=1):
    return f"{v:.{d}f}".replace(".", ",")


# ======================================================================== ЭЛЕКТРИКА
# №: (что питает, защита, кабель ВВГнг(А)-LS, кВт)
RESERVE = [
    "водонагреватель на время летнего отключения горячей воды",
]

APPL = {
    "ПММ": "Посудомоечная машина", "Дух": "Духовой шкаф", "Вар": "Варочная панель", "Хол": "Холодильник",
    "СВЧ": "Встроенная СВЧ", "Выт": "Вытяжка", "Стир": "Стиральная машина", "Суш": "Сушильная машина",
    "ТП": "Питание терморегулятора тёплого пола", "Конд": "Точка питания и управления кондиционером",
    "ПС": "Полотенцесушитель",
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
sock("spalnya", 446, 354, "u", ["std", "std"], 70, 4, "у тумбочки слева")
sock("spalnya", 716, 354, "u", ["std", "std"], 70, 4, "у тумбочки справа")
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
sock("detskaya-1", 836, 672, "u", ["std", "std", "std"], 85, 5, "у торца стола")
sock("detskaya-1", 750, 363, "d", ["std"], 65, 5, "в стеллаже-тумбочке у изголовья: телефон заряжается на полке")
sw("detskaya-1", 425, 514, "r", [("norm", "k1_main")], 90, 1, "у двери, со стороны ручки, между полками и наличником")
lt("detskaya-1", "ceiling", 640, 520, "k1_main", 1, "потолочный светильник")
lt("detskaya-1", "sconce", 710, 363, "k1_bra", 1, "бра у изголовья, выключатель на самом бра", d="d")
sock("detskaya-2", 836, 1008, "u", ["std", "std", "std"], 85, 6, "у торца стола")
sock("detskaya-2", 540, 1008, "u", ["std"], 60, 6, "над тумбочкой у изголовья: телефон, ночник")
sock("detskaya-2", 782, 706, "d", ["std"], 30, 6, "у кресла-мешка: лампа, гирлянда")
sw("detskaya-2", 445, 706, "d", [("norm", "k2_main")], 90, 1, "у двери, со стороны ручки")
lt("detskaya-2", "ceiling", 630, 870, "k2_main", 1, "потолочный светильник")
lt("detskaya-2", "sconce", 425, 982, "k2_bra", 1, "бра внутри кровати-домика, выключатель на самом бра", d="r")

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
out(K, 294, 1230, "r", "СВЧ", 200, 9, "в колонне над СВЧ; общая отключаемая линия кухни")
sock(K, 530, 1018, "d", ["std"], 90, 8, "над скамьёй: ноутбук, зарядка")
sock(K, 640, 1018, "d", ["std", "std"], 30, 8, "у дивана слева")
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
sw("su-1", 192, 526, "r", [("norm", "s1_main"), ("norm", "s1_fan")], 90, 3, "снаружи, в коридоре у двери, между шкафом и наличником")
lt("su-1", "spot", 90, 506, "s1_main", 3, "точечный над ванной, IP65")
lt("su-1", "spot", 95, 612, "s1_main", 3, "точечный, IP44")
lt("su-1", "mirror", 0, 592, "s1_main", 3, "подсветка зеркала на 200 см", d="r")
lt("su-1", "fan", 40, 662, "s1_fan", 3, "вентилятор в вентканал, с таймером", d="r")
sock("su-1", 0, 634, "r", ["std"], 110, 15, "у зеркала: фен, бритва; с крышкой IP44")
out("su-1", 183, 505, "l", "ПС", 110, 15, "электрический полотенцесушитель над краем ванны")
sw("su-2", 218, 1118, "u", [("norm", "s2_main"), ("norm", "s2_fan")], 90, 3, "снаружи, в прихожей справа от двери, за наличником")
lt("su-2", "spot", 172, 1172, "s2_main", 3, "точечный, IP44")
lt("su-2", "spot", 137, 1266, "s2_main", 3, "точечный над душем, IP65")
lt("su-2", "mirror", 284, 1163, "s2_main", 3, "подсветка зеркала на 200 см", d="l")
lt("su-2", "fan", 67, 1292, "s2_fan", 3, "вентилятор в вентканал над душем, IPX4, с таймером", d="r")
sock("su-2", 284, 1140, "l", ["std"], 115, 15, "у зеркала: фен; с крышкой IP44")
out("su-2", 67, 1190, "r", "Стир", 110, 14, "отдельная розетка сбоку от колонны, доступна без снятия машин, с крышкой IP44")
out("su-2", 67, 1204, "r", "Суш", 150, 18, "отдельная розетка сбоку от колонны, не за машинами; высоту сверить по комплекту установки")
out("su-2", 284, 1224, "l", "ПС", 110, 15, "электрический полотенцесушитель на правой стене, в 75 см от душа")
out("su-1", 192, 548, "r", "ТП", 150, 19, "терморегулятор снаружи санузла; кабель датчика пола отдельно")
out("su-2", 230, 1118, "u", "ТП", 150, 19, "терморегулятор снаружи санузла; кабель датчика пола отдельно")
out("spalnya", 770, 0, "d", "Конд", 230, 20, "общая QF20 для двух кондиционеров; питание блоков и допустимость снятия питания — по модели")
out(K, 860, 1170, "l", "Конд", 230, 21, "общая QF20 для двух кондиционеров; отдельная ветвь от клемм этой группы")

# Старые номера объединённых ветвей преобразуются до построения всех планов.
for point in EL + SW + LT:
    point["g"] = GROUP_MERGES.get(point["g"], point["g"])

TECH_EL = [
    ("prihozhaya", "Щит квартиры на 54 модуля", "техническая секция шкафа-купе; корпус и высоты уточнить", "по корпусу", "—"),
    ("prihozhaya", "Розетки сети, роутера, коммутатора и сервера", "техническая секция, монтажная панель", "70", 8),
    ("prihozhaya", "Питание защиты от протечек и домофона", "техническая секция", "120", 8),
]


def kinds_text(kinds):
    count = len(kinds)
    return "Розетка" if count == 1 else f"{count} розетки"


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


def el_overlay(mode="all"):
    o = S.Overlay(["links", "light", "power", "groups"])
    x1, y1, x2, y2 = TECH
    o.add("power", S.zone(x1, y1, x2, y2, "#343A40", None, fill_op=0.06))
    o.add("power", S.panel(3, 832, 11, 48))
    o.add("power", S.txt(36, 846, "щит", fs=7, weight=700, font=S.SANS))
    if mode != "light":
        o.add("groups", S.badge(36, 872, "8"))
    for p in (EL if mode != "light" else []):
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
    for s in (SW if mode != "power" else []):
        o.add("light", S.switch(s["x"], s["y"], s["d"], s["keys"]))
        if s["h"] != 90:
            lx, ly = S.label_pos(s["x"], s["y"], s["d"], 18)
            o.add("light", S.txt(lx, ly, s["h"], fs=6.2))
        nx, ny = S.N[s["d"]]
        o.add("groups", S.badge(s["x"] + nx * 5 - 9 * (1 if s["d"] in "ud" else 0), s["y"] + ny * 5 - 9 * (1 if s["d"] in "lr" else 0), s["g"]))
    for l in (LT if mode != "power" else []):
        if l["kind"] == "strip":
            o.add("light", S.strip(l["pts"]))
        else:
            o.add("light", S.lamp(l["x"], l["y"], l["kind"], l["d"]))
    # связи «выключатель — светильники»
    by_c = {}
    for l in (LT if mode != "power" else []):
        pt = l["pts"][0] if l["kind"] == "strip" else (l["x"], l["y"])
        by_c.setdefault(l["c"], []).append(pt)
    for s in (SW if mode != "power" else []):
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
    tot = [0, 0, 0, 0]
    for r in ROOM_ORDER:
        socks = sum(len(p["kinds"]) for p in EL if p["room"] == r and p["t"] in ("sock", "floor"))
        outs = sum(1 for p in EL if p["room"] == r and p["t"] == "appl")
        lamps = sum(1 for l in LT if l["room"] == r and l["kind"] not in ("motion", "fan"))
        sws = sum(1 for s in SW if s["room"] == r)
        vals = [socks, outs, lamps, sws]
        tot = [a + b for a, b in zip(tot, vals)]
        rows.append([RN[r]] + [num(v or "—") for v in vals])
    rows.append(["<b>Всего</b>"] + [f"<b>{num(v)}</b>" for v in tot])
    return rows, tot


def el_legend():
    def ic(inner, vb=(-10, -10, 20, 20)):
        return S.icon(inner, vb)
    return [
        (ic(S.socket(0, -4, "d", ["std"])[0]), "Розетка, рядом высота в см"),
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


def merged_group_blocks():
    return [
        ("h2", "13 рабочих линий"),
        ("table", "Объединённые линии", ["Группа", "Что объединено", "Условие"], [
            ["QF1", "Свет спальни, двух детских и кухни-гостиной", "C10; проходной свет QF3 под другим УЗО"],
            ["QF4", "Розетки спальни, прихожей, коридора и кладовой", "Общий C16"],
            ["QF5", "Розетки двух детских", "Общий C16"],
            ["QF8", "Холодильник, гостиная и техника связи в шкафу", "Общий C16, вне разгрузки; групповая неисправность отключит и холодильник"],
            ["QF15", "Розетки двух санузлов, полотенцесушители и тёплые полы", "C16; ≈ 3,1 кВт с одним феном; отключается целиком"],
            ["QF20", "Кондиционеры спальни и гостиной", "C16; ≈ 2 кВт суммарно предварительно, подтвердить по моделям"],
        ], "Духовка, варочная, ПММ, стиральная и сушильная машины сохраняют отдельные автоматы. QF19/QF21 больше нет: их точки относятся к QF15/QF20. Номера остальных линий сохранены."),
    ]


def group_feeds(g):
    items = []
    for point in EL:
        if point["g"] != g:
            continue
        what = kinds_text(point["kinds"]) if point["t"] in ("sock", "floor") else APPL[point["code"]]
        items.append(f"{RN[point['room']]}: {what}, {point['where']}")
    items += [f"{RN[r]}: {what}, {where}" for r, what, where, _, gg in TECH_EL if gg == g]
    return items


def dev_info(key):
    code, rating, short, mods, kind, title, details = DEV[key]
    details = list(details)
    if key.isdigit():
        g = int(key)
        bank = BANK_OF[g]
        _, _, neutral, comb = BANKS[bank]
        phase = f"{comb} → QF{g} → " + (f"X{g}.L → ветви W{g}.*" if g in BRANCHES else f"W{g}.L")
        details.append(("Подключение", phase + f"; N от {neutral}" + (f" через QF{g}.N" if g == 3 else "") + f" → W{g}.N; PE от XPE → W{g}.PE."))
        feeds = group_feeds(g)
        if feeds:
            details.append(("Что питает", "<ul>" + "".join(f"<li>{x}</li>" for x in feeds) + "</ul>"))
    body = "<dl>" + "".join(f"<dt>{a}</dt><dd>{b}</dd>" for a,b in details) + "</dl>"
    prefix = "QF"+key if key.isdigit() else code
    return key, ((prefix+" — ") if prefix else "")+title, f"{rating} · {mods} мод.", body


def panel_info():
    return [dev_info(k) for row in PANEL_ROWS for k in row]


def panel_svg():
    return overview_svg(PANEL_ROWS, DEV)


# ======================================================================== ВОДОПРОВОД И КАНАЛИЗАЦИЯ
# Независимые вводы: по одному узлу учёта ХВС/ГВС в каждом санузле.
WATER_NODES = {"У1": "Санузел у спален", "У2": "Санузел у входа и кухня"}
# Трубы: (вид c/h, куда, комната, путь, узел). Между узлами соединений нет.
PIPES = [
    ("c", "С/у 1: унитаз", "su-1", [(32, 690), (62, 690), (62, 693)], "У1"),
    ("h", "С/у 1: раковина", "su-1", [(32, 676), (36, 676), (36, 600), (4, 600)], "У1"),
    ("c", "С/у 1: раковина", "su-1", [(32, 670), (42, 670), (42, 584), (4, 584)], "У1"),
    ("h", "С/у 1: ванна", "su-1", [(32, 664), (48, 664), (48, 514), (4, 514)], "У1"),
    ("c", "С/у 1: ванна", "su-1", [(32, 654), (54, 654), (54, 498), (4, 498)], "У1"),
    ("c", "Стиральная машина", "su-2", [(67, 1142), (85, 1142), (85, 1132)], "У2"),
    ("h", "С/у 2: раковина", "su-2", [(67, 1196), (262, 1196), (262, 1155), (280, 1155)], "У2"),
    ("c", "С/у 2: раковина", "su-2", [(67, 1202), (270, 1202), (270, 1171), (280, 1171)], "У2"),
    ("h", "Кухня: мойка", K, [(67, 1210), (333, 1210), (333, 1339), (402, 1339), (402, 1356)], "У2"),
    ("c", "Кухня: мойка и посудомойка", K, [(67, 1216), (327, 1216), (327, 1345), (386, 1345), (386, 1356)], "У2"),
    ("c", "С/у 2: унитаз", "su-2", [(67, 1226), (237, 1226), (237, 1307)], "У2"),
    ("h", "С/у 2: душ", "su-2", [(67, 1232), (108, 1232), (108, 1307)], "У2"),
    ("c", "С/у 2: душ", "su-2", [(67, 1240), (96, 1240), (96, 1307)], "У2"),
]

# Коллекторы вынесены из узких шахт в обслуживаемые модули.
# Координаты — проектный габаритный резерв до обмера, не сертификация размещения.
WATER_CABINETS=[('У1',123,652,183,697,100,180),('У2',213,1286,273,1311,140,220)]
WATER_MAINS=[
 ('c','У1',[(17,658),(123,658),(123,660),(150,660)],3.0),
 ('h','У1',[(17,684),(123,684),(123,680),(150,680)],3.0),
 ('c','У2',[(25.5,1146),(48,1146),(48,1224),(240,1224),(240,1290)],5.0),
 ('h','У2',[(25.5,1166),(48,1166),(48,1230),(246,1230),(246,1300)],5.0),
]
_u2_paths=[
 [(240,1290),(240,1212),(85,1212),(85,1132)],
 [(246,1300),(262,1300),(262,1155),(280,1155)],
 [(240,1290),(270,1290),(270,1171),(280,1171)],
 [(246,1300),(333,1300),(333,1339),(402,1339),(402,1356)],
 [(240,1290),(327,1290),(327,1345),(386,1345),(386,1356)],
 [(240,1290),(237,1290),(237,1307)],
 [(246,1300),(108,1300),(108,1307)],
 [(240,1290),(96,1290),(96,1307)],
]
for _i,(_kind,_dest,_room,_pts,_node) in enumerate(PIPES):
    if _node=='У1':
        _start=(150,660 if _kind=='c' else 680)
        _pts=[_start,(_start[0],_pts[1][1])]+_pts[1:]
    else:
        _pts=_u2_paths[_i-5]
    PIPES[_i]=(_kind,_dest,_room,_pts,_node)

# Выводы: (комната, прибор, x, y, d, виды, высота воды, канализация, высота канализации, стояк, точка выпуска)
FIXTURES = [
    (K, "Мойка, посудомойка через кран-тройник под мойкой", 394, 1360, "u", ["c", "h"], "55", "Ø50", "45", "К3", (394, 1360, "u")),
    ("su-2", "Стиральная машина", 85, 1128, "d", ["c"], "70, в доступной боковой зоне", "Ø40, сифон в стене", "60", "К2", (108, 1128, "d")),
    ("su-2", "Раковина", 284, 1163, "l", ["h", "c"], "55", "Ø50", "50", "К3", (284, 1163, "l")),
    ("su-2", "Унитаз подвесной с инсталляцией", 237, 1311, "u", ["c"], "100, внутри рамы", "Ø110", "23, по раме", "К3", None),
    ("su-2", "Душ: наружный термостат; уровень пола после обмера", 102, 1311, "u", ["c", "h"], "105, лейка сверху 210", "линейный трап у стены шахты, Ø50", "в полу", "К2", None),
    ("su-1", "Ванна 180×80", 0, 506, "r", ["c", "h"], "80, на 20 выше борта", "Ø50", "у пола, ванна на ножках", "К1", None),
    ("su-1", "Раковина", 0, 592, "r", ["c", "h"], "55", "Ø50", "50", "К1", (0, 592, "r")),
    ("su-1", "Унитаз подвесной с инсталляцией", 62, 697, "u", ["c"], "100, внутри рамы", "Ø110", "23, по раме", "К1", None),
]

RISERS_W = [("В1.1", 6, 658, C["cold"], "ХВС с/у 1"), ("Т3.1", 6, 684, C["hot"], "ГВС с/у 1"),
            ("В1.2", 14, 1146, C["cold"], "ХВС с/у 2"), ("Т3.2", 14, 1166, C["hot"], "ГВС с/у 2")]
MOTOR_VALVES = [(17, 658), (17, 684), (25.5, 1146), (25.5, 1166)]
RISERS_K = [("К1", 16, 672), ("К2", 29, 1295), ("К3", 249, 1339)]

# канализация: (откуда, Ø, уклон %, путь)
SEWER = [
    ("С/у 1: ванна", 50, 3, [(30, 530), (22, 530), (22, 672), (16, 672)]),
    ("С/у 1: раковина", 50, 3, [(4.5, 592), (22, 592), (22, 672), (16, 672)]),
    ("С/у 1: унитаз", 110, 2, [(78, 678), (16, 678), (16, 672)]),
    ("С/у 2: унитаз", 110, 2, [(250, 1298), (250, 1339), (249, 1339)]),
    ("С/у 2: стиральная машина", 40, 3, [(108, 1132), (73, 1132), (73, 1290), (29, 1290), (29, 1295)]),
    ("С/у 2: душ", 50, 3, [(77, 1302), (29, 1302), (29, 1295)]),
    ("С/у 2: раковина", 50, 3, [(279.5, 1163), (279.5, 1330), (249, 1330), (249, 1339)]),
    ("Кухня: мойка", 50, 3, [(394, 1355.5), (394, 1351), (249, 1351), (249, 1339)]),
]
DRAIN_PTS = [(30, 530), (78, 678), (250, 1298), (77, 1302)]

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
    # Счётчики/приводы у своих стояков; сервисные модули показаны отдельно.
    o.add('supply',S.zone(11,651,32,697,'#1971c2',None,fill_op=.12))
    o.add('supply',S.txt(55,643,'У1: узел учёта',fs=6.2,font=S.SANS))
    o.add('supply',S.zone(24,1134,58,1188,'#1971c2',None,fill_op=.12))
    o.add('supply',S.txt(44,1195,'У2: учёт',fs=6.2,font=S.SANS))
    for node,x1,y1,x2,y2,h1,h2 in WATER_CABINETS:
        o.add('supply',S.zone(x1,y1,x2,y2,'#495057',None,fill_op=.08,dash='4 2'))
        o.add('supply',S.txt((x1+x2)/2,y1-8,node+' сервис: +'+str(h1)+'…'+str(h2),fs=6.2,font=S.SANS))
    for kind,node,pts,length in WATER_MAINS:
        o.add('supply',S.path(pts,C['cold'] if kind=='c' else C['hot'],2.2,dash='5 2'))
    for code, x, y, col, _ in RISERS_W:
        o.add("supply", S.riser(x, y, code, col))
    for (x,y),mark,kind in zip(MOTOR_VALVES,('V1C','V1H','V2C','V2H'),('c','h','c','h')):
        o.add('supply',S.valve(x,y,color=C['cold'] if kind=='c' else C['hot'],motor=True))
        o.add('supply',S.txt(x+16,y+4,mark,fs=5.8,font=S.SANS))
    # Подробный порядок арматуры — на отдельных схемах У1 и У2, после узлов учёта.
    for kind, _, _, pts, node in PIPES:
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
    o.add("sewer", S.txt(266, 1322, "Ø110", fs=6.4, fill=C["sewer"]))
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
        (ic(S.path([(-9, 0), (9, 0)], C["cold"], 1.5) + S.path([(-9, 5), (9, 5)], C["hot"], 1.5), (-10, -8, 20, 18)), "Лучи16 мм; магистрали20 мм пунктиром"),
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
    return S.path_len(pts) / 100 + 2.5   # предварительный запас вертикалей и концов от новых сервисных модулей


def collector_rows():
    rows = []
    counts = {node: {"c": 0, "h": 0} for node in WATER_NODES}
    for kind, dest, room, pts, node in PIPES:
        counts[node][kind] += 1
        no = f"{node}.{'ХВС' if kind == 'c' else 'ГВС'}-{counts[node][kind]}"
        rows.append([node, no, dest, num(fmt(pipe_len(pts)))])
    return rows, sum(c["c"] for c in counts.values()), sum(c["h"] for c in counts.values())


def sewer_rows(room_filter=None):
    rows = []
    for name, dia, slope, pts in SEWER:
        L = S.path_len(pts) / 100
        drop = L * slope
        rows.append([name, f"Ø{dia}", num(fmt(L)), num(f"{slope} %"), num(f"{max(1, round(drop))} см")])
    return rows


def collector_svg(node):
    """Один независимый узел: учёт застройщика → квартирная защита → коллекторы."""
    W = 760
    outs = {kind: [dest for k, dest, _, _, n in PIPES if k == kind and n == node] for kind in ("c", "h")}
    H = 140 + sum(160 + 27 * len(outs[k]) for k in ("c", "h"))
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="{node}: два счётчика и коллекторы">',
           f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>',
           S.txt(W / 2, 24, f"{node} · {WATER_NODES[node]}", fs=17, font=S.SANS, weight=700, halo=False)]

    def box(x, y, w, title, sub, col):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="58" rx="5" fill="#F7F9FA" stroke="{col}" stroke-width="1.5"/>'
                + S.txt(x + w / 2, y + 20, title, fs=12, font=S.SANS, weight=700, halo=False)
                + S.txt(x + w / 2, y + 39, sub, fs=11, font=S.SANS, weight=500, halo=False))

    y = 68
    for kind, title, col, riser in (("c", "Холодная вода", C["cold"], "В1"), ("h", "Горячая вода", C["hot"], "Т3")):
        out.append(S.txt(25, y, title, fs=14, font=S.SANS, weight=700, fill=col, anchor="start", halo=False))
        cy = y + 47
        out.append(S.txt(42, cy, f"{riser}.{node[-1]}", fs=12, font=S.SANS, weight=700, fill=col, halo=False))
        for a, b in ((78, 110), (285, 320), (490, 525)):
            out.append(S.path([(a, cy), (b, cy)], col, sw=2))
            out.append(f'<polygon points="{b-6},{cy-4} {b},{cy} {b-6},{cy+4}" fill="{col}"/>')
        out.append(box(110, y + 18, 175, "Счётчик " + ("ХВС" if kind == "c" else "ГВС"), "узел учёта застройщика", col))
        out.append(box(320, y + 18, 170, "Кран с приводом", "после учёта", col))
        out.append(box(525, y + 18, 210, "Фильтр / редуктор", "состав и давление уточнить", col))
        bar = y + 111
        out.append(S.path([(735, cy), (745, cy), (745, bar), (80, bar)], col, sw=2))
        out.append(S.txt(370, bar - 13, f"Коллектор {'ХВС' if kind == 'c' else 'ГВС'}: {len(outs[kind])} выходов", fs=12, font=S.SANS, weight=700, fill=col, halo=False))
        for i, dest in enumerate(outs[kind], 1):
            yy = bar + 27 * i
            out.append(S.path([(80, yy - 27), (80, yy), (124, yy)], col, sw=2))
            out.append(S.valve(110, yy, color=col))
            out.append(S.txt(138, yy, f"{node}.{'ХВС' if kind == 'c' else 'ГВС'}-{i} · {dest}", fs=12, font=S.SANS, weight=500, anchor="start", halo=False))
        y += 160 + 27 * len(outs[kind])
    out.append(S.txt(380, y + 8, "До счётчиков нет потребительских отводов и байпаса. Пломбы сохраняются.", fs=12, font=S.SANS, weight=700, halo=False))
    out.append(S.txt(380, y + 33, "Предсчётчиковая арматура и обратные клапаны — по фактическому узлу и требованиям УК.", fs=11, font=S.SANS, weight=500, halo=False))
    out.append(S.txt(380, y + 58, "Трубы 16 мм в гофре, без соединений в полу. У1 и У2 между собой не соединять.", fs=11, font=S.SANS, weight=500, halo=False))
    out.append("</svg>")
    return "".join(out)


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
    [(17, 658), (45, 658), (45, 640), (170, 640)],
    [(17, 684), (45, 684), (45, 658)],
    [(25.5, 1146), (48, 1146), (48, 1124), (150, 1124)],
    [(25.5, 1166), (48, 1166), (48, 1146)],
    [(394, 1325), (340, 1325), (340, 1222), (150, 1222), (150, 1196)],
    [(464, 1342), (464, 1325), (394, 1325)],
]


def lan_overlay():
    o = S.Overlay(["cables", "lan", "leak", "other"])
    x1, y1, x2, y2 = TECH
    o.add("lan", S.zone(x1, y1, x2, y2, C["lan"], None, fill_op=0.12))
    o.add("lan", S.txt(30, 846, "сеть", fs=7, font=S.SANS, weight=700, fill=C["lan"]))
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
    for x, y in MOTOR_VALVES:
        o.add("leak", S.valve(x, y, motor=True))
    o.add("leak", S.txt(92, 1124 - 7, "У2: 2 крана с приводом", fs=6, font=S.SANS, weight=700, fill=C["leak"]))
    o.add("leak", S.txt(75, 633, "У1: 2 крана с приводом", fs=6, font=S.SANS, weight=700, fill=C["leak"]))
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
    """Вид спереди на техническую секцию шкафа-купе: от пола до потолка, с вводами кабелей."""
    H = round(PLAN_CLEAR_HEIGHT*100)  # пример из модели высоты; нужен фактический обмер
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-112 -30 412 336" role="img" aria-label="Техническая секция шкафа-купе">',
           '<rect x="-112" y="-30" width="412" height="336" fill="#FFFFFF"/>']
    Y = lambda h: H - h   # noqa: E731  высота от пола → y
    PW, LV = "#495057", C["lan"]

    def item(x, h0, w, hh, title, col, fill, label_y=None, lines=(), fs=None):
        s = f'<rect x="{x}" y="{Y(h0 + hh)}" width="{w}" height="{hh}" rx="2" fill="{fill}" stroke="{col}" stroke-width="1.2"/>'
        s += S.txt(x + w / 2, Y(h0 + hh / 2), title, fs=fs or (6.2 if w < 30 else 7), font=S.SANS, weight=700, fill=col, halo=False)
        if lines:
            ly = label_y if label_y is not None else Y(h0 + hh / 2)
            s += f'<line x1="{x + w}" y1="{Y(h0 + hh / 2)}" x2="{92}" y2="{ly}" stroke="#ADB5BD" stroke-width="0.7"/>'
            s += note(96, ly, lines)
        return s

    def note(x, y, lines, anchor="start"):
        s = ""
        for i, ln in enumerate(lines):
            s += S.txt(x, y + i * 9 - (len(lines) - 1) * 4.5, ln, fs=7 if i == 0 else 6.4, font=S.SANS, weight=700 if i == 0 else 500,
                       anchor=anchor, fill="#1F2A30" if i == 0 else "#495057", halo=False)
        return s

    def arrow_up(x, h1, h2, col, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        return (f'<line x1="{x}" y1="{Y(h1)}" x2="{x}" y2="{Y(h2) + 5}" stroke="{col}" stroke-width="2"{d}/>'
                f'<polygon points="{x - 3},{Y(h2) + 6} {x + 3},{Y(h2) + 6} {x},{Y(h2)}" fill="{col}"/>')

    # секция, антресоль, пол и потолок
    out.append(f'<rect x="0" y="{Y(H)}" width="60" height="{H}" fill="#FBF8F2" stroke="#495057" stroke-width="1.6"/>')
    out.append(f'<rect x="0" y="{Y(H)}" width="60" height="{H - 227}" fill="#EBD3B1" stroke="#A87A42" stroke-width="1"/>')
    out.append(f'<rect x="0" y="{Y(227)}" width="60" height="2" fill="#A87A42"/>')
    out.append(S.txt(34, Y(249), "антресоль", fs=6.4, font=S.SANS, halo=False, fill="#8A6234"))
    out.append(f'<line x1="-34" y1="{Y(H)}" x2="76" y2="{Y(H)}" stroke="#1F2A30" stroke-width="2.4"/>')
    out.append(S.txt(78, Y(H) - 5, "потолок", fs=6.4, font=S.SANS, anchor="start", halo=False, fill="#495057"))
    out.append(f'<line x1="-34" y1="{Y(0)}" x2="76" y2="{Y(0)}" stroke="#1F2A30" stroke-width="2.4"/>')
    out.append(f'<rect x="-34" y="{Y(0)}" width="110" height="8" fill="#DEE2E6"/>')
    out.append(S.txt(30, Y(0) + 5, "сухой пол", fs=5, font=S.SANS, halo=False, fill="#495057"))
    # силовой короб от пола до потолка, слева
    out.append(f'<rect x="1" y="{Y(H)}" width="6" height="{H}" fill="#E9ECEF" stroke="{PW}" stroke-width="1"/>')
    out.append(S.txt(4, Y(100), "короб 100×60: силовые кабели", fs=5, font=S.SANS, weight=700, fill=PW, halo=False, rot=-90))
    out.append(arrow_up(4, -8, 0, PW))
    out.append(arrow_up(4, H - 2, H + 12, PW))
    # щит и ввод питания через заднюю стену
    out.append(item(9, 154, 44, 66, "ЩК", "#343A40", "#E9ECEF", Y(176), ["Щит квартиры", "54 модуля; корпус уточнить"]))
    out.append(item(9, 135, 16, 6, "SB0 / SB1", PW, "#F1F3F5", Y(157), ["Кнопочный пост под щитом", "Стоп / ручной возврат разгрузки"], fs=3.5))
    for hh in (159, 215):
        out.append(f'<line x1="7" y1="{Y(hh)}" x2="9" y2="{Y(hh)}" stroke="{PW}" stroke-width="3"/>')
    out.append(f'<circle cx="31" cy="{Y(192)}" r="3.4" fill="#FFFFFF" stroke="#C92A2A" stroke-width="1.3"/><circle cx="31" cy="{Y(192)}" r="1.1" fill="#C92A2A"/>')
    # монтажная панель с DIN-рейками; слаботочные кабели идут за ней
    out.append(f'<rect x="9" y="{Y(125)}" width="49" height="{125 - 64}" rx="1.5" fill="#F3E3C8" stroke="#A87A42" stroke-width="1.1"/>')
    for hr in (113, 122):
        out.append(f'<rect x="11" y="{Y(hr + 1.75)}" width="45" height="3.5" fill="#ADB5BD" stroke="#868E96" stroke-width="0.5"/>')
    out.append(f'<path d="M55,{Y(-8)} V{Y(112)}" stroke="{LV}" stroke-width="2" stroke-dasharray="4 2.5" fill="none"/>')
    out.append(f'<path d="M55,{Y(112)} H50" stroke="{LV}" stroke-width="2" stroke-dasharray="4 2.5" fill="none"/>')
    out.append(arrow_up(55, -8, 0, LV))
    for cx in (44, 50):
        out.append(f'<circle cx="{cx}" cy="{Y(126)}" r="2.6" fill="#FFFFFF" stroke="{LV}" stroke-width="1.2"/>')
    out.append(item(12, 112, 12, 12, "", C["leak"], "#E3FAFC", Y(128), ["Монтажная панель, фанера 18 мм, на брусках 4 см,", "две DIN-рейки: контроллер протечек,", "блоки питания; слаботочные кабели — за панелью"]))
    out.append(item(26, 112, 8, 12, "", "#7048E8", "#F3F0FF"))
    out.append(item(9.5, 103, 48, 9, "патч-панель", LV, "#E6FCF5", Y(106), ["Патч-панель 1U на кронштейне", "16–24 порта, кабели заходят снизу"]))
    out.append(item(10, 86, 28, 10, "коммутатор", LV, "#E6FCF5", Y(89), ["Коммутатор с PoE и роутер", "на шурупах через проушины"], fs=4.3))
    out.append(item(40, 86, 16, 10, "роутер", LV, "#E6FCF5", fs=4.6))
    out.append(item(10, 68, 13, 12, "ONT", "#495057", "#F1F3F5", Y(72), ["Терминал провайдера", "и удлинитель от QF8"]))
    out.append(item(26, 70, 30, 6, "удлинитель", PW, "#F1F3F5", fs=4.8))
    out.append(f'<rect x="8" y="{Y(46)}" width="51" height="2" fill="#A87A42"/>')
    out.append(item(12, 48, 26, 14, "сервер", "#1F2A30", "#F1F3F5", Y(53), ["Домашний сервер на полке", "мини-ПК или NAS на 2 диска"]))
    # подписи вводов
    out.append(note(-28, Y(H) - 14, ["К потолку: свет,", "кондиционеры — 3 группы"], "end"))
    out.append(f'<line x1="-26" y1="{Y(H) - 14}" x2="3" y2="{Y(H + 6)}" stroke="#ADB5BD" stroke-width="0.7"/>')
    out.append(note(96, Y(236), ["Через заднюю стену из общего коридора:", "кабель питания — прямо в щит (красный),", "2 трубы Ø25 для оптики — за панель (зелёные)"]))
    out.append(f'<line x1="34" y1="{Y(192)}" x2="92" y2="{Y(236)}" stroke="#ADB5BD" stroke-width="0.7"/>')
    out.append(f'<line x1="52" y1="{Y(126)}" x2="92" y2="{Y(236) + 9}" stroke="#ADB5BD" stroke-width="0.7"/>')
    out.append(note(-28, Y(-14), ["Из пола: силовые", "силовые трассы, в короб"], "end"))
    out.append(f'<line x1="-26" y1="{Y(-14)}" x2="3" y2="{Y(-6)}" stroke="#ADB5BD" stroke-width="0.7"/>')
    out.append(note(66, Y(-14), ["Из пола: 12 Cat6, провода датчиков", "протечки и кранов — в гофре, за панель"]))
    # вентиляция
    for x in (20, 40):
        out.append(f'<path d="M{x},{Y(-2)} V{Y(6)}" stroke="#4DABF7" stroke-width="1.4"/><polygon points="{x - 3},{Y(4)} {x + 3},{Y(4)} {x},{Y(9)}" fill="#4DABF7"/>')
        out.append(f'<path d="M{x},{Y(223)} V{Y(231)}" stroke="#FA5252" stroke-width="1.4"/><polygon points="{x - 3},{Y(228)} {x + 3},{Y(228)} {x},{Y(233)}" fill="#FA5252"/>')
    # высоты
    out.append(f'<line x1="-14" y1="{Y(0)}" x2="-14" y2="{Y(H)}" stroke="#495057" stroke-width="0.8"/>')
    for h in (0, 46, 64, 125, 220, 227, H):
        out.append(f'<line x1="-18" y1="{Y(h)}" x2="-10" y2="{Y(h)}" stroke="#495057" stroke-width="0.8"/>' + S.txt(-20, Y(h) + (4 if h == 220 else (-3 if h == 227 else 0)), h, fs=5.6, anchor="end", halo=False))
    out.append(S.txt(30, Y(H) - 22, "ширина секции 60 см", fs=6.2, halo=False))
    out.append("</svg>")
    return "".join(out)


CABLE_ROUTES = [
    ("Питание квартиры от этажного щита", "из общего коридора через заднюю стену", "прямо в щит сзади; если этажный щит далеко — по потолку в короб", "1 кабель"),
    ("Розетки, техника и полы — 10 групп", "по согласованным трассам у плиты; конструкция защиты по проекту", "вверх по силовому коробу в щит снизу", "10 групп; ветвей может быть больше. Кабели 3×2,5 и 3×6"),
    ("Свет и кондиционеры, 3 группы", "к потолку", "из щита сверху по силовому коробу через антресоль, дальше над натяжным потолком", "две группы света 3×1,5; одна группа кондиционеров с двумя ветвями 3×2,5"),
    ("Витая пара Cat6", "по согласованным трассам у плиты; конструкция защиты по проекту", "за монтажной панелью вверх, к патч-панели снизу; запас петлёй 1 м", "12 кабелей"),
    ("Датчики протечки и краны с приводом", "по согласованным трассам у плиты; конструкция защиты по проекту", "за панелью к контроллеру на DIN-рейке", "6 датчиков + 4 привода; 10 кабелей"),
    ("Оптика провайдера", "из общего коридора", "через заднюю стену в двух трубах Ø25 за панель, к терминалу", "1 + 1 запасная"),
]


CABINET_ITEMS = [
    ("Кнопочный пост SB0 / SB1", "на 135–141 см под щитом, выше слаботочной панели; кнопки «Стоп» NC и «Возврат» NO. Управление от QFC, кабель в силовом коробе"),
    ("Монтажная панель: фанера 18 мм 49×61 см на брусках 4 см, две DIN-рейки", "на стене секции на 64–125 см; на ней сетевое оборудование, за ней слаботочные кабели. Проверить габариты с корпусом щита"),
    ("Силовой короб 100×60 от пола до потолка", "слева в секции: кабели из пола в щит и из щита к свету на потолке"),
    ("Автономный пожарный датчик", "на стенке секции или под антресолью"),
    ("Патч-панель Cat6 1U на 16–24 порта на настенном кронштейне", "на 103–112 см: 12 кабелей сейчас, остальные порты в запасе"),
    ("Коммутатор на 16 портов 1 Гбит с PoE для точек доступа", "на панели на шурупах через проушины или на DIN-рейке; можно без PoE и два PoE-инжектора на DIN"),
    ("Роутер", "на панели рядом с коммутатором; Wi-Fi в нём не нужен: раздают точки доступа"),
    ("Оптический терминал провайдера", "ставит провайдер"),
    ("Удлинитель на 4–6 розеток", "на панели, включён в обычную розетку QF8"),
    ("Домашний сервер: NAS на 2 диска", "на полке 46 см; питание QF8"),
    ("Две точки доступа Wi-Fi 6 на потолке", "коридор и кухня-гостиная, одна сеть по всей квартире"),
    ("Контроллер защиты от протечек", "6 датчиков и 4 крана с приводом, от обычной линии QF8; контроллер с 4 выходами или совместимым расширением"),
]


# ======================================================================== СБОРКА РАЗДЕЛОВ
def blocks_tables(title, head, rows, note=None):
    return ("table", title, head, rows, note)


def build(n):
    if n != 1:
        return {}
    from water_docs import build as water
    from low_voltage_docs import build as lan
    from renovation_docs import build as renovation
    return {"elektrika": build_electrical(globals()), "santehnika": water(globals()),
            "slabotochka": lan(globals()), "remont": renovation(globals())}
