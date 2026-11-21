"""Квартира Level Южнопортовая, 104,5 м²."""
from geometry104 import RIGHT_DEPTH, ROOM_POLYGONS, fmt, living_polygon, polygon_area, room_area

OBJECT = {
    'slug': 'kvartira-104',
    'title': 'Квартира 104,5 м²',
    'subtitle': 'Три семейные планировки с двумя детскими и спальней родителей в центре',
    'about': 'У каждой детской своё окно и рабочий стол. В первом варианте семья обедает у кухонного окна, во втором отдельная гардеробная освобождает прихожую от сезонных вещей. В третьем обеденный стол находится в гостиной, а двери спальни родителей и правой детской выходят в холл.',
    'facts': ['104,5 м²', 'потолок 270 см после стяжки', '3 эскиза'],
    'links': [('Квартира на сайте застройщика', 'https://level.ru/southport/flat/3room/9-257/')],
    'plan_image': 'plan.jpg', 'plan_size': (1139, 881), 'cover': 'previews/v1.svg', 'plans_only': True,
    'plan_notice': 'Размеры в сантиметрах. В площади спален учтены выступы пилонов. Площадь кухни-гостиной указана отдельно от холла.',
    'plan_note': 'Контур восстановлен по скриншоту 1139×881 и векторному плану застройщика. Масштаб 1,28 см на пиксель подобран по подписанным площадям. Толщины новых перегородок и зазоры под мебель предстоит проверить по обмеру. С1 и С2 обозначают предполагаемое положение стояков в пределах своих технических коробов.',
}
VARIANT_SHORT = {1: 'стол у окна', 2: 'семейная гардеробная', 3: 'столовая в гостиной'}


def room(key, slug, name):
    values = {}
    for v in RIGHT_DEPTH:
        pts = ROOM_POLYGONS[v][key]
        xs, ys = zip(*pts)
        values[v] = dict(area=fmt(room_area(v,key)), rect=(min(xs),min(ys),max(xs),max(ys)))
    return dict(id=slug, name=name, **values[1], override=values, notes={v:name for v in RIGHT_DEPTH})


ROOMS = [
    room('kid1','detskaya-1','Детская 1'), room('kid2','detskaya-2','Детская 2'),
    room('parents','spalnya','Спальня родителей'),
]
for slug, name, area, rect in [
    ('kuhnya-gostinaya', 'Кухня-гостиная', fmt(polygon_area(living_polygon(1))), (0, 410, 610, 1046)),
    ('holl', 'Прихожая и хранение', 'шкафы глубиной 60 см', (598,475,1370,850)),
    ('su-1', 'Ванная', '≈ 4,9 м²', (598,410,870,631)),
    ('su-2', 'Душевая', '≈ 4,7 м²', (598,850,870,1046)),
]:
    ROOMS.append(dict(id=slug, name=name, area=area, rect=rect, notes={v:name for v in RIGHT_DEPTH}))
ROOMS[4]['override'] = {3: {'rect': (598,275,1370,850)}}
SECTIONS = []
