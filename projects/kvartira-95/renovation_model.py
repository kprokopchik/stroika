"""Проверяемая предварительная ведомость В1. Все размеры/нормы вынесены в данные.

Никаких сетевых запросов при сборке сайта. Цены — бюджетные допуски, предложения
магазинов хранятся отдельно в procurement_sources.json. Перегородки не являются КЖ.
"""
from pathlib import Path
from collections import defaultdict, Counter
from decimal import Decimal, ROUND_HALF_UP
import csv, json, math, io
import importlib.util

ROOT=Path(__file__).resolve().parent
_layout_spec=importlib.util.spec_from_file_location('_quantity_layout95',ROOT/'layout.py')
quantity_layout=importlib.util.module_from_spec(_layout_spec)
_layout_spec.loader.exec_module(quantity_layout)
AS_OF='21.11.2026'
DEVELOPER_CLEAR_HEIGHT=2.70
DEVELOPER_FLOOR=.10    # неизвестно: допущение, не подтверждённая толщина застройщика
RAW_HEIGHT=DEVELOPER_CLEAR_HEIGHT+DEVELOPER_FLOOR
FLOOR_HEIGHT=.12
CEILING_DROP=.04
WALL_HEIGHT=RAW_HEIGHT
CLEAR_HEIGHT=round(RAW_HEIGHT-FLOOR_HEIGHT-CEILING_DROP,3)
STAGES=[
 ('0','Подготовка и обмер','1–2 недели','Обмер плиты/стояков, КЖ, раскладка мебели, защиты и заказ проекта; не демонтаж отсутствующих стен.'),
 ('1','Перегородки и закладные','2–3 недели','Разметка на плите → каркас → усиления. Вторую сторону закрывать после скрытых инженерных работ.'),
 ('2','Черновые инженерные сети','3–5 недель','Вода/канализация, щит, кабели, LAN, вентиляция и трассы кондиционеров; исполнительная съёмка до закрытия.'),
 ('3','Мокрые основания и гидроизоляция','3–5 недель с сушкой','Штукатурка бетона, отдельные минеральные полы санузлов, гидроизоляция и проверка герметичности.'),
 ('4','Сухой пол на лагах','1–2 недели','После сушки мокрых процессов: виброопоры, лаги, вата, два слоя фанеры. Перегородки уже стоят на плите.'),
 ('5','Окраска и плитка','3–4 недели','Подготовка/окраска стен, облицовка, кухонный фартук, тёплый пол только под свободными зонами.'),
 ('6','Чистовые устройства и двери','1–2 недели','Ламинат, плинтусы, двери, натяжной потолок, свет, механизмы розеток и выключателей; порядок согласовать по защите покрытий.'),
 ('7','Мебель, техника и пуск','2–4 недели','Монтаж кухни/шкафов, сантехники, машин и сети; испытания, маркировка, уборка и передача документации.'),
]
ROOM_NAMES={'spalnya':'Спальня родителей','detskaya-1':'Детская 1','detskaya-2':'Детская 2',
 'kuhnya-gostinaya':'Кухня-гостиная','prihozhaya':'Прихожая','sport':'Спорт-кладовая',
 'koridor':'Коридор','su-1':'Санузел у спален','su-2':'Санузел у входа','common':'Общеквартирное'}
# Нумерация floor в layout.v1(): не прямоугольники из object.py, а контуры чистого пола.
FLOOR_INDEX={'spalnya':[0],'detskaya-1':[1],'su-1':[2],'su-2':[3],
 'prihozhaya':[4,7],'koridor':[5],'kuhnya-gostinaya':[6],'sport':[8],'detskaya-2':[9]}
WINDOW_WIDTH={'spalnya':5.95,'detskaya-1':2.39,'detskaya-2':2.39,'kuhnya-gostinaya':2.40}
DOOR_WIDTH={'spalnya':.79,'detskaya-1':.88,'detskaya-2':.84,'su-1':.73,'su-2':.76,
 'sport':.80,'prihozhaya':.98+.76+.80+1.00,'koridor':.79+.88+.84+.73+1.10,'kuhnya-gostinaya':1.00}
