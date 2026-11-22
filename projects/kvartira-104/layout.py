"""Эскизы квартиры 104,5 м², три семейные планировки.

Сантиметры, x вправо, y вниз. Привязка к приложенному plan.jpg:
(x, y) = ((px - 15) * 1.28, (py - 45) * 1.28).
Масштаб восстановлен по площадям, не является обмером. Геометрия округлена.
Тонкие исходные перегородки не сохраняются; пилоны, фасад и шахты сохраняются.
Дверные проёмы 90 см в комнатах, 80 см в санузлах; новые стены 10–12 см.
"""
from plan_svg import CAT, Plan

from geometry104 import (PLAN_IMG_BOX, VIEWBOX, PYLONS, SHAFTS, RISERS, SINK_CENTER,
                         RIGHT_DEPTH, ROOM_POLYGONS, fmt, living_polygon, polygon_area, room_area)


def dim_h(p, x1, x2, y, wall_y, label=None):
    for x in (x1, x2):
        p.line(x, wall_y, x, y, '#8D979C', .7, 'dims')
    p.dim(x1, y, x2, y, label)


def dim_v(p, y1, y2, x, wall_x, label=None):
    for y in (y1, y2):
        p.line(wall_x, y, x, y, '#8D979C', .7, 'dims')
    p.dim(x, y1, x, y2, label)


def shell(p):
    W = p.wall
    # Фасад: четыре верхних окна, два боковых в гостиной и одно на кухне.
    for x1, x2 in [(-20, 82), (230, 333), (539, 641), (850, 954), (1160, 1196)]:
        W(x1, -36, x2, 0)
    for x1, x2 in [(82, 230), (333, 539), (641, 850), (954, 1160)]:
        p.window(x1, -20, x2, 0)
    for y1, y2 in [(-36, 75), (320, 422), (660, 716)]:
        W(-20, y1, 0, y2)
    for y1, y2 in [(75, 320), (422, 660)]:
        p.window(-20, y1, 0, y2, room='right')
    W(1171, -36, 1196, 680)
    W(-20, 691, 330, 736)
    W(216, 736, 251, 760)
    W(216, 1000, 251, 1071)
    p.window(231, 760, 251, 1000, room='right')
    W(216, 1046, 531, 1071)
    W(531, 1011, 608, 1071)
    W(608, 1046, 895, 1071)
    W(870, 850, 895, 1071)
    W(870, 850, 1370, 875)
    W(1171, 680, 1370, 705)
    W(1345, 705, 1370, 730)
    W(1345, 825, 1370, 875)
    p.door((1370, 730), (1370, 825), (1465, 730))
    p.text(1400, 860, 'Вход', fs=14)


def fixed_cores(p):
    # Рисуем бетон поверх примыкающих новых стен, а не перекрашиваем его в снос/новые стены.
    for rect in PYLONS:
        p.wall(*rect)
    for rect in SHAFTS:
        p.shaft(*rect)
    for i, (x, y) in enumerate(RISERS, 1):
        p.circle(x, y, 10, '#FFFFFF', '#147A82', 1, 'labels')
        p.text(x, y, f'С{i}', fs=8, fill='#147A82', halo=False)


