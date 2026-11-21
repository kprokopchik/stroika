"""Страница шагов с раскрывающимися закупками и компактная печатная версия."""
from html import escape as E
import renovation_model as M


def anchor(id):return 'step-'+id.replace('.','-')
def title(s):return f'{s["order"]:02d}. {s["title"]} · шаг {s["id"]}'
def link(id, plan, prefix=''):
    s=next(s for s in plan['steps'] if s['id']==id)
    return f'<a href="{prefix}#{anchor(id)}">{s["order"]:02d} · {id}</a>'
def tab(name,head,rows,note=None):return ('table',name,head,rows,note)


def sequence_table(plan, prefix='', room=None):
    rows=[];cumulative=0
    for s in plan['steps']:
        if room is not None:
            values=s['room_cost'].get(room,{})
            goods=values.get('materials',0);work=values.get('labor',0)
            if not goods+work:continue
            cumulative+=goods+work
            rows.append([link(s['id'],plan,prefix),s['title'],M.money(goods),M.money(work),M.money(goods+work),M.money(cumulative)])
        else:
            rows.append([link(s['id'],plan,prefix),s['title'],
                         ', '.join(link(a,plan,prefix) for a in s['after']) or 'Начало',
                         M.money(s['cash']),M.money(s['contingency']),M.money(s['total']),M.money(s['cumulative'])])
    if room is not None:
        return tab('Платежи этой комнаты по шагам',['№ / шаг','Что делаем','Товары, ₽','Работы, ₽','Расходы, ₽','Накопленно, ₽'],rows,
                   'Это доли общей закупки и пакетов работ, без логистики/резерва. Собирать заказ нужно по общей карточке шага; отдельное округление пачек на комнату не требуется.')
    return tab('Последовательность и деньги на каждом шаге',
               ['№ / шаг','Что делаем','После шагов','Расходы, ₽','Резерв, ₽','Лимит шага, ₽','Лимит накопленно, ₽'],rows,
               'Нажмите номер: откроются действия, закупки и работы. «Расходы» = оплаты товаров + работы + логистика. Резерв — отдельный запас денег. Накопленный лимит включает резерв и не означает, что он обязательно будет потрачен.')


def build_document(rows,plan,src,source_html):
    items={r['id']:r for r in rows};blocks=[];printed=[]
    intro=('Номера слева задают безопасную последовательность. Код шага сохраняет номер раздела сметы: '
           'например, закрытие стен 1.03 идёт после испытаний 2.06, мокрая отделка 5.01…5.03 — перед деревянным полом 4.01…4.03, '
           'а фартук 5.04 — после кухни 7.02. Независимые работы можно совмещать после выполнения зависимостей.')
    costs=('Встроенные шкафы, кухня, скамья и ограждение душа оплачиваются в расчётном сценарии 50/50: '
           'аванс на шаге 7.01, остаток при монтаже. Полный заказ учитывается один раз. '
           'Доставка и резерв распределены из прежних общих сумм; стоимость квартиры не увеличена.')
    blocks += [('p',intro),('p',costs),sequence_table(plan)]
    printed += [('p',intro),('p',costs),sequence_table(plan)]
    for s in plan['steps']:
        after=', '.join(link(a,plan) for a in s['after']) or 'Начало работ'
        amounts=[['Закупки / оплаты заказов',M.money(s['materials'])],['Работы',M.money(s['labor'])],
                 ['Логистика: плановый лимит',M.money(s['logistics'])],['Расходы без резерва',M.money(s['cash'])],
                 ['Резерв',M.money(s['contingency'])],['Лимит шага с резервом',M.money(s['total'])],
                 ['Лимит от начала ремонта',M.money(s['cumulative'])]]
        detail=[('p',f'<b>После:</b> {after}. <b>Ориентир срока:</b> {E(s["duration"])}.'),
                ('cards',[('Выполнение',None,[s['action']]),('Можно переходить дальше',None,[s['ready']])]),
                tab('Деньги на шаг',['Статья','Сумма, ₽'],amounts)]
        print_detail=[('h2',title(s)),('p',s['action']),('p','Готовность: '+s['ready']),
                      ('p',f'Расходы {M.money(s["cash"])} ₽; резерв {M.money(s["contingency"])} ₽; лимит {M.money(s["total"])} ₽. После: '+', '.join(s['after']))]
        buying=[];compact=[]
        for line in s['purchases']:
            r=items[line['item_id']]
            amount=(str(int(line['packs'])) if float(line['packs']).is_integer() else M.f(line['packs'],3))
            quantity=f'{amount} × {M.f(r["pack"],3)} {r["unit"]}'
            if line['kind']=='Доплата 50%':
                operation='Доплата 50%; без нового заказа. Аванс: '+link('7.01',plan)
            elif line['kind']=='Аванс 50%':
                operation=f'Заказать {quantity}; аванс 50%. Полный заказ: {M.money(r["cost"])} ₽.'
            else:operation=line['kind']+': '+quantity
            buying.append([f'<a href="../zakupki/#sku-{r["id"]}">{E(r["name"])}</a>',operation,M.money(line['cost']),source_html(r['id'],src)])
            compact.append([r['name'],line['kind']+(': '+quantity if line['packs'] else '; без нового заказа'),M.money(line['cost'])])
        if buying:
            detail.append(tab('Купить или оплатить на этом шаге',['Позиция','Заказ / оплата','Сумма, ₽','Где купить'],buying,
                              'Запас и округление упаковок уже учтены. Для аванса количество означает весь заказ, сумма — только первый платёж. Не оплачивайте полный заказ повторно при доплате.'))
            print_detail.append(tab('Закупки и оплаты',['Позиция','Количество / действие','Сумма, ₽'],compact))
        else:
            detail.append(('p','Новых покупок на этом шаге нет; см. работы и материалы из ранних закупок.'))
        if s['jobs']:
            workrows=[[j['name'],str(j['share'])+'% от '+M.money(j['package_cost'])+' ₽',M.money(j['cost'])] for j in s['jobs']]
            detail.append(tab('Оплата работ',['Пакет','Доля оплаты','Сумма, ₽'],workrows,
                              'Это часть ранее учтённого пакета работ. Проценты — предварительный сценарий договора; общая стоимость пакета сохранена.'))
            print_detail.append(tab('Работы',['Пакет','Доля','Сумма, ₽'],workrows))
        if s['stock']:
            stockrows=[[items[id]['name'],link(plan['items'][id]['first'],plan),'Проверить остаток; в новую закупку повторно не включено'] for id in s['stock']]
            detail.append(tab('Использовать из ранних закупок',['Материал / устройство','Первая закупка','Учёт'],stockrows,
                              'Показан источник запаса, а не обещанный остаток на складе: остатки сверить перед началом шага. При нехватке сверх сметы оформляется отдельная корректировка.'))
            print_detail.append(('p','Из ранних закупок: '+', '.join(items[id]['name'] for id in s['stock'])+'. Повторной оплаты в этом шаге нет.'))
        blocks.append(('details',anchor(s['id']),title(s)+' · лимит '+M.money(s['total'])+' ₽',detail))
        printed.extend(print_detail)
    return dict(lede=f'{len(plan["steps"])} последовательных шагов с закупками, работами, проверками и накопленным лимитом. Этапы сметы сохранены, их порядок на площадке уточнён.',
                blocks=blocks,pdf_blocks=printed)