# id, ось длина м (включая проём), проём м, помещение А/Б, мокрая обшивка, примечание.
PARTITIONS=[
 ('П01а',1.19,.79,'spalnya','koridor',False,'Спальня / коридор, дверной участок'),
 ('П01б',4.35,0,'spalnya','detskaya-1',False,'Спальня / детская1'),
 ('П02',3.52,.88,'detskaya-1','koridor',False,'Детская 1 / коридор'),
 ('П03',1.08,0,'detskaya-1','detskaya-2',False,'Тонкое продолжение у существующего массивного участка'),
 ('П04',5.67,0,'detskaya-2','kuhnya-gostinaya',False,'Детская 2 / кухня-гостиная'),
 ('П05',2.31,.73,'su-1','koridor',True,'Санузел 1 / коридор'),
 ('П06',1.83,0,'su-1','prihozhaya',True,'Санузел 1 / прихожая'),
 ('П07',2.42,0,'su-2','kuhnya-gostinaya',True,'Санузел 2 / кухня, включая участок рядом с шахтой'),
 ('П08',2.94,.76,'su-2','prihozhaya',True,'Санузел 2 / прихожая'),
 ('П09а',1.00,.84,'detskaya-2','prihozhaya',False,'Детская2 / проход прихожей'),
 ('П09б',2.02,0,'detskaya-2','sport',False,'Детская2 / спорт-кладовая'),
 ('П10',1.77,0,'sport','prihozhaya',False,'Северная стенка кладовой'),
 ('П11',2.12,.80,'sport','prihozhaya',False,'Западная стенка кладовой со сдвижной дверью'),
 ('П12',.36,0,'sport','kuhnya-gostinaya',False,'Южный короткий участок кладовой'),
 ('Ш01',3.00,0,'su-1','su-2',True,'Условный запас облицовок шахт 3 м; состав и объём после обмера, не вскрытие вентканала'),
]

def area(pts):
 return abs(sum(x*y2-x2*y for (x,y),(x2,y2) in zip(pts,pts[1:]+pts[:1])))/20000

def perimeter(pts):
 return sum(math.hypot(x-x2,y-y2) for (x,y),(x2,y2) in zip(pts,pts[1:]+pts[:1]))/100

def geometry():
 plan=quantity_layout.v1();floors=[i for i in plan.items if i['kind']=='floor']
 obstacles=[]
 for item in plan.items:
  if item['kind']=='wall':obstacles.append((item['x1'],item['y1'],item['x2'],item['y2']))
  elif item['kind']=='shaft':
   obstacles.append((item['x1'],item['y1'],item['x2'],item['y2']))
 def inside(x,y,pts):
  odd=False
  for (x1,y1),(x2,y2) in zip(pts,pts[1:]+pts[:1]):
   if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:odd=not odd
  return odd
 data={}
 for room,indices in FLOOR_INDEX.items():
  polygons=[floors[i]['pts'] for i in indices];vertices=[v for pts in polygons for v in pts]
  raw=sum(area(pts) for pts in polygons)
  xmin,xmax=min(x for x,y in vertices),max(x for x,y in vertices)
  ymin,ymax=min(y for x,y in vertices),max(y for x,y in vertices)
  obs=[o for o in obstacles if o[0]<xmax and o[2]>xmin and o[1]<ymax and o[3]>ymin]
  xs=sorted({x for x,y in vertices}|{max(xmin,min(xmax,x)) for o in obs for x in (o[0],o[2])})
  ys=sorted({y for x,y in vertices}|{max(ymin,min(ymax,y)) for o in obs for y in (o[1],o[3])})
  cells=set()
  for i,(a,b) in enumerate(zip(xs,xs[1:])):
   for j,(c,d) in enumerate(zip(ys,ys[1:])):
    x=(a+b)/2;y=(c+d)/2
    if any(inside(x,y,pts) for pts in polygons) and not any(a<=x<b and c<=y<d for a,c,b,d in obs):cells.add((i,j))
  net=0;edge=0
  for i,j in cells:
   w=xs[i+1]-xs[i];h=ys[j+1]-ys[j];net+=w*h
   edge+=h*((i-1,j) not in cells)+h*((i+1,j) not in cells)
   edge+=w*((i,j-1) not in cells)+w*((i,j+1) not in cells)
  a=net/10000;p=edge/100
  surface=max(0,p*CLEAR_HEIGHT-WINDOW_WIDTH.get(room,0)*1.60-DOOR_WIDTH[room]*2.10)
  data[room]={'area':a,'raw_area':raw,'deduction':raw-a,'perimeter':p,'wall':surface,'wet':room.startswith('su-')}
 return data

def specs():
 rows=[]
 for line in (ROOT/'procurement_specs.tsv').read_text().splitlines():
  if not line or line.startswith('#'):continue
  id,stage,name,unit,pack,price,query,note=line.split('|')
  rows.append(dict(id=id,stage=int(stage),name=name,unit=unit,pack=float(pack),price=int(price),query=query,note=note))
 return {r['id']:r for r in rows}

