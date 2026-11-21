"""Последовательность В1 и кассовый план без повторной закупки упаковок.

Этап — раздел бюджета, order — порядок на площадке. Поэтому закрытие стен этапа1
следует за испытанием сетей этапа2, а мокрая отделка этапа5 — до деревянного пола.
Все цены/количества берутся из общей сметы; здесь только сроки покупок и оплаты.
"""
from math import ceil
import renovation_model as M


def step(id, title, after, action, ready, duration):
    return dict(id=id, stage=int(id.split('.')[0]), title=title,
                after=after.split(), action=action, ready=ready, duration=duration)


STEPS = [
    step('0.01', 'Обмер и обследование', '',
         'Измерить плиты, окна, проёмы, стояки и выпуски канализации; получить КЖ и параметры ввода.',
         'Есть обмер, отметки и список подтверждённых исходных данных.', '1–3 дня'),
    step('0.02', 'Рабочие схемы и согласование комплектующих', '0.01',
         'Утвердить мебель/технику, чистый ноль, перегородки и закладные; согласовать все трассы. Выбрать скрытые части сантехники, аппараты щита, свет и карнизы до закупки.',
         'Размеры, совместимость, доступ и способ прокладки возле дерева проверены проектировщиками.', '5–10 рабочих дней'),
    step('0.03', 'Подготовка площадки', '0.02',
         'Защитить окна и общие зоны, обозначить склад и место мусора; организовать временное питание и воду силами подрядчика.',
         'Площадка готова, пути доставки и хранения согласованы. Отсутствующие перегородки не демонтируем.', '1–2 дня'),
    step('1.01', 'Каркас перегородок и усиленные проёмы', '0.03',
         'Разметить и закрепить каркас на плите, поставить UA и закладные под сантехнику, кухню, шкафы, спорт и карнизы.',
         'Проёмы и закладные сверены с мебелью и дверными блоками; пол ещё не собран.', '3–5 дней'),
    step('1.02', 'Первая сторона перегородок', '1.01',
         'Привезти первую партию листов и крепежа, зашить одну сторону по системе. Другую оставить открытой для сетей.',
         'Есть доступ внутрь каркаса, скрытые закладные сфотографированы.', '2–3 дня'),
    step('2.01', 'Черновые трассы кондиционеров и вентиляция', '1.02',
         'Проложить медь, изоляцию, конденсат и воздуховоды. Согласовать с потолками и прочими трассами.',
         'Трассы закреплены, герметичность проверена, конденсат имеет согласованный слив.', '2–3 дня'),
    step('2.02', 'Вода, канализация и сантехнические закладные', '1.02 2.01',
         'Собрать два независимых узла, лучи и канализацию, рамы WC и лоток. Примерить/установить ванну с каркасом и сливом по её инструкции до примыкающей облицовки; защитить её. Контроллер и приводы одной системы проверить вместе.',
         'Измерены уклоны и отметки, сохранён доступ к арматуре; узлы примыкания ванны и трапа согласованы.', '4–6 дней'),
    step('2.03', 'Силовые трассы и монтажные коробки', '2.02',
         'Проложить кабели, защитные трубы и коробки по рабочему проекту. Подготовить лючок, проходы через лаги и вводы в щит.',
         'Кабели подписаны, трассы доступны для осмотра и не конфликтуют с трубами/лагами.', '4–6 дней'),
    step('2.04', 'Сборка распределительного щита', '2.03',
         'Собрать 13 линий, четыре УЗО и одну ступень разгрузки, раздельные N-шины, PE и ручной возврат.',
         'Схема соответствует выбранным аппаратам; измерения и проверка логики запланированы до закрытия.', '1–2 дня'),
    step('2.05', 'Cat6, домофон и кабели автоматики', '2.03',
         'Проложить 12 лучей Cat6, вводы провайдера, домофон и кабели датчиков/приводов; установить патч-панель и модули.',
         'Бирки совпадают с портовой картой, нет скрытых муфт, радиусы и разделение трасс выдержаны.', '2–3 дня'),
    step('2.06', 'Проверка скрытых сетей и исполнительная съёмка', '2.02 2.04 2.05',
         'Испытать воду и канализацию, проверить кабели и защиту, прозвонить LAN; снять фото с размерами.',
         'Получены акты и результаты испытаний. До этого шага вторую сторону стен и пол не закрывать.', '1–2 дня'),
    step('1.03', 'Вата и закрытие второй стороны перегородок', '2.06',
         'Привезти оставшиеся листы/крепёж, уложить вату, закрыть каркас и обработать швы по системе.',
         'Доступные ревизии оставлены, обшивка и узлы проверены, акты скрытых работ подписаны.', '2–4 дня'),
    step('3.01', 'Штукатурка минеральных стен', '1.03',
         'Подготовить бетон и оштукатурить сухие/влажные зоны совместимыми составами; не штукатурить листы как бетон.',
         'Геометрия и плоскости приняты, известны чистовые размеры под мебель.', '4–7 дней плюс сушка'),
    step('3.02', 'Минеральные основания санузлов', '2.06 3.01',
         'Собрать основания, отметки трапа, порога и уклоны, сохранив доступ к прочисткам.',
         'Толщина и нагрузки проверены; прочность/влажность позволяют наносить гидроизоляцию.', '2–3 дня плюс выдержка'),
    step('3.03', 'Гидроизоляция мокрых зон', '3.02',
         'Выполнить слои, ленты, манжеты и примыкания к ванне/лотку по одной системе.',
         'Все проходки и углы защищены, состав выдержан по инструкции.', '1–2 дня плюс выдержка'),
    step('3.04', 'Проверка гидроизоляции', '3.03',
         'Проверить герметичность по регламенту системы, зафиксировать результат до плитки.',
         'Нет дефектов, есть акт и фотографии. Проверка оплачивается в пакете работ по санузлам.', 'По регламенту системы'),
    step('5.01', 'Тёплые полы и облицовка санузлов', '3.04',
         'Разложить маты только на свободных зонах, проверить сопротивление/изоляцию, выполнить плитку и затирку. Фартук кухни оставляем до столешницы.',
         'Плитка и примыкания приняты, тёплый пол включать только после положенной выдержки клея.', '5–8 дней плюс выдержка'),
    step('5.02', 'Шпаклёвка и подготовка сухих стен', '3.01 5.01',
         'Подготовить стены к окраске, выполнить шлифовку и грунтование, убрать строительную пыль.',
         'Поверхности приняты под выбранную краску.', '3–5 дней плюс сушка'),
    step('5.03', 'Основная окраска', '5.02',
         'Выполнить основные слои краски до деревянного пола; оставить материал для локальных подкрасок после монтажа.',
         'Покрытие просохло, цвет и качество приняты.', '2–3 дня плюс сушка'),
    step('3.05', 'Сушка и допуск к деревянному полу', '5.01 5.03',
         'Измерить влажность оснований и древесины, проверить вентиляцию, окончания мокрых процессов и отметки пола.',
         'Есть зафиксированные измерения в пределах требований материалов; только теперь привозим и акклиматизируем дерево.', 'По измерениям, не по календарю'),
    step('4.01', 'Виброопоры и лаги', '3.05 2.06',
         'Собрать лаги на виброопорах, выдержать шаг и уровень, упругие примыкания и коридоры коммуникаций.',
         'Лаги устойчивы, нагрузка/опоры проверены, жёстких акустических мостов нет.', '2–3 дня'),
    step('4.02', 'Шумоизоляция пола', '4.01',
         'Уложить вату, осмотреть все проходы и кабели до настила.',
         'Полости заполнены без пережатия труб, есть фото открытого пола.', '1 день'),
    step('4.03', 'Два слоя фанеры и лючок', '4.02',
         'Собрать два слоя со смещением стыков, клеем и крепежом, установить ранее купленный лючок на подготовленную опору.',
         'Нет прогиба/скрипа, выдержаны зазоры, лючок открывается и соответствует полому полу.', '2–3 дня'),
    step('7.01', 'Контрольный обмер и заказ встроенной мебели', '4.03 5.01',
         'Подтвердить высоту будущего покрытия и потолка, размеры кухни, шкафов, скамьи и ограждения душа. Заказать изготовление; в расчётном сценарии оплатить 50%.',
         'Есть развёртки, комплектность, сроки и размер аванса. Плинтусы, карнизы, доступ к технике и ревизиям учтены.', 'Обмер 1 день; изготовление обычно параллельно чистовым работам'),
    step('6.01', 'Ламинат и подложка', '4.03 5.03',
         'Уложить покрытие с зазорами по паспорту, сразу защитить от последующего монтажа.',
         'Пол принят, дверные блоки проверяются по фактической отметке покрытия.', '2–3 дня'),
    step('6.02', 'Дверные блоки', '6.01',
         'Установить пять распашных дверей и сдвижную дверь кладовой, фурнитуру и ограничители по комплектам.',
         'Проходы/открывание проверены, полотно не задевает покрытие и мебель.', '1–2 дня'),
    step('6.03', 'Карнизы, платформы и натяжные потолки', '6.02 7.01',
         'Проверить закладные и глубины приборов, установить карнизы и потолок. Подводы/драйверы остаются доступными.',
         'Опуск минимален для выбранных приборов, все точки и выходы подготовлены.', '1–2 дня'),
    step('6.04', 'Розетки, выключатели, свет и термостаты', '6.03 2.04',
         'Установить механизмы, светильники, вентиляторы, термостаты и фасады LAN; проверить цепи и защиту.',
         'Назначения/высоты/маркировка совпадают с ведомостями, безопасное питание готово к подключению техники.', '2–4 дня'),
    step('6.05', 'Плинтусы и завершение примыканий', '6.04',
         'Смонтировать плинтусы там, где они не мешают встроенной мебели; остатки оставить для завершающих участков.',
         'Плавающий пол не зажат, технологические зазоры сохранены.', '1–2 дня'),
    step('7.02', 'Кухня и столешница', '7.01 6.05',
         'Принять доставку, собрать корпуса и столешницу по карте раскроя, установить подсветку. Оплатить оставшиеся 50% кухонного заказа.',
         'Столешница и стыки приняты, техника/выводы доступны; можно делать фартук.', '2–4 дня после готовности заказа'),
    step('5.04', 'Фартук кухни', '7.02',
         'Выполнить фартук по установленной столешнице, закрыть примыкания. Использовать остатки клея/затирки из общей закупки.',
         'Кухня и пол защищены, стык со столешницей герметичен.', '1–2 дня плюс выдержка'),
    step('7.03', 'Шкафы и техническая секция', '7.01 6.05',
         'Смонтировать шкафы, технический корпус и скамью; оплатить оставшиеся 50% соответствующих заказов.',
         'Щит, сеть и сервисные люки доступны, вентиляция технической секции не перекрыта.', '2–4 дня после готовности заказа'),
    step('7.04', 'Чистовая сантехника', '5.01 5.04',
         'Установить чаши WC, тумбы/раковины, смесители, мойку, ограждение, зеркала и полотенцесушители; завершить ванну и подключение сливов.',
         'Нет течей, все приборы/краны/сифоны обслуживаются. Остаток заказа ограждения оплачивается здесь.', '2–3 дня'),
    step('7.05', 'Бытовая техника и блоки кондиционеров', '7.02 7.04 6.04',
         'Подключить кухонную технику, отдельные стиральную/сушильную машины и два сплита. Колонну собрать только совместимым комплектом.',
         'Вводные мощности и лимит варочной подтверждены, доступы сохранены, первоначальные тесты выполнены.', '2–3 дня'),
    step('7.06', 'Свободностоящая мебель и хранение', '7.03 7.05',
         'Собрать кровати, столы, стулья, диван, стеллажи и спортивное оснащение; крепить только к подготовленным закладным.',
         'Расстановка и проходы проверены, крепления и комплекты приняты.', '2–4 дня'),
    step('7.07', 'Сеть, сервер и домофон', '7.03 6.04',
         'Подключить роутер, коммутатор, AP и NAS, измерить LAN, настроить Wi-Fi и проверить домофон.',
         'Получены карта портов и результаты тестов; пароли переданы непублично.', '1–2 дня'),
    step('7.08', 'Уборка после монтажа', '7.04 7.05 7.06 7.07',
         'Убрать монтажную пыль, снять защиту, проверить покрытия и остатки материалов до раскладки ковров/штор.',
         'Помещения чистые, повреждения и замечания зафиксированы.', '1–2 дня'),
    step('7.09', 'Шторы и ковры', '7.08 6.03',
         'Установить текстиль по фактической чистой высоте и разложить ковры.',
         'Текстиль не мешает дверям, радиаторам и проходам.', '1 день'),
    step('7.10', 'Общая пусконаладка', '7.05 7.07 7.09',
         'Проверить щит и разгрузку с ручным возвратом, все датчики/четыре крана, одновременный водоразбор/слив, сеть и технику.',
         'Протоколы и режимы работы подписаны; выявленные дефекты устранены.', '1–2 дня'),
    step('7.11', 'Передача квартиры и документов', '7.10',
         'Передать исполнительные схемы, акты, гарантии, настройки, инструкции и оставшиеся материалы.',
         'Замечания закрыты, показаны ручные режимы щита/воды и доступ к обслуживанию.', '1 день'),
]
BY_ID = {s['id']: s for s in STEPS}

