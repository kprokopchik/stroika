"""Проверки бюджета и междисциплинарных связей, которые легко сломать при правке."""
import json,unittest,xml.etree.ElementTree as ET,zipfile
from pathlib import Path
import eng
import renovation_model as M
from renovation_docs import sources_data
from export_renovation import write_exports

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

if __name__=='__main__':unittest.main()