def takeoff(e):
 """Расход по помещениям; запас один раз перед общим округлением до упаковок."""
 geo=geometry(); q=defaultdict(lambda:defaultdict(float)); how={}; waste={}
 def add(id,room,n,rule,loss=0):
  if n>0:q[id][room]+=n
  how[id]=rule;waste[id]=loss
 dry=sum(x['area'] for x in geo.values() if not x['wet'])
 total=sum(x['area'] for x in geo.values())
 newfaces=defaultdict(float)
 for id,length,opening,a,b,wet,note in PARTITIONS:
  net=length*WALL_HEIGHT-opening*2.1
  for r in (a,b):newfaces[r]+=length*CLEAR_HEIGHT-opening*2.1
  add('stud',a,length/.6*WALL_HEIGHT/2,'Длина осей / 0,6 × высота; половина на каждую сторону',.12)
  add('stud',b,length/.6*WALL_HEIGHT/2,'Длина осей / 0,6 × высота; половина на каждую сторону',.12)
  for r in (a,b):
   add('track',r,length,'Верх и низ оси, деление стоимости между сторонами',.1)
   add('boardwet' if wet else 'board',r,2*net,'Два слоя на каждой стороне; проёмы вычтены',.12)
   add('wool',r,net/2,'Полная площадь полости перегородок, половина на сторону',.05)
   add('joint',r,net*.5,'0,5 кг на м² одной стороны, включая внутренние швы',.10)
   add('jointtape',r,length*2,'2 м на погонный метр оси каждой стороны, предварительно',.10)
   add('sealtape',r,length+WALL_HEIGHT,'Периметр каркаса 2L+2H, деление между сторонами',.10)
 for r,d in geo.items():
  a=d['area'];p=d['perimeter'];w=d['wall']
  # Новые обшивки считаются нетто после проёмов; остаток бетона — оценка по периметру.
  concrete=max(0,w-newfaces[r])
  if d['wet']:
   add('cementplaster',r,concrete*14,'Минеральные стены: 14 кг/м² при 10 мм',.10)
   add('screed',r,a*.07*1800,'Санузлы: 70 мм × 1800 кг/м³ сухой смеси, допущение',.10)
   waterproof=a+p*.20+(1.8+0.8)*2*2.0 if r=='su-1' else a+p*.20+(1.4+.9)*2*2.0
   add('waterproof',r,waterproof*1.5,'Пол + бортик 0,2 м + стены мокрых зон 2 м; 1,5 кг/м², зоны консервативно суммированы',.10)
   add('wptape',r,p+8,'Периметр и четыре вертикальных мокрых угла по 2 м',.10)
   add('wpcollar',r,7,'Семь проходок на санузел; уточнить по выводам')
   add('floortile',r,a,'Пол целиком, под оборудованием тоже',.10)
   add('walltile',r,w,'Развёртка стен до условной чистой высоты, проёмы вычтены',.12)
   add('tileglue',r,(a+w)*5,'5 кг/м² пола и стен',.10)
   add('grout',r,(a+w)*.35,'0,35 кг/м²; формат/шов уточнить',.10)
   add('silicone',r,4,'4 картриджа на санузел, предварительно')
  else:
   add('plaster',r,concrete*8.5,'8,5 кг/м² бетона при среднем слое 10 мм',.10)
   add('putty',r,w*1.8,'1,2 кг/м²/мм × 1,5 мм',.10)
   paintwall=w-(2.7 if r=='kuhnya-gostinaya' else 0)
   add('paint',r,paintwall*.24,'Два слоя по 0,12 л/м²; кухонный фартук вычтен',.10)
   add('floorboard',r,a/.4,'Шаг лаг 400 мм: 2,5 пог. м/м²',.10)
   add('vibro',r,a*3.2,'3,2 опоры/м² по инструкции Виброфлекс-LD, шаг лаг 400 мм',.05)
   add('plywood',r,a*2,'Два слоя фанеры 18 мм',.10)
   add('floorwool',r,a,'50 мм в межлаговом пространстве',.05)
   add('floortape',r,p,'Разделение по периметру каждого помещения',.10)
   add('floorglue',r,a*.25,'0,25 кг/м² пола между листами, уточнить по клею',.10)
   add('underlay',r,a,'Под ламинат, 2 мм по паспорту',.05)
   add('laminate',r,a,'Все сухие помещения, непрерывность/разрывы по паспорту',.08)
   add('skirting',r,max(0,p-DOOR_WIDTH[r]),'Периметр минус проёмы; встроенная мебель пока не вычтена',.10)
   add('skirtingglue',r,max(0,p-DOOR_WIDTH[r])/10,'Один картридж на 10 м, предварительно')
  add('concreteprimer',r,concrete*.35,'0,35 кг/м² плотного бетона',.05)
  add('primer',r,(w+a)*.2,'0,2 л/м² стен и пола, суммарный предварительный расход',.10)
  add('ceiling',r,a,'Контур комнаты; цена полотна, монтаж отдельно',.05)
  add('ceilingprofile',r,p,'Периметр натяжного потолка',.08)
  add('protection',r,a,'1 м² защитного материала на 1 м² квартиры',.10)
  add('bags',r,a*.7,'0,7 мешка/м² без демонтажа; уточнение по накоплению')
 # Общие пакеты и крепёж — явно, без второй скрытой процентной наценки.
 for id,n,rule in [('screws',5,'2 коробки25 мм +3 коробки35 мм по1000 шт; предварительно на весь объём обшивки'),('anchors',8,'800 креплений предварительно'),
 ('backing',6,'6 листов под кухню, шкафы, карнизы, сантехнику и спорт; схема закладных до зашивки'),
 ('floorscrew',4,'4000 саморезов предварительно')]:add(id,'common',n,rule)
 for r in ['spalnya','detskaya-1','detskaya-2','su-1','su-2']:
  add('ua',r,2,'Две усиленные стойки на дверной проём');add('uaangle',r,4,'Верх/низ двух усиленных стоек')
  add('door',r,1,'Один распашной блок');add('handle',r,1,'Один набор фурнитуры')
 add('slidingdoor','sport',1,'Одна накладная раздвижная дверь');add('handle','sport',1,'Ручка и направляющая фурнитура')
 # Вода: новые габаритные модули, плановые пути и 2,5 м вертикалей/концов на луч.
 for kind,dest,r,pts,node in e['PIPES']:
  length=e['pipe_len'](pts)
  add('pex16',r,length,'Плановая длина луча от нового модуля +2,5 м вертикалей/концов',.15)
  add('insulation',r,length,'По длине каждой водяной трубы, включая ГВС и ХВС',.10)
  add('fitting16',r,1,'13 начал лучей');add('elbow16',r,1,'13 концов лучей')
  add('sleeve16',r,2,'Два аксиальных соединения на луч')
 for r in ('su-1','su-2'):
  add('pex20',r,6 if r=='su-1' else 10,'Две магистрали: У1 по3 м, У2 по5 м, включая вертикали',.15)
  add('insulation22',r,6 if r=='su-1' else 10,'Изоляция магистралей, размер22 мм уточнить',.10)
  for id,n in [('fitting20',4),('sleeve20',4),('filter',2),('reducer',2),('pressuregauge',2),('checkvalve',2),('ballvalve',2),('union',6),('leakvalve',2),('servicecab',1),('cap',2)]:add(id,r,n,'По два независимых постучётных ввода на санузел; часть арматуры условная')
 add('manifold3','su-1',1,'У1 ГВС 2+1');add('manifold4','su-1',1,'У1 ХВС 3+1')
 add('manifold4','su-2',1,'У2 ГВС 3+1');add('manifold6','su-2',1,'У2 ХВС 5+1');add('manifoldjoin','su-2',1,'Стыковка двух 3-выходных модулей')
 add('leakcontroller','common',1,'Один контроллер на все четыре привода')
 for i,(r,x,y,where) in enumerate(e['LEAK'],1):add('leaksplit' if i==2 else 'leaksensor',r,1,'6 датчиков: 5 оконечных Эксперт +1 Классика-разветвитель')
 # Уникальные отрезки канализации в обоих направлениях, без повторной закупки общей трассы.
 intervals=defaultdict(list)
 for dest,dia,slope,pts in e['SEWER']:
  room='kuhnya-gostinaya' if 'Кухня' in dest else 'su-1' if 'С/у 1' in dest else 'su-2'
  for a,b in zip(pts,pts[1:]):
   vertical=a[0]==b[0];fixed=a[0] if vertical else a[1]
   lo,hi=sorted((a[1],b[1]) if vertical else (a[0],b[0]))
   intervals[(max(dia,50),vertical,fixed,room)].append((lo,hi))
 for (dia,vertical,fixed,room),spans in intervals.items():
  merged=[]
  for lo,hi in sorted(spans):
   if merged and lo<=merged[-1][1]:merged[-1][1]=max(hi,merged[-1][1])
   else:merged.append([lo,hi])
  length=sum(hi-lo for lo,hi in merged)/100
  add('sewer110' if dia==110 else 'sewer50',room,length,'Объединение коллинеарных перекрывающихся участков; вертикали/раструбы +20%',.20)
 for r in ('su-1','su-2'):
  for id,n in [('bend50',6),('tee50',2),('bend110',2),('cleanout',1),('pipeclamp',15),('wcframe',1),('wc',1),('basin',1),('basinmixer',1),('basinsiphon',1),('towel',1),('heatmat',1),('thermostat',1),('fan',1),('mirror',1)]:add(id,r,n,'По плану санузла; фасонные части предварительно')
 for id,n in [('bend50',4),('tee50',2),('cleanout',2),('pipeclamp',8),('sink',1),('sinkmixer',1),('sinksiphon',1),('machinevalve',1)]:add(id,'kuhnya-gostinaya',n,'Мойка и ПММ, доступный общий узел')
 for id in ('bath','bathdrain','bathmixer'):add(id,'su-1',1,'Один комплект по плану')
 for id in ('showerdrain','showergrate','showermixer','showerglass','machinevalve','laundrysiphon'):add(id,'su-2',1,'Один комплект по плану')
 add('backsplash','kuhnya-gostinaya',2.7,'4,36 м × 0,62 м, округлено',.10)
 add('tileglue','kuhnya-gostinaya',2.7*5,'Кухонный фартук, 5 кг/м²',.1);add('grout','kuhnya-gostinaya',2.7*.35,'Кухонный фартук, 0,35 кг/м²',.1)
 for r in ('su-1','su-2','kuhnya-gostinaya'):add('ventgrille',r,1,'Естественная вентиляция, наличие и размеры проверить')
 add('ventduct','kuhnya-gostinaya',3,'Трасса вытяжки 3 м — допущение',.10);add('ventbend','kuhnya-gostinaya',2,'Два поворота — допущение')
 for r in ('spalnya','kuhnya-gostinaya'):
  for id,n in [('ac',1),('acpipe',5),('acdrain',5),('acsiphon',1)]:add(id,r,n,'Два отдельных сплита, трасса каждого условно 5 м; по ОВиК')
 # Предварительные силовые трассы: щит (30;856), ортогонально через коридор.
 # Отдельные радиальные ответвления каждой розетки консервативны; перед закупкой заменить кабельным журналом.
 for p in e['EL']:
  r=p['room'];path=(abs(p['x']-30)+abs(p['y']-856))/100+2.0
  id='cable6' if p['g']==12 else 'cable25'
  add(id,r,path,'Ортогональная оценка от щита до КАЖДОЙ точки +2 м вертикалей/хвостов; без оптимизации шлейфов',.15)
  if p['t']=='floor':add('floorbox',r,1,'Лючок полого пола с 2 силовыми и 2 LAN-модулями');continue
  if p['t']=='sock':
   n=len(p['kinds']);add('socketwet' if r.startswith('su-') else 'socket',r,n,'По 39 силовым местам; два места лючка не дублировать')
   add('socketbox',r,n,'По числу механизмов');add('frame',r,n,'Бюджет на пост, блоки рамок после раскладки')
  elif p['code'] in ('ТП','ПС'):
   add('socketbox',r,1,'Под терморегулятор либо скрытое подключение полотенцесушителя; накладка в комплекте устройства')
  elif p['code'] not in ('Вар','Конд','ТП','ПС'):
   add('socketwet' if r.startswith('su-') else 'socket',r,1,'Розетка отдельного бытового прибора из ведомости EL')
   add('socketbox',r,1,'Под отдельный прибор');add('frame',r,1,'Бюджет на пост')
 for l in e['LT']:
  r=l['room'];kind=l['kind'];path=(abs(l['x']-30)+abs(l['y']-856))/100+2.0 if kind!='strip' else 8
  add('cable15',r,path,'Ортогональная оценка каждого светильника +2 м; без оптимизации шлейфов',.15)
  if kind in ('fan','mirror','strip'):continue
  id={'spot':'spot','ceiling':'ceilinglamp','sconce':'sconce','step':'step','motion':'motion','pendant':'pendant'}[kind]
  add('spot65' if kind=='spot' and r.startswith('su-') and ('ванн' in l['where'] or 'душ' in l['where']) else id,r,1,'По ведомости LT, IP по зоне')
  if kind in ('spot','ceiling','pendant','motion'):
   add('ceilingmount',r,1,'Закладная по потолочному прибору');add('ceilingring',r,1,'Термокольцо по прибору')
 for s in e['SW']:
  keys=[k for k,c in s['keys']];r=s['room']
  if keys==['norm','norm']:add('switch2',r,1,'Двухклавишный механизм по SW');n=1
  else:
   for k in keys:add({'norm':'switch1','pass':'passswitch','cross':'crossswitch'}[k],r,1,'По типам управления SW')
   n=len(keys)
  add('socketbox',r,n,'По числу механизмов выключателей');add('frame',r,n,'Бюджет на пост')
  add('cable15',r,5,'Предварительно 5 м на точку выключателя, проходные уточнить',.15)
 add('socket','prihozhaya',4,'Четыре обычные розетки QF8 в техсекции');add('socketbox','prihozhaya',4,'Техническая секция');add('frame','prihozhaya',4,'Техническая секция')
 for id,n in [('led',4.26),('ledprofile',4.26),('ledpsu',1)]:add(id,'kuhnya-gostinaya',n,'Подсветка 4,26 м по полилинии плана',.05 if id!='ledpsu' else 0)
 # Металлические трассы — выделенная сумма до точного рабочего проекта, а не обещанный комплект монтажных труб.
 add('steelpipe','common',160,'Предварительный лимит 160 м трасс возле дерева; по электропроекту',.10)
 add('steelbox','common',20,'20 доступных протяжных/ответвительных коробок предварительно')
 add('conduit','common',150,'Свет по минеральным основаниям, предварительно',.10)
 for id,n in [('panelbox',1),('rcd',4),('mcb16',10),('mcb10',1),('mcb10two',1),('mcb32',1),('mcb2',1),('isolator',1),('voltage',1),('priority',1),('contactor',1),('auxcontact',1),('buttons',1),('inputblock',2),('nbar',4),('pebar',1),('branchblock',2),('comb',2),('wirekit',1),('ferrules',1)]:add(id,'common',n,'Состав текущей 54-модульной схемы; точные серии/модели до закупки')
 # 10 обычных C16? В модели их 10: 4,5,8,9,11,13,14,15,18,20.
 for r,where,pts in e['PORTS']:
  add('cat6',r,e['lan_len'](pts,'потолке' in where),'По 12 трассам LAN с вертикалями и запасами функции lan_len',.15)
  add('dataconduit',r,e['lan_len'](pts,'потолке' in where),'Отдельная труба на каждую линию до разветвления, консервативно',.10)
  add('keystone',r,2,'Два конца каждой линии, два модуля в лючке вычитаются ниже')
  add('patchcord',r,1,'Панель → коммутатор: один на линию')
 q['keystone']['spalnya']-=2
 for r,x,y,d,n,h,where in e['LAN_PTS']:add('lanface',r,1,'По пяти настенным местам LAN')
 for r,x,y,id,reserve in e['APS']:
  add('apbox',r,1,'Сервисная коробка AP, включая резерв')
  if not reserve:add('ap',r,1,'Две активные AP');add('patchcord',r,1,'Короткое подключение AP')
 for r,n in [('spalnya',3),('detskaya-1',2),('detskaya-2',2),('kuhnya-gostinaya',2)]:add('roompatch',r,n,'9 пользовательских портов')
 for id,n in [('patchpanel',1),('switchpoe',1),('router',1),('nas',1),('hdd',2),('intercom',1),('powerstrip',1),('networkbracket',1),('duct',3),('firedetector',1),('patchcord',2)]:add(id,'common',n,'Общее оборудование технической секции, без ИБП')
 add('signalwire','common',110,'10 кабелей датчиков/приводов по отдельным трассам с хвостами; условно 110 м',.10)
 # Базовая мебель по плану. Метраж корпусной мебели — нормированный бюджет, не каталожный комплект.
 furniture={
 'spalnya':{'wardrobe':2.15,'bed180':1,'mattress180':1,'nightstand':2,'desk':1.4,'officechair':1,'commode':1,'armchair':1,'ottoman':1,'curtainrod':3,'curtains':3},
 'detskaya-1':{'wardrobe':2.08,'kidbed':1,'kidmattress':1,'shelfbed':1,'desk':2.0,'officechair':1,'bookcase':1,'wallshelf':4,'climbing':1,'mat':1,'rug':1,'curtainrod':1,'curtains':1},
 'detskaya-2':{'wardrobe':1.5,'kidbed':1,'kidmattress':1,'nightstand':1,'desk':1.8,'officechair':1,'bookcase':1,'beanbag':1,'wallbars':1,'rug':1,'curtainrod':1,'curtains':1},
 'prihozhaya':{'wardrobe':2.26,'techcase':1,'shoebench':1,'wallbars':1,'mat':1},
 'koridor':{'shallowwardrobe':2.14},
 'sport':{'bikehook':4,'storageshelf':1,'sporthook':4},
 'kuhnya-gostinaya':{'kitchenbase':3.76,'kitchenupper':3.16,'kitchentower':1,'worktop':4.36,'kitchenhardware':6,'diningtable':1,'chair':3,'bench':1,'sofa':1,'coffeetable':1,'tvstand':1,'rug':1,'fridge':1,'oven':1,'hob':1,'dishwasher':1,'microwave':1,'hood':1,'kettle':1,'coffee':1,'curtainrod':1,'curtains':1},
 'su-1':{'storageshelf':1},'su-2':{'washer':1,'dryer':1,'stackkit':1}}
 for r,items in furniture.items():
  for id,n in items.items():add(id,r,n,'Количество/длина из расстановки В1; корпусная мебель уточняется обмером',.10 if id=='worktop' else 0)
 catalog=specs();rows=[]
 for id,s in catalog.items():
  byroom=q[id];net=sum(byroom.values());demand=net*(1+waste.get(id,0));packs=(round(demand/s['pack'],3) if id in {'wardrobe','shallowwardrobe','desk','kitchenbase','kitchenupper','worktop'} else math.ceil(round(demand/s['pack'],9)))
  cost=round(packs*s['price']); allocations={}
  # Целые рубли методом наибольших остатков, точное равенство комнаты↔квартира.
  fractions=[]
  for r,n in byroom.items():
   x=cost*n/net if net else 0; allocations[r]=int(x);fractions.append((x-int(x),r))
  for _,r in sorted(fractions,reverse=True)[:cost-sum(allocations.values())]:allocations[r]+=1
  rows.append({**s,'net':net,'waste':waste.get(id,0),'demand':demand,'packs':packs,'buy':packs*s['pack'],
   'cost':cost,'room_qty':dict(byroom),'room_cost':allocations,'rule':how.get(id,'Не задано')})
 return rows