# Каждая позиция указана ровно в одной группе. Дополнительные партии листов/крепежа
# распределяются ниже из уже округлённой общей закупки, без нового округления.
PURCHASE_GROUPS = {
 '0.03': 'protection bags',
 '1.01': 'stud track ua uaangle backing anchors sealtape',
 '1.02': 'board boardwet screws joint jointtape',
 '1.03': 'wool',
 '2.01': 'ventduct ventbend acpipe acdrain acsiphon',
 '2.02': 'pex16 pex20 insulation fitting16 sleeve16 elbow16 fitting20 sleeve20 manifold3 manifold4 manifold6 cap filter reducer checkvalve ballvalve union leakcontroller leakvalve leaksensor servicecab sewer50 sewer110 bend50 tee50 bend110 cleanout pipeclamp wcframe showerdrain machinevalve laundrysiphon insulation22 leaksplit pressuregauge manifoldjoin signalwire bath bathdrain',
 '2.03': 'cable15 cable25 cable6 steelpipe steelbox conduit socketbox floorbox',
 '2.04': 'panelbox rcd mcb16 mcb10 mcb10two mcb32 mcb2 isolator voltage priority contactor auxcontact buttons inputblock nbar pebar branchblock comb wirekit ferrules duct',
 '2.05': 'cat6 dataconduit patchpanel keystone apbox networkbracket',
 '3.01': 'plaster cementplaster concreteprimer primer',
 '3.02': 'screed',
 '3.03': 'waterproof wptape wpcollar',
 '4.01': 'floorboard vibro floortape',
 '4.02': 'floorwool',
 '4.03': 'plywood floorglue floorscrew',
 '5.01': 'floortile walltile tileglue grout silicone heatmat',
 '5.02': 'putty',
 '5.03': 'paint',
 '5.04': 'backsplash',
 '6.01': 'underlay laminate',
 '6.02': 'door slidingdoor handle',
 '6.03': 'ceiling ceilingprofile ceilingmount ceilingring curtainrod',
 '6.04': 'thermostat fan ventgrille socket socketwet switch1 switch2 passswitch crossswitch frame spot ceilinglamp sconce pendant step motion lanface spot65',
 '6.05': 'skirting skirtingglue',
 '7.02': 'kitchenbase kitchenupper kitchentower worktop kitchenhardware led ledprofile ledpsu',
 '7.03': 'wardrobe shallowwardrobe techcase bench',
 '7.04': 'bathmixer basin basinmixer basinsiphon wc showermixer showerglass sink sinkmixer sinksiphon towel mirror showergrate',
 '7.05': 'ac fridge oven hob dishwasher microwave hood washer dryer stackkit kettle coffee',
 '7.06': 'bed180 mattress180 kidbed kidmattress nightstand shelfbed desk officechair commode armchair ottoman bookcase wallshelf beanbag wallbars climbing mat rug shoebench bikehook storageshelf sporthook diningtable chair sofa coffeetable tvstand',
 '7.07': 'patchcord roompatch switchpoe router ap nas hdd intercom powerstrip firedetector',
 '7.09': 'curtains',
}
# Ковры раскладываются после уборки, вместе с текстилем.
PURCHASE_GROUPS['7.06'] = PURCHASE_GROUPS['7.06'].replace(' rug ', ' ')
PURCHASE_GROUPS['7.09'] += ' rug'
ADVANCE_IDS = set('kitchenbase kitchenupper kitchentower worktop kitchenhardware wardrobe shallowwardrobe techcase bench showerglass'.split())
PARTY_IDS = set('board boardwet screws joint jointtape'.split())
REUSE = {
 '1.02': 'backing sealtape anchors',
 '2.05': 'signalwire leakcontroller leaksensor leaksplit',
 '1.03': 'backing anchors sealtape',
 '3.01': 'joint jointtape protection bags',
 '3.03': 'primer bath bathdrain showerdrain',
 '5.01': 'primer bath bathdrain',
 '5.02': 'primer joint jointtape',
 '5.03': 'primer protection',
 '4.01': 'protection bags',
 '4.03': 'floorbox',
 '6.03': 'backing protection',
 '6.04': 'cable15 cable25 socketbox keystone apbox',
 '6.05': 'protection',
 '7.02': 'backing',
 '5.04': 'primer tileglue grout silicone',
 '7.04': 'bath bathdrain silicone',
 '7.07': 'patchpanel keystone',
 '7.10': 'leakcontroller leaksensor leaksplit leakvalve',
}

