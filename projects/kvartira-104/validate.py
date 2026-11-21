"""Проверка ключевых ограничений эскиза: python3 projects/kvartira-104/validate.py.

Не заменяет обмер и проверку проекта архитектором.
"""
import math
import sys
from bisect import bisect_right
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import layout
from geometry104 import ROOM_PROBES


def overlap(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def check_enclosures(p, variant):
    """Закрываем только заявленные двери. Любая иная щель должна провалить тест.

    Сетка строится по ВСЕМ граням стен: даже зазор 1 см не исчезает из-за
    округления или выбранного разрешения картинки. Мебель стены не заменяет.
    """
    barriers = []
    for i in p.items:
        if i['kind'] in ('wall', 'shaft', 'window', 'slide'):
            barriers.append((i['x1'], i['y1'], i['x2'], i['y2']))
        elif i['kind'] == 'door':
            (x, y), (x2, y2) = i['hinge'], i['closed']
            barriers.append((min(x, x2) - (12 if x == x2 else 0),
                             min(y, y2) - (12 if y == y2 else 0),
                             max(x, x2) + (12 if x == x2 else 0),
                             max(y, y2) + (12 if y == y2 else 0)))
    xs = sorted({-50, 1510} | {x for r in barriers for x in (r[0], r[2])})
    ys = sorted({-70, 1120} | {y for r in barriers for y in (r[1], r[3])})
    nx, ny = len(xs) - 1, len(ys) - 1
    xi, yi = {x: n for n, x in enumerate(xs)}, {y: n for n, y in enumerate(ys)}
    labels = [0] * (nx * ny)
    for x1, y1, x2, y2 in barriers:
        for y in range(yi[y1], yi[y2]):
            labels[y*nx + xi[x1]:y*nx + xi[x2]] = [-1] * (xi[x2] - xi[x1])
    component = 0
    for start in range(len(labels)):
        if labels[start]:
            continue
        component += 1
        queue = deque([start])
        labels[start] = component
        while queue:
            n = queue.popleft()
            x, y = n % nx, n // nx
            for other in ((n-1 if x else -1), (n+1 if x+1 < nx else -1),
                          (n-nx if y else -1), (n+nx if y+1 < ny else -1)):
                if other >= 0 and labels[other] == 0:
                    labels[other] = component
                    queue.append(other)

    def at(x, y):
        return labels[(bisect_right(ys, y) - 1)*nx + bisect_right(xs, x) - 1]

    outside, common = at(-40, -60), at(450, 720)
    assert common != outside and common > 0, 'Незамкнутый наружный контур'
    probes = dict(ROOM_PROBES[variant], su1=(730, 510), su2=(720, 930))
    if variant == 2:
        probes['гардеробная'] = (1050, 610)
    groups = {name: at(*point) for name, point in probes.items()}
    assert all(c > 0 and c not in (outside, common) for c in groups.values()), ('Дыра в стене', groups)
    assert len(set(groups.values())) == len(groups), ('Комнаты соединены незаявленным проёмом', groups)


def check_kitchen_backing(p):
    for i in p.items:
        if i['kind'] == 'appliance' and i.get('k3') in ('fridge', 'oven'):
            x, y, w, h = i['x'], i['y'], i['w'], i['h']
            assert 251 <= x < x+w <= 598 and 770 <= y < y+h <= 1011, 'Техника вне кухонной зоны'
            assert any(b['kind'] == 'wall' and abs(b['x1'] - (x+w)) < .01
                       and b['y1'] <= y and b['y2'] >= y+h for b in p.items), 'Техника без стены за спиной'


def check_wall_connections(p):
    walls = [i for i in p.items if i['kind'] == 'wall']
    for a in walls:
        if not a['new']:
            continue
        # Положительная длина примыкания: касания только уголком недостаточно.
        def connected(b):
            dx = min(a['x2'], b['x2']) - max(a['x1'], b['x1'])
            dy = min(a['y2'], b['y2']) - max(a['y1'], b['y1'])
            return dx >= 0 and dy >= 0 and (dx > 0 or dy > 0)
        assert any(b is not a and connected(b) for b in walls), ('Оторванная перегородка', a)


def furniture_bounds(item):
    kind = item['kind']
    if kind in ('box', 'bed', 'bench', 'wardrobe', 'sofa', 'shelf', 'washer',
                'wc', 'walkin', 'basin', 'bath', 'counter', 'appliance'):
        x, y = item['x'], item['y']
        return x, y, x+item['w'], y+item['h']
    if kind == 'diagonal_chair':
        r = item['size']/math.sqrt(2)  # проекция квадрата, повёрнутого на 45°
        return item['cx']-r, item['cy']-r, item['cx']+r, item['cy']+r
    if kind in ('office_chair', 'chair', 'roundtable'):
        r = item['size']/2 if kind == 'chair' else item['r']
        x, y = item['cx'], item['cy']
        return x-r, y-r, x+r, y+r


def check_use(p, v):
    # Проверяем реальные предметы, включая спинки стульев. Круглый стол и
    # круглое кресло для маршрута консервативно вписываем в квадрат.
    furniture = [(item, furniture_bounds(item)) for item in p.items if furniture_bounds(item)]
    solid = [(i['x1'], i['y1'], i['x2'], i['y2']) for i in p.items
             if i['kind'] in ('wall','window','shaft')]
    for j, (a, rect) in enumerate(furniture):
        assert not any(overlap(rect, w) for w in solid), (v, 'предмет в стене', a)
        for b, other in furniture[j+1:]:
            if a['kind'] == 'roundtable' or b['kind'] == 'roundtable':
                disk, box = (a, other) if a['kind'] == 'roundtable' else (b, rect)
                dx = max(box[0]-disk['cx'], 0, disk['cx']-box[2])
                dy = max(box[1]-disk['cy'], 0, disk['cy']-box[3])
                seat = b if disk is a else a
                if seat['kind'] == 'diagonal_chair':
                    # Каждое кресло обращено прямо к столу: расстояние до
                    # ближней стороны сиденья измеряется по этому радиусу.
                    distance = math.hypot(disk['cx']-seat['cx'], disk['cy']-seat['cy']) - seat['size']/2
                    assert distance >= disk['r'], (v, a, b)
                else:
                    assert dx*dx+dy*dy >= disk['r']**2, (v, a, b)
            else:
                assert not overlap(rect,other), (v, 'наложение мебели',a,b)
    doors = [i for i in p.items if i['kind']=='door']
    for door in doors:
        hx,hy = door['hinge']
        cx,cy = door['closed']
        ox,oy = door['opened']
        radius = abs(cx-hx)+abs(cy-hy)
        quadrant = min(hx,cx,ox),min(hy,cy,oy),max(hx,cx,ox),max(hy,cy,oy)
        for item,rect in furniture:
            dx = max(rect[0]-hx, 0, hx-rect[2])
            dy = max(rect[1]-hy, 0, hy-rect[3])
            assert not (overlap(rect,quadrant) and dx*dx+dy*dy < radius**2), (v, 'дверь задевает', item)
        solid.append((min(hx,ox)-1,min(hy,oy)-1,max(hx,ox)+1,max(hy,oy)+1))
    solid.extend(rect for _,rect in furniture)

    # За входной дверью начинаем с центра прихожей. Стены фасада
    # не допускают обхода снаружи. Шаг 5 см, свободный квадрат 80×80.
    # Для захода в с/у в проём 80 см отдельно проверяем квадрат 70×70.
    def accessible(width, destinations):
        half = width/2
        blocked=set()
        for x1,y1,x2,y2 in solid:
            for x in range(math.floor((x1-half)/5)+1, math.ceil((x2+half)/5)):
                for y in range(math.floor((y1-half)/5)+1, math.ceil((y2+half)/5)):
                    blocked.add((x,y))
        start = (258,152)  # 1290,760
        assert start not in blocked
        visited={start}
        queue=deque([start])
        while queue:
            x,y=queue.popleft()
            for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if 0<=q[0]<=269 and 0<=q[1]<=209 and q not in visited and q not in blocked:
                    visited.add(q)
                    queue.append(q)
        for name,(x,y) in destinations.items():
            assert (x//5,y//5) in visited, (v, name, width, (x,y))
    targets = dict(кухня=(480,925), гостиная=(285,530),
                   детская_слева=(145,255), родители=(600,145) if v==3 else (500,260),
                   детская_справа=(1025,280) if v!=3 else (1045,330))
    if v==2:
        targets['гардеробная']=(1050,610)
    accessible(80, targets)
    accessible(70, {'ванная':(743,522), 'душевая':(715,905)})


for v in layout.VARIANTS:
    p = layout.build_plan(v)
    check_enclosures(p, v)
    check_use(p, v)
    check_kitchen_backing(p)
    check_wall_connections(p)
    for key, minimum in [('kid1', 13), ('kid2', 13), ('parents', 17)]:
        assert layout.room_area(v, key) >= minimum, (v, key)
    assert layout.polygon_area(layout.living_polygon(v)) >= 19
    windows = [(i['x1'], i['y1'], i['x2'], i['y2']) for i in p.items if i['kind'] == 'window']
    for i in p.items:
        if i['kind'] == 'wall' and i['new']:
            rect = (i['x1'], i['y1'], i['x2'], i['y2'])
            assert not any(overlap(rect, w) for w in windows), ('Перегородка делит окно', v, rect)
    assert any(i['kind'] == 'ksink' and i['x'] + i['w']/2 == layout.SINK_CENTER[0]
               and i['y'] + i['h']/2 == layout.SINK_CENTER[1] for i in p.items)
    assert all(any(i['kind'] == 'shaft' and i['x1'] <= x <= i['x2'] and i['y1'] <= y <= i['y2']
                   for i in p.items) for x, y in layout.RISERS)
    print(f'Вариант {v}: замкнутость комнат и с/у, примыкания стен, техника у стены кухни, площади и мебель — OK')