LABOR=[
 ('0','Обмер, рабочие схемы, технадзор (допуск)',1,'компл',140000),
 ('1','Каркасные перегородки с обшивкой',None,'м² перегородки',2600),
 ('2','Электрика: разводка, сборка щита и испытания',1,'компл',280000),
 ('2','Водопровод, канализация, узлы и испытания',1,'компл',210000),
 ('2','LAN, датчики, шкаф и измерения линий',1,'компл',70000),
 ('2','Два сплита: черновой/чистовой монтаж',2,'компл',25000),
 ('2','Вентиляция и подключения',1,'компл',25000),
 ('3','Штукатурка минеральных оснований',None,'м²',950),
 ('3','Полы санузлов и гидроизоляция',1,'компл',65000),
 ('4','Лаги, виброопоры, два слоя фанеры',None,'м² пола',2100),
 ('5','Шпаклёвка, шлифовка, окраска',None,'м² стен',1500),
 ('5','Облицовка стен/пола плиткой',None,'м²',2800),
 ('6','Натяжной потолок: монтаж/обводы',None,'м² потолка',700),
 ('6','Ламинат и плинтусы',None,'м² пола',950),
 ('6','Установка дверей',6,'шт',7500),
 ('7','Сборка мебели и подключение техники',1,'компл',140000),
 ('7','Монтаж сантехники, приёмка и уборка',1,'компл',85000),
]

