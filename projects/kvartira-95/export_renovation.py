"""Экспорт сметы стандартной библиотекой: CSV, JSON и Excel OOXML без зависимостей."""
import csv,io,json,zipfile
from html import escape as X
import renovation_model as M
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'

def col(n):
 s=''
 while n:n,a=divmod(n-1,26);s=chr(65+a)+s
 return s

def xlsx(path,sheets):
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  def put(name,data):
   info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
   z.writestr(info,data)
  put('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'+''.join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1,len(sheets)+1))+'</Types>')
  put('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
  put('xl/workbook.xml',f'<workbook xmlns="{NS}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'+''.join(f'<sheet name="{X(name,quote=True)}" sheetId="{i}" r:id="rId{i}"/>' for i,(name,_) in enumerate(sheets,1))+'</sheets><calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>')
  put('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1,len(sheets)+1))+'</Relationships>')
  for i,(name,rows) in enumerate(sheets,1):
   xml=[f'<worksheet xmlns="{NS}"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><cols><col min="1" max="1" width="22" customWidth="1"/><col min="2" max="2" width="45" customWidth="1"/><col min="3" max="20" width="22" customWidth="1"/></cols><sheetData>']
   for ri,row in enumerate(rows,1):
    xml.append(f'<row r="{ri}">')
    for ci,v in enumerate(row,1):
     addr=f'{col(ci)}{ri}'
     if isinstance(v,tuple) and v[0]=='formula':xml.append(f'<c r="{addr}"><f>{X(v[1])}</f><v>{v[2]}</v></c>')
     elif isinstance(v,(int,float)):xml.append(f'<c r="{addr}"><v>{v}</v></c>')
     else:xml.append(f'<c r="{addr}" t="inlineStr"><is><t xml:space="preserve">{X(str(v))}</t></is></c>')
    xml.append('</row>')
   xml.append(f'</sheetData><autoFilter ref="A1:{col(len(rows[0]))}{len(rows)}"/></worksheet>')
   put(f'xl/worksheets/sheet{i}.xml',''.join(xml))

def write_exports(rows,src,room_totals,room_work):
 dest=M.ROOT/'downloads';dest.mkdir(exist_ok=True)
 headers=['Код','Позиция','Этап','Единица','Нетто','Запас доля','В упаковке','Купить упаковок','Цена уп ₽','Итого ₽','Купить единиц','Источник 1','Источник 2','Формула объёма','Примечание']
 data=[headers];excel=[headers]
 for i,r in enumerate(rows,2):
  sources=src.get(r['id'],{}).get('links',[])
  urls=[s['url'] for s in sources[:2]]+['','']
  vals=[r['id'],r['name'],r['stage'],r['unit'],round(r['net'],4),r['waste'],r['pack'],r['packs'],r['price'],r['cost'],round(r['buy'],4),urls[0],urls[1],r['rule'],r['note']]
  data.append(vals)
  vals=vals.copy();vals[7]=('formula',(f'ROUND(E{i}*(1+F{i})/G{i},3)' if r['id'] in {'wardrobe','shallowwardrobe','desk','kitchenbase','kitchenupper','worktop'} else f'ROUNDUP(E{i}*(1+F{i})/G{i},0)'),r['packs']);vals[9]=('formula',f'ROUND(H{i}*I{i},0)',r['cost']);vals[10]=('formula',f'H{i}*G{i}',r['buy']);excel.append(vals)
 def csvfile(name,items):
  with (dest/name).open('w',encoding='utf-8-sig',newline='') as fp:csv.writer(fp,delimiter=';').writerows(items)
 csvfile('v1-procurement.csv',data)
 roomdata=[['Помещение','Код','Позиция','Нетто комнаты','Ед.','Доля закупки ₽']]
 for r in rows:
  for room,n in r['room_qty'].items():roomdata.append([M.ROOM_NAMES[room],r['id'],r['name'],round(n,4),r['unit'],r['room_cost'][room]])
 csvfile('v1-room-takeoff.csv',roomdata)
 stages=[['Этап','Название','Товары ₽','Работы ₽','Прямые затраты ₽']]
 for id,name,*_ in M.STAGES:
  n=int(id);mat=sum(r['cost'] for r in rows if r['stage']==n);work=sum(r['cost'] for r in M.labor_rows() if r['stage']==n)
  ri=len(stages)+1
  stages.append([n,name,('formula',f'SUMIF(Закупки!C2:C{len(rows)+1},A{ri},Закупки!J2:J{len(rows)+1})',mat),work,('formula',f'C{ri}+D{ri}',mat+work)])
 roomsummary=[['Помещение','Товары ₽','Работы ₽','Логистика ₽','Резерв ₽','ИТОГО ₽']]+[[name,*[room_totals[room][k] for k in ('materials','labor','logistics','contingency','total')]] for room,name in M.ROOM_NAMES.items()]
 works=[['Этап','Работа','Объём','Ед.','Ставка ₽','Стоимость ₽']]+[[r['stage'],r['name'],r['qty'],r['unit'],r['rate'],r['cost']] for r in M.labor_rows()]
 sourcerows=[['Код','Магазин / страница','Ссылка','Найденный ценовой фрагмент','Проверено','Статус']]
 for r in rows:
  for s in src.get(r['id'],{}).get('links',[]):sourcerows.append([r['id'],s['label'],s['url'],s.get('price_excerpt','Не показан'),M.AS_OF,'Аналог/подборка, сверить параметры и комплектность'])
 assumptions=[['Параметр','Значение'],['Дата',M.AS_OF],['Бюджет','Практичный средний'],['Высота плита-плита','2,80 м — НЕ измерена; допущение 2,70+0,10'],['Пол / потолок','0,12 /0,04 м — допущение'],['Цена','Колонка I на листе Закупки — плановый допуск, не подтверждённая цена всех продавцов'],['Изменение','Редактировать E/F/G/I на листе Закупки; H/J/K и этапы пересчитываются'],['Комнаты','Доли и листы расхода экспортированы на дату расчёта. После изменения количеств перераспределить их новой сборкой; суммы комнат не динамические'],['Логистика','3,5% товаров; доставка, подъём, вывоз'],['Резерв','12% материалов+работ+логистики'],['Исключено','ИБП, бойлер, ТВ, робот, замена окон/радиаторов/входной двери, демонтаж отсутствующих стен'],['Источники','Открытые карточки/узкие каталоги, цену/остаток/регион/упаковку уточнять перед заказом']]
 totals=M.totals(rows)
 budget=[['Статья','Сумма ₽'],['Товары',('formula',f'SUM(Закупки!J2:J{len(rows)+1})',totals['materials'])],['Работы',totals['labor']],['Логистика',('formula','ROUND(B2*0.035,0)',totals['logistics'])],['Резерв',('formula','ROUND(SUM(B2:B4)*0.12,0)',totals['contingency'])],['ВСЕГО',('formula','SUM(B2:B5)',totals['total'])]]
 xlsx(dest/'v1-renovation.xlsx',[('Бюджет',budget),('Закупки',excel),('Этапы',stages),('Комнаты',roomsummary),('Расход комнат',roomdata),('Работы',works),('Работы комнат',[['Комната','Работа','Этап','Доля ₽','Основание']]+[[M.ROOM_NAMES[room],j['name'],j['stage'],cost,j['basis']] for j in room_work for room,cost in j['room_cost'].items()]),('Источники',sourcerows),('Допущения',assumptions)])
 payload={'date':M.AS_OF,'status':'preliminary','geometry':M.geometry(),'assumptions':dict(raw_height=M.RAW_HEIGHT,clear_height=M.CLEAR_HEIGHT,floor=M.FLOOR_HEIGHT,ceiling=M.CEILING_DROP),
 'totals':totals,'stages':M.STAGES,'items':rows,'labor':M.labor_rows(),'room_budget':room_totals,'room_labor':room_work,'sources':src}
 (dest/'v1-estimate.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