def wet_rooms(p):
    N = p.new_wall
    p.floor([(610, 420), (860, 420), (860, 585), (823, 585), (823, 621), (610, 621)], 'wet')
    p.floor([(610, 860), (870, 860), (870, 1011), (835, 1011), (835, 1046), (610, 1046)], 'wet')
    # Верхний санузел: вход с юга, отводы остаются у своего стояка.
    N(600, 410, 870, 420)
    N(600, 420, 610, 631)
    N(860, 420, 870, 631)
    N(823, 585, 870, 595)
    N(823, 585, 833, 631)
    N(600, 621, 690, 631)
    N(770, 621, 870, 631)
    p.door((690, 621), (770, 621), (690, 541))
    p.bath(610, 420, 75, 170, 'Ванна 170×75', fs=10)
    p.basin(706, 420, 90, 50, 'top', 'Тумба 90', fs=10)
    p.wc(795, 507, 65, 42, 'right')
    p.room_label(750, 570, 'Ванная', '≈ 4,9 м²', fs=13)
    p.clear(685, 529, 795, 529, fs=10)

    N(598, 850, 675, 860)
    N(755, 850, 870, 860)
    N(598, 860, 610, 1046)
    N(835, 1011, 870, 1021)
    N(835, 1011, 845, 1046)
    p.door((755, 860), (675, 860), (755, 940))
    p.walkin(610, 946, 90, 100, (700, 955, 700, 1046), (615, 1041, 695, 1041),
             ['Душ', '90×100'], fs=10)
    p.washer(705, 981, 65, 65, None)
    p.text(737, 1013, ['СМ +', 'сушка'], fs=10, halo=False)
    p.wc(805, 937, 65, 42, 'right')
    p.basin(783, 860, 75, 48, 'top', 'Тумба 75', fs=10)
    p.room_label(744, 950, 'Душевая', '≈ 4,7 м²', fs=12)
    dim_h(p, 610, 860, 654, 631)
    dim_v(p, 420, 621, 889, 870)
    dim_h(p, 610, 870, 1105, 1046)
    dim_v(p, 860, 1046, 913, 870)


def partitions(p, v):
    n = p.new_wall
    n(318, 31, 330, 195)
    n(330, 183, 382, 195)
    n(370, 195, 382, 422)
    door_left = 138 if v == 3 else 242
    n(0, 410, door_left, 422)
    n(door_left+90, 410, 382, 422)
    hinge = door_left if v == 3 else door_left+90
    p.door((hinge, 410), (2*door_left+90-hinge, 410), (hinge, 320))

    if v == 3:
        # Двери двух комнат открываются из общей ниши справа от ванной.
        n(382, 410, 600, 420)
        n(860, 7, 870, 298)
        n(860, 388, 870, 410)
        p.door((860, 388), (860, 298), (770, 388))
        n(870, 275, 997, 285)
        n(987, 285, 997, 412)
        n(987, 502, 997, 615)
        p.door((997, 412), (997, 502), (1087, 412))
        n(997, 605, 1171, 615)
    else:
        n(382, 410, 458, 420)
        n(548, 410, 600, 420)
        p.door((458, 410), (548, 410), (458, 320))
        d = RIGHT_DEPTH[v]
        n(860, 7, 870, d+10)
        n(870, d, 889, d+10)
        n(979, d, 1171, d+10)
        p.door((889, d), (979, d), (889, d-90))
        if v == 2:
            # Гардеробная в глубине входной зоны. Полотно уходит вдоль южной стены.
            n(989, d+10, 1001, 680)
            n(1086, 670, 1171, 680)
            p.slide_door(1001, 676, 1086, 680, 1086, 676, 1171, 680)
    n(598, 631, 610, 660)
    n(598, 770, 610, 1011)


def study(p, x, y, w, h, cx, cy):
    p.desk(x, y, w, h, f'Стол {max(w,h)}×{min(w,h)}', fs=11)
    p.office_chair(cx, cy)


def left_child(p, v):
    if v == 1:
        p.bed(5, 310, 210, 100, 'left', '90×200', fs=12)
        p.shelf(5, 273, 35, 30, 'полка', fs=8)
        study(p, 40, 10, 145, 65, 110, 110)
        p.wardrobe(258, 35, 60, 145, 'left', 'Шкаф 145', fs=10)
        p.clear(145, 135, 145, 310)
        p.room_label(222, 235, 'Детская 1', fmt(room_area(v,'kid1')), fs=14)
    elif v == 2:
        p.bed(216, 40, 100, 210, 'top', '90×200', fs=12)
        p.shelf(183, 42, 28, 35, 'полка', fs=8)
        study(p, 12, 15, 145, 65, 80, 115)
        p.wardrobe(8, 350, 190, 60, 'top', 'Шкаф 190', fs=11)
        p.clear(182, 250, 182, 350)
        p.room_label(110, 263, 'Детская 1', fmt(room_area(v,'kid1')), fs=14)
    else:
        p.bed(267, 200, 100, 210, 'bottom', '90×200', fs=12)
        p.shelf(233, 372, 29, 33, 'полка', fs=8)
        study(p, 10, 82, 60, 140, 105, 150)
        p.wardrobe(258, 35, 60, 145, 'left', 'Шкаф 145', fs=10)
        p.clear(130, 210, 267, 210)
        p.room_label(158, 274, 'Детская 1', fmt(room_area(v,'kid1')), fs=14)


