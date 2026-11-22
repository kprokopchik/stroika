"""Проверки бюджета и междисциплинарных связей, которые легко сломать при правке."""
import json,unittest,xml.etree.ElementTree as ET,zipfile
from pathlib import Path
import eng
import renovation_model as M
from renovation_docs import sources_data
from export_renovation import write_exports
import renovation_steps as S

class Renovation(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=M.takeoff(vars(eng));cls.byid={r['id']:r for r in cls.rows};cls.rooms,cls.work=M.room_budget(vars(eng),cls.rows)
 def test_geometry_excludes_shaft_and_pylons(self):
  g=M.geometry()
  self.assertAlmostEqual(sum(d['raw_area'] for d in g.values()),95.5924)
  self.assertAlmostEqual(sum(d['area'] for d in g.values()),95.0989)
  self.assertAlmostEqual(g['su-1']['deduction'],.212)
  self.assertAlmostEqual(g['spalnya']['deduction'],.2815)
 def test_every_catalog_item_has_quantity_and_two_sources(self):
  sources=sources_data();self.assertEqual(len(self.rows),223)
  for r in self.rows:
   self.assertGreater(r['packs'],0,r['id']);self.assertGreater(r['cost'],0,r['id'])
   links=sources[r['id']]['links'];self.assertTrue(2<=len(links)<=3,r['id'])
   self.assertEqual(len({s['url'] for s in links}),len(links),r['id'])
   self.assertFalse(any('integration.vs' in s['url'] for s in links),r['id'])
 def test_pack_rounding_and_room_allocations(self):
  for r in self.rows:
   self.assertGreaterEqual(r['buy']+1e-7,r['demand'],r['id'])
   self.assertEqual(sum(r['room_cost'].values()),r['cost'],r['id'])
   self.assertAlmostEqual(sum(r['room_qty'].values()),r['net'])
  self.assertEqual(self.byid['cat6']['packs'],1)
  self.assertEqual(self.byid['cat6']['buy'],305)
 def test_stage_room_grand_totals_reconcile(self):
  t=M.totals(self.rows)
  for key in t:self.assertEqual(sum(r[key] for r in self.rooms.values()),t[key],key)
  self.assertEqual(sum(sum(j['room_cost'].values()) for j in self.work),t['labor'])
  self.assertEqual(sum(sum(r['cost'] for r in self.rows if r['stage']==s) for s in range(8)),t['materials'])
 def test_no_double_purchase_of_packaged_devices(self):
  for id,n in [('mcb16',10),('rcd',4),('leaksensor',5),('leaksplit',1),('leakvalve',4),('floorbox',1),('keystone',22),('patchcord',16),('roompatch',9),('ap',2),('nas',1),('hdd',2),('chair',3),('washer',1),('dryer',1),('heatmat',2),('spot65',2)]:self.assertEqual(self.byid[id]['net'],n,id)
  self.assertFalse(any('ИБП' in r['name'] or 'бойлер' in r['name'].lower() for r in self.rows))
  self.assertAlmostEqual(self.byid['wardrobe']['net'],7.99)
 def test_collectors_match_live_rays_and_reserve(self):
  from collections import Counter
  n=Counter((node,kind) for kind,dest,r,pts,node in eng.PIPES)
  self.assertEqual(n,{('У1','c'):3,('У1','h'):2,('У2','c'):5,('У2','h'):3})
  self.assertEqual(3+4+4+6-len(eng.PIPES),4)
 def test_sewer_endpoints_and_slope(self):
  risers={(x,y) for name,x,y in eng.RISERS_K}
  for dest,dia,slope,pts in eng.SEWER:
   self.assertIn(tuple(pts[-1]),risers,dest)
   self.assertEqual(slope,2 if dia==110 else 3,dest)
  # Общая вертикаль ванна/раковина не должна закупаться второй раз.
  self.assertAlmostEqual(self.byid['sewer50']['net'],8.385)
 def test_ap_uses_actual_poe_ports(self):
  from low_voltage_docs import build
  doc=build(vars(eng));porttable=doc['extras']['porty']['blocks'][0][3]
  self.assertEqual(len({r[3] for r in porttable}),12)
  for row in porttable:
   if row[4]=='PoE':self.assertIn(row[3],['SW01','SW02'])
 def test_exports_read_and_formula_cache_matches(self):
  write_exports(self.rows,sources_data(),self.rooms,self.work)
  with zipfile.ZipFile(M.ROOT/'downloads/v1-renovation.xlsx') as z:
   self.assertIsNone(z.testzip())
   for name in z.namelist():ET.fromstring(z.read(name))
   ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
   root=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
   cell=root.find('.//s:c[@r="B6"]/s:v',ns)
   self.assertEqual(int(cell.text),M.totals(self.rows)['total'])
  data=json.loads((M.ROOT/'downloads/v1-estimate.json').read_text())
  self.assertEqual(data['totals'],M.totals(self.rows))

 def test_step_budget_and_room_costs_reconcile(self):
  plan=S.build_plan(self.rows,self.rooms,self.work)
  self.assertEqual(len(plan['steps']),40)
  previous=0
  for s in plan['steps']:
   self.assertEqual(s['cash'],s['materials']+s['labor']+s['logistics'])
   self.assertEqual(s['total'],s['cash']+s['contingency'])
   self.assertEqual(s['cumulative'],previous+s['total']);previous=s['cumulative']
  self.assertEqual(previous,M.totals(self.rows)['total'])
  for key in ('materials','labor','logistics','contingency','total'):
   self.assertEqual(sum(x[key] for x in S.stage_totals(plan).values()),M.totals(self.rows)[key])
  for room,budget in self.rooms.items():
   for key in ('materials','labor'):
    self.assertEqual(sum(s['room_cost'].get(room,{}).get(key,0) for s in plan['steps']),budget[key],(room,key))

 def test_orders_and_rounded_packs_are_not_purchased_twice(self):
  plan=S.build_plan(self.rows,self.rooms,self.work)
  for item in self.rows:
   payments=[p for s in plan['steps'] for p in s['purchases'] if p['item_id']==item['id']]
   self.assertAlmostEqual(sum(p['packs'] for p in payments),item['packs'],msg=item['id'])
   self.assertAlmostEqual(sum(p['buy'] for p in payments),item['buy'],msg=item['id'])
   self.assertEqual(sum(p['cost'] for p in payments),item['cost'],item['id'])
   if item['id'] in S.ADVANCE_IDS:
    self.assertEqual([p['kind'] for p in payments],['Аванс 50%','Доплата 50%'])
    self.assertEqual(payments[1]['packs'],0)
    self.assertEqual(payments[0]['cost'],(item['cost']+1)//2)
   if item['id'] in S.PARTY_IDS:
    self.assertTrue(all(float(p['packs']).is_integer() for p in payments))

 def test_construction_gates_precede_covering_and_wood(self):
  plan=S.build_plan(self.rows,self.rooms,self.work)
  order={s['id']:s['order'] for s in plan['steps']}
  for before,after in [('2.06','1.03'),('3.04','5.01'),('5.01','3.05'),('5.03','3.05'),
                       ('3.05','4.01'),('4.01','4.02'),('4.02','4.03'),
                       ('7.01','7.02'),('7.02','5.04'),('7.08','7.09'),('7.10','7.11')]:
   self.assertLess(order[before],order[after],(before,after))
  for s in plan['steps']:
   for dependency in s['after']:self.assertLess(order[dependency],order[s['id']])
   for id in s['stock']:self.assertLess(order[plan['items'][id]['first']],s['order'])

 def test_step_workbook_and_csv_keep_the_financial_totals(self):
  import csv
  write_exports(self.rows,sources_data(),self.rooms,self.work)
  ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
  with zipfile.ZipFile(M.ROOT/'downloads/v1-renovation.xlsx') as z:
   book=ET.fromstring(z.read('xl/workbook.xml'))
   names=[s.attrib['name'] for s in book.find('s:sheets',ns)]
   for name in ('Шаги','Покупки шагов','Работы шагов'):self.assertIn(name,names)
   root=ET.fromstring(z.read(f'xl/worksheets/sheet{names.index("Шаги")+1}.xml'))
   cached=lambda address:float(root.find(f'.//s:c[@r="{address}"]/s:v',ns).text)
   self.assertEqual(cached('M41'),M.totals(self.rows)['total'])
   self.assertEqual(sum(cached('F'+str(n)) for n in range(2,42)),M.totals(self.rows)['materials'])
   self.assertEqual(sum(cached('G'+str(n)) for n in range(2,42)),M.totals(self.rows)['labor'])
   self.assertEqual(sum(cached('H'+str(n)) for n in range(2,42)),M.totals(self.rows)['logistics'])
   self.assertEqual(sum(cached('I'+str(n)) for n in range(2,42)),M.totals(self.rows)['contingency'])
  with (M.ROOT/'downloads/v1-steps.csv').open(encoding='utf-8-sig',newline='') as fp:steps=list(csv.DictReader(fp,delimiter=';'))
  self.assertEqual(len(steps),40)
  self.assertEqual(int(steps[-1]['Лимит накопленно ₽']),M.totals(self.rows)['total'])

if __name__=='__main__':unittest.main()
