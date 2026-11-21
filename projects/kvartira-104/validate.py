"""Проверка ключевых ограничений эскиза: python3 projects/kvartira-104/validate.py.

Не заменяет обмер и проверку проекта архитектором.
"""
import sys
from bisect import bisect_right
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import layout


def overlap(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def check_enclosures(p, variant):
    """Закрываем только заявленные двери. Любая иная щель должна провалить тест.

    Сетка строится по ВСЕМ граням стен: даже зазор 1 см не исчезает из-за
    округления или выбранного разрешения картинки. Мебель стены не заменяет.
    """
    barriers = []
    for i in p.items:
        if i['kind'] in ('wall', 'shaft', 'window'):
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
    probes = dict(layout.ROOM_PROBES[variant], su1=(730, 510), su2=(720, 930))
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
    for i in p.items:
        if i['kind'] in ('bed', 'wardrobe', 'box', 'shelf', 'appliance', 'basin', 'bath', 'wc', 'washer', 'walkin', 'counter'):
            rect = (i['x'], i['y'], i['x']+i['w'], i['y']+i['h'])
            assert not any(overlap(rect, (w['x1'], w['y1'], w['x2'], w['y2'])) for w in walls), ('Мебель внутри стены', i)


for v in (1, 2):
    p = layout.build_plan(v)
    check_enclosures(p, v)
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
    # Полноразмерные каркасы кроватей и шкафы не пересекаются.
    furniture = [i for i in p.items if i['kind'] in ('bed', 'wardrobe')]
    for j, a in enumerate(furniture):
        for b in furniture[j+1:]:
            assert not overlap((a['x'], a['y'], a['x']+a['w'], a['y']+a['h']),
                               (b['x'], b['y'], b['x']+b['w'], b['y']+b['h'])), (v, a, b)
    print(f'Вариант {v}: замкнутость комнат и с/у, примыкания стен, техника у стены кухни, площади и мебель — OK')