def right_child(p, v):
    if v == 1:
        # Изголовье и шкаф у внутренних стен. Стол получает свет справа.
        p.bed(1066, 115, 105, 210, 'bottom', '90×200', fs=12)
        p.shelf(1135, 330, 31, 30, 'полка', fs=8)
        study(p, 893, 14, 150, 65, 967, 114)
        p.wardrobe(998, 450, 173, 60, 'top', 'Шкаф 173', fs=11)
        p.clear(1080, 325, 1080, 450)
        p.room_label(973, 313, 'Детская 2', fmt(room_area(v,'kid2')), fs=14)
    elif v == 2:
        p.bed(875, 100, 105, 210, 'top', '90×200', fs=12)
        p.shelf(875, 62, 35, 30, 'полка', fs=8)
        study(p, 1010, 15, 145, 65, 1082, 116)
        p.wardrobe(995, 415, 176, 60, 'top', 'Шкаф 176', fs=11)
        p.clear(1007, 310, 1007, 415)
        p.room_label(1060, 273, 'Детская 2', fmt(room_area(v,'kid2')), fs=14)
    else:
        p.bed(1070, 42, 100, 210, 'bottom', '90×200', fs=12)
        p.shelf(1130, 260, 35, 30, 'полка', fs=8)
        study(p, 888, 12, 145, 65, 959, 114)
        p.wardrobe(1007, 545, 164, 60, 'top', 'Шкаф 164', fs=11)
        p.clear(997, 345, 1171, 345)
        p.room_label(1087, 475, 'Детская 2', fmt(room_area(v,'kid2')), fs=13)


def parents(p, v):
    if v == 2:
        p.bed(650, 80, 210, 190, 'right', '180×200', fs=13)
        for y in (37, 281):
            p.box(817, y, 40, 33, 'store', 'тумба', fs=8)
        p.wardrobe(576, 350, 284, 60, 'top', 'Шкаф-купе 284', fs=11)
        study(p, 352, 35, 140, 60, 420, 130)
        p.clear(685, 270, 685, 350)
        p.room_label(510, 235, 'Родители', fmt(room_area(v,'parents')), fs=15)
    else:
        bx = 581 if v == 1 else 520
        p.bed(bx, 200, 190, 210, 'bottom', '180×200', fs=13)
        for x in (bx-32, bx+195):
            p.box(x, 364, 29, 36, 'store', 'тумба', fs=8)
        if v == 1:
            p.wardrobe(382, 198, 60, 180, 'right', 'Шкаф 180', fs=10)
            p.wardrobe(800, 45, 60, 140, 'left', 'Шкаф 140', fs=11)
            study(p, 347, 12, 146, 60, 416, 106)
            p.clear(610, 31, 610, 200)
            p.clear(771, 255, 860, 255)
            p.room_label(505, 260, 'Родители', fmt(room_area(v,'parents')), fs=14)
        else:
            p.wardrobe(800, 35, 60, 213, 'left', 'Шкаф 213', fs=10)
            study(p, 365, 35, 195, 65, 464, 136)
            p.clear(710, 230, 800, 230)
            p.room_label(690, 140, 'Родители', fmt(room_area(v,'parents')), fs=14)


