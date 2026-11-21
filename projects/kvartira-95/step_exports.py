"""Табличные представления шагов; формулы используют существующую книгу сметы."""
import renovation_model as M


def formula(expression, cached):
    return ('formula', expression, cached)


def make_sheets(rows, plan):
    items={r['id']:r for r in rows}
    item_rows={r['id']:i for i,r in enumerate(rows,2)}
    payments=[['Шаг','Код','Позиция','Вид оплаты','Заказать упаковок','Объём заказа','Единица',
               'Цена уп ₽','Платёж ₽','Цена полного заказа ₽','Источник1','Источник2',
               'Примечание','Стоимость поставки для логистики ₽']]
    payment_csv=[payments[0]]
    earlier={}
    for step in plan['steps']:
        for line in step['purchases']:
            item=items[line['item_id']];base=item_rows[item['id']];ri=len(payments)+1
            advance=line['kind'] in ('Аванс 50%','Доплата 50%')
            prior=earlier.get(item['id'],[])
            if line['kind']=='Доплата 50%':quantity='0'
            elif line['kind']=='Покупка партии':
                quantity=(f'ROUNDUP(Закупки!H{base}/2,0)' if line['event_index']==0
                          else f'Закупки!H{base}-SUM('+','.join('E'+str(n) for n in prior)+')')
            else:quantity=f'Закупки!H{base}'
            if line['kind']=='Аванс 50%':cost=f'ROUND(Закупки!J{base}*0.5,0)'
            elif line['kind']=='Доплата 50%':cost=f'Закупки!J{base}-SUM('+','.join('I'+str(n) for n in prior)+')'
            elif line['kind']=='Покупка партии':cost=f'ROUND(E{ri}*H{ri},0)'
            else:cost=f'Закупки!J{base}'
            shipment = (f'Закупки!J{base}' if line['kind']=='Доплата 50%' else '0') if advance else f'I{ri}'
            note=('Заказ целиком регистрируется при авансе; доплата не создаёт повторную покупку.' if advance
                  else 'Часть общей закупки: суммарно столько же упаковок, без повторного запаса.' if line['kind']=='Покупка партии'
                  else item['note'])
            urls=[s['url'] for s in plan['sources'].get(item['id'],{}).get('links',[])][:2]+['','']
            cached=[step['id'],item['id'],item['name'],line['kind'],line['packs'],line['buy'],item['unit'],
                    item['price'],line['cost'],item['cost'],urls[0],urls[1],note,
                    item['cost'] if line['kind']=='Доплата 50%' else 0 if advance else line['cost']]
            payment_csv.append(cached)
            cells=cached.copy()
            cells[4]=formula(quantity,line['packs'])
            cells[5]=formula(f'E{ri}*Закупки!G{base}',line['buy'])
            cells[7]=formula(f'Закупки!I{base}',item['price'])
            cells[8]=formula(cost,line['cost'])
            cells[9]=formula(f'Закупки!J{base}',item['cost'])
            cells[13]=formula(shipment,cached[13]);payments.append(cells)
            earlier.setdefault(item['id'],[]).append(ri)
    works=[['Шаг','Код пакета','Работа','Цена пакета ₽','Доля пакета %','Платёж ₽']]
    work_csv=[works[0]];earlier={}
    for step in plan['steps']:
        for job in step['jobs']:
            ri=len(works)+1;base=int(job['id'][1:])+2;prior=earlier.get(job['id'],[])
            before='SUM('+','.join('E'+str(n) for n in prior)+')' if prior else '0'
            upto='SUM('+','.join('E'+str(n) for n in prior+[ri])+')'
            cached=[step['id'],job['id'],job['name'],job['package_cost'],job['share'],job['cost']]
            work_csv.append(cached)
            cells=cached.copy();cells[3]=formula(f'Работы!F{base}',job['package_cost'])
            cells[5]=formula(f'ROUND(D{ri}*{upto}/100,0)-ROUND(D{ri}*{before}/100,0)',job['cost'])
            works.append(cells);earlier.setdefault(job['id'],[]).append(ri)
    headers=['Порядок','Шаг','Этап','Что делаем','После шагов','Закупки/оплаты ₽','Работы ₽',
             'Логистика ₽','Резерв ₽','Расходы без резерва ₽','Лимит шага ₽',
             'Расходы накопленно ₽','Лимит накопленно ₽','Действия','Условие готовности',
             'Ориентир срока','Стоимость поставок для логистики ₽']
    table=[headers];step_csv=[headers];last=len(plan['steps'])+1
    for ri,s in enumerate(plan['steps'],2):
        cached=[s['order'],s['id'],s['stage'],s['title'],', '.join(s['after']),s['materials'],s['labor'],
                s['logistics'],s['contingency'],s['cash'],s['total'],s['cash_cumulative'],s['cumulative'],
                s['action'],s['ready'],s['duration'],s['delivery_weight']]
        step_csv.append(cached)
        cells=cached.copy()
        cells[5]=formula(f"SUMIF('Покупки шагов'!A2:A{len(payments)},B{ri},'Покупки шагов'!I2:I{len(payments)})",s['materials'])
        cells[6]=formula(f"SUMIF('Работы шагов'!A2:A{len(works)},B{ri},'Работы шагов'!F2:F{len(works)})",s['labor'])
        cells[16]=formula(f"SUMIF('Покупки шагов'!A2:A{len(payments)},B{ri},'Покупки шагов'!N2:N{len(payments)})",s['delivery_weight'])
        before_log=f'ROUND(Бюджет!B4*SUM(Q2:Q{ri-1})/SUM(Q2:Q{last}),0)' if ri>2 else '0'
        cells[7]=formula(f'ROUND(Бюджет!B4*SUM(Q2:Q{ri})/SUM(Q2:Q{last}),0)-{before_log}',s['logistics'])
        before_res=f'ROUND(Бюджет!B5*SUM(J2:J{ri-1})/SUM(J2:J{last}),0)' if ri>2 else '0'
        cells[8]=formula(f'ROUND(Бюджет!B5*SUM(J2:J{ri})/SUM(J2:J{last}),0)-{before_res}',s['contingency'])
        for col,expr,cache in [(9,f'SUM(F{ri}:H{ri})',s['cash']), (10,f'J{ri}+I{ri}',s['total']),
                               (11,f'SUM(J2:J{ri})',s['cash_cumulative']), (12,f'SUM(K2:K{ri})',s['cumulative'])]:
            cells[col]=formula(expr,cache)
        table.append(cells)
    return ([('Шаги',table),('Покупки шагов',payments),('Работы шагов',works)],
            {'v1-steps.csv':step_csv,'v1-step-purchases.csv':payment_csv,'v1-step-labor.csv':work_csv})