def labor_rows():
 g=geometry();dry=sum(d['area'] for d in g.values() if not d['wet']);wet=sum(d['area'] for d in g.values() if d['wet']);walls=sum(d['wall'] for d in g.values() if not d['wet'])
 partition=sum(l*WALL_HEIGHT-o*2.1 for _,l,o,*_ in PARTITIONS)
 concrete=max(0,sum(d['wall'] for d in g.values())-partition*2)
 quantities={'м² перегородки':partition,'м²':concrete,'м² пола':dry,'м² стен':walls,'м² потолка':dry+wet}
 out=[]
 for stage,name,n,unit,rate in LABOR:
  qty=n if n is not None else (sum(d['wall'] for d in g.values() if d['wet'])+wet+2.7 if 'плиткой' in name else quantities[unit])
  out.append(dict(stage=int(stage),name=name,qty=round(qty,2),unit=unit,rate=rate,cost=round(qty*rate)))
 return out

def money(n):return f'{round(n):,}'.replace(',',' ')
def f(n,d=1):return f'{n:.{d}f}'.replace('.',',')

def totals(rows):
 materials=sum(r['cost'] for r in rows);labor=sum(r['cost'] for r in labor_rows())
 logistics=round(materials*.035) # доставка/подъём/вывоз отдельно, не расход материала
 contingency=round((materials+labor+logistics)*.12)
 return dict(materials=materials,labor=labor,logistics=logistics,contingency=contingency,total=materials+labor+logistics+contingency)