def kitchen(p):
    p.counter(251, 986, 280, 60)
    p.counter(531, 986, 67, 25)
    p.counter(538, 920, 60, 66)
    p.cooktop(300, 986, 60, 60, 'Варочная 60', fs=10, lpos=(330, 1084))
    p.sink(472, 1006, 60, 40, 'Мойка', fs=10)
    p.rect(412, 986, 60, 60, 'none', '#6F7980', 1, layer='detail', dash='4 3')
    p.text(442, 1019, 'ПММ 60', fs=10)
    p.circle(*SINK_CENTER, 5, '#147A82', layer='labels')
    p.text(505, 1082, '● мойка: исходная точка', fs=11, fill='#147A82')
    p.appliance(533, 790, 65, 70, ['Холод.', '65×70'], fs=10, k3='fridge')
    p.appliance(538, 860, 60, 60, ['Дух. +', 'СВЧ'], fs=10, k3='oven')
    p.text(568, 954, ['Рабочая', 'столешница'], rot=-90, fs=10)


def diagonal_chair(p, x, y, angle):
    # Стул 42×42, спинка наружу от центра круглого стола.
    fill, edge = CAT["seat"]
    transform = f' transform="rotate({angle} {x} {y})"'
    p.rect(x-21, y-21, 42, 42, fill, edge, 1.1, 8, extra=transform)
    p.rect(x-18, y+12, 36, 8, edge, "none", 0, 3, "detail", extra=transform)
    p.rec('diagonal_chair', cx=x, cy=y, angle=angle, size=42)


def common_room(p, v):
    kitchen(p)
    if v == 1:
        p.bench(251, 753, 45, 155, 'left', 'Скамья 155', fs=10)
        p.desk(300, 760, 75, 145, 'Стол 145×75', fs=11, k3='dining')
        for y in (795, 866):
            p.chair(405, y, 'left')
        p.clear(426, 832, 533, 832)
        p.sofa(12, 596, 265, 95, 'bottom', 'Диван 265', fs=12)
        p.box(35, 422, 151, 26, 'store', 'ТВ · консоль', fs=10)
        p.room_label(368, 569, 'Кухня-гостиная', fmt(polygon_area(living_polygon(v))), fs=14)
    elif v == 2:
        p.circle(357, 827, 50, '#F7DE98', '#B8902A')
        p.rec('roundtable', cx=357, cy=827, r=50)
        p.text(357, 827, 'Стол Ø100', fs=11)
        for dx, dy, angle in [(-51, -51, 135), (51, -51, -135),
                              (-51, 51, 45), (51, 51, -45)]:
            diagonal_chair(p, 357+dx, 827+dy, angle)
        p.clear(438, 796, 533, 796)
        p.sofa(12, 423, 225, 92, 'top', 'Диван 225', fs=11)
        p.box(12, 515, 88, 68, 'seat', 'Шезлонг', fs=10)
        p.box(40, 661, 155, 30, 'store', 'ТВ · консоль', fs=10)
        p.room_label(320, 580, 'Кухня-гостиная', fmt(polygon_area(living_polygon(v))), fs=14)
    else:
        p.bench(339, 423, 220, 45, 'top', 'Обеденная скамья', fs=10)
        p.desk(350, 470, 166, 75, 'Стол 166×75', fs=11, k3='dining')
        for x in (390, 476):
            p.chair(x, 573, 'up')
        p.sofa(8, 596, 225, 95, 'bottom', 'Диван 225', fs=11)
        p.box(14, 422, 110, 25, 'store', 'ТВ', fs=10)
        p.box(12, 521, 60, 60, 'seat', 'Пуф', fs=10)
        # Низкая рабочая поверхность в кухне, без посадки со стороны прохода.
        p.counter(251, 778, 132, 65)
        p.text(317, 811, ['Подготовка', '132×65'], fs=10)
        p.clear(383, 819, 533, 819)
        p.clear(449, 594, 449, 691)
        p.room_label(328, 652, 'Кухня-гостиная', fmt(polygon_area(living_polygon(v))), fs=14)