# Проценты — распределение имеющихся договорных пакетов, не новые работы.
# Порядок ключей соответствует LABOR; проверка имени защищает от сдвига индексов.
LABOR_PARTS = [
 ('Обмер, рабочие схемы, технадзор (допуск)', {'0.01':30, '0.02':50, '3.05':10, '7.11':10}),
 ('Каркасные перегородки с обшивкой', {'1.01':40, '1.02':20, '1.03':40}),
 ('Электрика: разводка, сборка щита и испытания', {'0.03':5, '2.03':35, '2.04':25, '2.06':20, '6.04':10, '7.10':5}),
 ('Водопровод, канализация, узлы и испытания', {'2.02':70, '2.06':20, '7.10':10}),
 ('LAN, датчики, шкаф и измерения линий', {'2.05':40, '2.06':20, '7.07':30, '7.10':10}),
 ('Два сплита: черновой/чистовой монтаж', {'2.01':60, '7.05':40}),
 ('Вентиляция и подключения', {'2.01':70, '6.04':30}),
 ('Штукатурка минеральных оснований', {'3.01':100}),
 ('Полы санузлов и гидроизоляция', {'3.02':55, '3.03':30, '3.04':15}),
 ('Лаги, виброопоры, два слоя фанеры', {'4.01':45, '4.02':10, '4.03':45}),
 ('Шпаклёвка, шлифовка, окраска', {'5.02':60, '5.03':40}),
 ('Облицовка стен/пола плиткой', {'5.01':93, '5.04':7}),
 ('Натяжной потолок: монтаж/обводы', {'6.03':100}),
 ('Ламинат и плинтусы', {'6.01':75, '6.05':25}),
 ('Установка дверей', {'6.02':100}),
 ('Сборка мебели и подключение техники', {'7.02':35, '7.03':25, '7.05':15, '7.06':20, '7.09':5}),
 ('Монтаж сантехники, приёмка и уборка', {'0.03':5, '7.04':60, '7.08':20, '7.10':10, '7.11':5}),
]


