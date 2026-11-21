"""Проверка ключевых ограничений эскиза: python3 projects/kvartira-104/validate.py.

Не заменяет обмер и проверку проекта архитектором.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import layout


def overlap(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


for v in (1, 2):
    p = layout.build_plan(v)
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
    print(f'Вариант {v}: площади, окна, кровати/шкафы, мойка и стояки — OK')