def apportion(cost,weights):
 total=sum(weights.values());out={k:int(cost*v/total) for k,v in weights.items() if v>0}
 fractions=sorted(((cost*v/total-out[k],k) for k,v in weights.items() if v>0),reverse=True)
 for _,k in fractions[:cost-sum(out.values())]:out[k]+=1
 return out

def room_budget(e,rows):
 """Распределение работ для планирования комнат; не отдельные оферты бригад."""
 g=geometry();areaweights={r:d['area'] for r,d in g.items()};dry={r:d['area'] for r,d in g.items() if not d['wet']}
 wall={r:d['wall'] for r,d in g.items() if not d['wet']};tile={r:d['wall']+d['area'] for r,d in g.items() if d['wet']};tile['kuhnya-gostinaya']=2.7
 byid={r['id']:r for r in rows};alloc=[]
 for job in labor_rows():
  name=job['name'];weights=areaweights;basis='Пропорционально площади пола'
  if job['stage']==0:weights={'common':1};basis='Общее обследование и проект'
  elif 'перегородки' in name:weights=byid['stud']['room_qty'];basis='Пропорционально расходу стоечного профиля'
  elif name.startswith('Электрика'):
   weights=Counter(p['room'] for p in e['EL']+e['LT']+e['SW']);weights['common']=sum(weights.values())/3;basis='Точки; 25% общей работы на щит и испытания'
  elif name.startswith('Водопровод'):weights=Counter(r for k,d,r,pts,n in e['PIPES']);basis='По числу 13 водяных лучей; узлы распределены между санузлами/кухней'
  elif name.startswith('LAN'):
   weights=Counter(r for r,w,pts in e['PORTS']);weights['common']=sum(weights.values());basis='Половина — общая секция и настройки, половина — по числу LAN-линий'
  elif 'сплита' in name:weights={'spalnya':1,'kuhnya-gostinaya':1};basis='По одному сплиту на помещение'
  elif name.startswith('Вентиляция'):weights={'su-1':1,'su-2':1,'kuhnya-gostinaya':1};basis='Три вентиляционные зоны'
  elif name.startswith('Штукатурка'):weights={r:v for id in ('plaster','cementplaster') for r,v in byid[id]['room_qty'].items()};basis='По расходу штукатурных смесей, предварительно'
  elif 'санузлов' in name:weights={r:d['area'] for r,d in g.items() if d['wet']};basis='Площади двух санузлов'
  elif name.startswith('Лаги') or name.startswith('Ламинат'):weights=dry;basis='Площадь сухого пола'
  elif name.startswith('Шпаклёвка'):weights=wall;basis='Площадь окрашиваемых стен'
  elif name.startswith('Облицовка'):weights=tile;basis='Площадь облицовки стен/полов и фартука'
  elif name.startswith('Установка дверей'):weights={r:1 for r in ('spalnya','detskaya-1','detskaya-2','su-1','su-2','sport')};basis='По одному дверному комплекту'
  elif name.startswith('Сборка мебели'):
   weights={r:sum(x['room_cost'].get(r,0) for x in rows if x['stage']==7) for r in g};basis='По стоимости мебели/оборудования этапа7'
  elif name.startswith('Монтаж сантехники'):weights={'su-1':4,'su-2':5,'kuhnya-gostinaya':2};basis='Условные доли сантехнических приборов/машин'
  alloc.append({**job,'basis':basis,'room_cost':apportion(job['cost'],weights)})
 result={r:{'materials':sum(x['room_cost'].get(r,0) for x in rows),'labor':sum(x['room_cost'].get(r,0) for x in alloc)} for r in ROOM_NAMES}
 t=totals(rows);weights={r:d['materials']+d['labor'] for r,d in result.items()}
 logistics=apportion(t['logistics'],weights);reserve=apportion(t['contingency'],weights)
 for r,d in result.items():
  d['logistics']=logistics[r];d['contingency']=reserve[r];d['total']=sum(d.values())
 return result,alloc