def hall(p, v):
    p.bench(1198, 811, 120, 39, 'bottom', 'Обувь · скамья', fs=10)
    if v == 1:
        p.wardrobe(875, 790, 295, 60, 'top', 'Одежда и хозяйственная секция 295', fs=11)
        p.wardrobe(1000, 520, 171, 60, 'bottom', 'Сезонный шкаф 171', fs=10)
        p.room_label(975, 691, 'Прихожая', 'семейные шкафы', fs=14)
    elif v == 2:
        p.wardrobe(1111, 485, 60, 180, 'left', 'Одежда 180', fs=10)
        p.wardrobe(875, 790, 200, 60, 'top', 'Повседневная одежда 200', fs=11)
        p.text(1054, 554, ['Гардеробная', '3,1 м²'], fs=11)
        p.clear(1001, 610, 1111, 610)
        p.room_label(961, 742, 'Прихожая', 'гардероб у входа', fs=13)
    else:
        p.wardrobe(997, 615, 174, 60, 'bottom', 'Бельё и чемоданы 174', fs=10)
        p.wardrobe(875, 790, 225, 60, 'top', 'Одежда 225', fs=10)
        p.clear(870, 530, 987, 530)
        p.text(928, 462, ['К спальне', 'и детской'], fs=10)
        p.room_label(963, 731, 'Прихожая', 'семейные шкафы', fs=13)
    p.clear(1250, 705, 1250, 811)
    p.dim(621, 660, 621, 770, '110', fs=11)


def dimensions(p, v):
    dim_h(p, 0, 1171, -112, 0)
    for a,b in [(0,318),(330,860),(870,1171)]:
        dim_h(p,a,b,-64,0)
    dim_v(p,0,410,-65,0)
    dim_v(p,422,691,-65,0)
    p.dim(318, 204, 370, 204, fs=10)
    dim_v(p,0,195,-105,0)
    dim_v(p,0,RIGHT_DEPTH[v],1212,1171)
    dim_v(p,736,1046,180,251)
    dim_h(p,251,531,1104,1046)
    dim_h(p,870,1345,907,850)
    # Ширина ниже уступа и чистая ширина дверных проёмов.
    y = 335 if v == 2 else 192
    p.dim(382, y, 860, y, fs=10)
    for item in p.items:
        if item['kind'] == 'door':
            (x1, y1), (x2, y2) = item['hinge'], item['closed']
            if abs(x1-x2) == 90:
                p.dim(min(x1, x2), y1+5, max(x1, x2), y2+5, fs=10)
            elif abs(y1-y2) == 90:
                x = x1+5 if x1 == 860 else x1-5
                p.dim(x, min(y1, y2), x, max(y1, y2), fs=10)
    if v == 3:
        p.dim(997, 526, 1171, 526, fs=10)
        dim_v(p,0,275,1260,1171)
    if v == 2:
        dim_h(p,1001,1171,699,680)
    p.dim(690, 613, 770, 613, '80', fs=10)
    p.dim(675, 840, 755, 840, '80', fs=10)
    p.text(670, 1143, 'Эскизные размеры в сантиметрах · потолок после стяжки 270 см', fs=14)


def build_plan(v):
    p = Plan()
    for pts in ROOM_POLYGONS[v].values():
        p.floor(pts)
    p.floor(living_polygon(v))
    d = RIGHT_DEPTH[v] + 10
    hall_top = ([(870, 285), (987, 285), (987, d)] if v == 3 else [(870, d)])
    p.floor([(610,631),(870,631)] + hall_top + [(1171,d),(1171,705),
            (1345,705),(1345,850),(610,850)], 'hall')
    shell(p)
    wet_rooms(p)
    partitions(p, v)
    fixed_cores(p)
    left_child(p, v)
    right_child(p, v)
    parents(p, v)
    common_room(p, v)
    hall(p, v)
    dimensions(p, v)
    return p


VARIANTS = {n: (lambda n=n: build_plan(n)) for n in RIGHT_DEPTH}


def build(v, overlay=None):
    p = build_plan(v)
    return p, p.render(VIEWBOX, overlay, f'План квартиры, вариант {v}', PLAN_IMG_BOX)