def distribute(cost, room_cost, portions):
    """Сохранить одновременно цену пакета и все его комнатные доли в рублях."""
    remaining = dict(room_cost)
    for i, (key, amount) in enumerate(portions):
        allocation = (dict(remaining) if i == len(portions)-1
                      else M.apportion(amount, remaining) if amount else {})
        assert sum(allocation.values()) == amount
        for room, value in allocation.items():
            remaining[room] -= value
            assert remaining[room] >= 0
        yield key, amount, allocation
    assert sum(remaining.values()) == 0 and sum(n for _, n in portions) == cost


def running_allocation(total, weights):
    """Округление накопленных долей: те же формулы можно воспроизвести в Excel."""
    denominator=sum(weights.values());accumulated=0;previous=0;result={}
    for key,weight in weights.items():
        accumulated+=weight
        rounded=(2*total*accumulated+denominator)//(2*denominator)
        result[key]=rounded-previous;previous=rounded
    return result


def build_plan(rows, room_totals, room_work):
    """Все суммы и заказы выводятся из общей сметы; повторно цены не назначаем."""
    steps = [{**s, 'order':i+1, 'purchases':[], 'jobs':[], 'stock':REUSE.get(s['id'],'').split(),
              'materials':0, 'labor':0, 'delivery_weight':0, 'room_cost':{}}
             for i,s in enumerate(STEPS)]
    by_step = {s['id']:s for s in steps}
    positions = {s['id']:s['order'] for s in steps}
    for s in steps:
        assert all(positions[a] < s['order'] for a in s['after']), s['id']
    assigned = {}
    for step_id, ids in PURCHASE_GROUPS.items():
        for item_id in ids.split():
            if item_id in assigned:raise ValueError('Повторная закупка: '+item_id)
            assigned[item_id] = step_id
    if set(assigned) != {r['id'] for r in rows}:
        raise ValueError('Не совпал состав закупок: '+str(set(assigned) ^ {r['id'] for r in rows}))
    schedule = {}
    for r in rows:
        dest = assigned[r['id']]
        deliveries = [(dest, r['packs'])]
        if r['id'] in PARTY_IDS:
            first = ceil(r['packs']/2)
            deliveries = [('1.02',first), ('1.03',r['packs']-first)]
        if r['id'] in ADVANCE_IDS:
            portions = [('7.01',(r['cost']+1)//2), (dest,r['cost']//2)]
        else:
            portions = [(s,round(packs*r['price'])) for s,packs in deliveries if packs]
        events=[]
        for index,(step_id,amount,room_share) in enumerate(distribute(r['cost'],r['room_cost'],portions)):
            advance = r['id'] in ADVANCE_IDS
            # При авансе регистрируем весь заказ один раз; при доплате количество не повторяем.
            packs = r['packs'] if advance and index==0 else 0 if advance else deliveries[index][1]
            kind = ('Аванс 50%' if index==0 else 'Доплата 50%') if advance else 'Покупка партии' if len(deliveries)>1 else 'Покупка'
            line = dict(item_id=r['id'], kind=kind, cost=amount, invoice_cost=r['cost'],
                        packs=packs, buy=packs*r['pack'], unit=r['unit'], pack=r['pack'],
                        price=r['price'], room_cost=room_share, event_index=index,
                        final=index==len(portions)-1)
            current=by_step[step_id]
            current['purchases'].append(line);current['materials']+=amount
            for room,n in room_share.items():
                current['room_cost'].setdefault(room,{'materials':0,'labor':0})['materials']+=n
            events.append(dict(step=step_id,kind=kind,packs=packs,cost=amount))
        delivery_step=dest if r['id'] in ADVANCE_IDS else portions[0][0]
        if r['id'] in ADVANCE_IDS:
            by_step[dest]['delivery_weight']+=r['cost']
        else:
            for step_id,amount in portions:by_step[step_id]['delivery_weight']+=amount
        schedule[r['id']]=dict(first=portions[0][0],delivery=delivery_step,events=events)
    if len(room_work)!=len(LABOR_PARTS):raise ValueError('Изменился состав работ')
    for labor_index,(job,(name,weights)) in enumerate(zip(room_work,LABOR_PARTS)):
        if job['name']!=name:raise ValueError('Проверить разбивку работы: '+job['name'])
        if sum(weights.values())!=100:raise ValueError('Доли оплаты должны составлять100%: '+name)
        costs=running_allocation(job['cost'],weights)
        for step_id,amount,room_share in distribute(job['cost'],job['room_cost'],list(costs.items())):
            current=by_step[step_id]
            current['jobs'].append(dict(id='L'+str(labor_index),name=name,cost=amount,
                                        share=weights[step_id],package_cost=job['cost'],room_cost=room_share))
            current['labor']+=amount
            for room,n in room_share.items():
                current['room_cost'].setdefault(room,{'materials':0,'labor':0})['labor']+=n
    for s in steps:
        for item_id in s['stock']:
            assert positions[schedule[item_id]['first']] < s['order'], (s['id'],item_id)
    totals=M.totals(rows)
    logistics=running_allocation(totals['logistics'],{s['id']:s['delivery_weight'] for s in steps})
    direct={s['id']:s['materials']+s['labor']+logistics.get(s['id'],0) for s in steps}
    reserve=running_allocation(totals['contingency'],direct)
    cumulative=0;cash_cumulative=0
    for s in steps:
        s['logistics']=logistics.get(s['id'],0);s['contingency']=reserve.get(s['id'],0)
        s['cash']=direct[s['id']];s['total']=s['cash']+s['contingency']
        cash_cumulative+=s['cash'];cumulative+=s['total']
        s['cash_cumulative']=cash_cumulative;s['cumulative']=cumulative
    assert cumulative==totals['total']
    for key in ('materials','labor','logistics','contingency','total'):
        assert sum(s[key] for s in steps)==totals[key],key
    for room,old in room_totals.items():
        for key in ('materials','labor'):
            assert sum(s['room_cost'].get(room,{}).get(key,0) for s in steps)==old[key],(room,key)
    return dict(steps=steps,items=schedule,
                assumptions=['Аванс встроенной мебели и ограждения50% — плановый сценарий, не условие всех магазинов.',
                             'Доли оплаты пакетов работ — предварительные; общая стоимость работ не меняется.',
                             'Логистика3,5% разнесена по поставкам; фактические рейсы/вывоз уточняются по заявкам.',
                             'Резерв12% — запас денег, а не обязательная покупка/платёж.'])


def stage_totals(plan):
    return {int(id):{key:sum(s[key] for s in plan['steps'] if s['stage']==int(id))
                    for key in ('materials','labor','logistics','contingency','cash','total')}
            for id,*_ in M.STAGES}
