"""Проверки согласованности схемы, планов и бюджета упрощённого щита."""
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import eng
from panel_model import BANKS, BANK_OF, CONTROLLED_IDS, BRANCHES
from electrical_docs import PAGES
from panel_readable import circuit_pages, overview_svg, bank_svg, priority_svg
from panel_wiring import terminal_rows
from load_priority import CONTROLLED
from power_budget import scenario_rows, LOADS


class SimplifiedPanel(unittest.TestCase):
    def test_all_plan_points_use_active_groups(self):
        self.assertEqual(len(eng.GROUPS), 13)
        for point in eng.EL + eng.SW + eng.LT:
            self.assertIn(point['g'], eng.GROUPS)
            self.assertNotIn('ups', point.get('kinds', []))
        for code, group in {'ТП':15, 'ПС':15, 'Конд':20, 'Хол':8, 'СВЧ':9, 'Выт':9, 'Стир':14, 'Суш':18}.items():
            points = [p for p in eng.EL if p.get('code') == code]
            self.assertTrue(points, code)
            self.assertEqual({p['g'] for p in points}, {group})
        self.assertEqual({p['g'] for p in eng.LT}, {1, 3})
        self.assertNotEqual(BANK_OF[1], BANK_OF[3])

    def test_rcd_groups_partition_lines_and_controlled_bank(self):
        all_groups = [g for _, groups, _, _ in BANKS.values() for g in groups]
        self.assertCountEqual(all_groups, eng.GROUPS)
        self.assertEqual(len(all_groups), len(set(all_groups)))
        self.assertEqual(len({b[2] for b in BANKS.values()}), len(BANKS))
        self.assertEqual(set(BANKS['QD4'][1]), set(CONTROLLED_IDS))
        self.assertEqual(set(CONTROLLED), {9, 15, 20})
        self.assertEqual({(v[0], v[1]) for v in CONTROLLED.values()}, {('KM1', 1)})
        for g in (1,3,4,5,8,11,12,13,14,18):
            self.assertNotIn(g, CONTROLLED)

    def test_every_panel_button_opens_existing_sheet(self):
        pages = circuit_pages()
        ids = {p['id'] for p in pages}
        self.assertEqual(len(ids), len(pages))
        root = ET.fromstring(overview_svg())
        for node in root.iter():
            if 'data-circuit' in node.attrib:
                self.assertIn(node.attrib['data-circuit'], ids)
                self.assertIn(node.attrib['data-info'], eng.DEV)
        for page in pages:
            ET.fromstring(page['svg'])

    def test_cable_conductors_and_correct_neutral_bank(self):
        rows = terminal_rows()
        self.assertEqual(len(rows), len(eng.GROUPS) + 1)
        for g in eng.GROUPS:
            svg = bank_svg(BANK_OF[g])
            root = ET.fromstring(svg)
            labels = {n.text for n in root.iter() if n.tag.endswith('text')}
            for pol in ('L','N','PE'):
                self.assertIn(f'W{g}.{pol}', labels)
            neutral = BANKS[BANK_OF[g]][2]
            self.assertIn(neutral, labels)
            row = next(r for r in rows if r[0].startswith(f'QF{g} /'))
            self.assertIn(neutral, row[2])
            self.assertIn(f'W{g}.PE', row[3])
            if g in BRANCHES:
                self.assertIn(f'X{g}.L', row[1])
            else:
                self.assertNotIn(f'X{g}.L', row[1])
        light = next(r for r in rows if r[0].startswith('QF3 /'))
        self.assertIn('QF3.N', light[2])
        self.assertEqual(eng.DEV['3'][3], 2)

    def test_all_rails_fit_and_no_consumer_is_duplicated(self):
        self.assertEqual(len(eng.PANEL_ROWS), 3)
        for row in eng.PANEL_ROWS:
            self.assertEqual(sum(eng.DEV[k][3] for k in row), 18)
        consumers = [int(k) for row in eng.PANEL_ROWS for k in row if k.isdigit()]
        self.assertCountEqual(consumers, eng.GROUPS)
        for removed in ('16','17','19','21','QD','SA','PM','KM2','KM5','KA3','KA4'):
            self.assertNotIn(removed, eng.DEV)
        self.assertIn('r1', eng.DEV)
        self.assertNotIn('term', eng.DEV)
        self.assertEqual({k for k in eng.DEV if k.startswith('X')}, {'XD','X15','X20'})

    def test_whole_project_builds_without_obsolete_source(self):
        data = eng.build(1)
        self.assertEqual(list(data['elektrika']['extras']), [p['id'] for p in PAGES])
        self.assertTrue(data['elektrika']['hide_plan'])
        text = repr(data)
        self.assertNotRegex(text, r'LiFePO4|АКБ|DO[1-5]|SA\.C|KM5|KA3|KA4')
        # В новых разделах есть явное пояснение «без ИБП»; проверяем состав, а не запрет слова.
        self.assertFalse(any('ИБП' in str(value) for value in eng.DEV.values()))
        self.assertEqual(eng.build(2), {})
        self.assertIn('N4S', priority_svg())
        self.assertIn('KM1a', priority_svg())
        self.assertIn('XC.N', priority_svg())

    def test_separate_power_and_lighting_plans(self):
        power=eng.el_overlay('power')
        light=eng.el_overlay('light')
        self.assertNotIn('lyr-light', power)
        self.assertNotIn('lyr-links', power)
        self.assertIn('lyr-light', light)
        self.assertIn('lyr-links', light)
        self.assertLess(len(light),len(eng.el_overlay()))

    def test_branch_cable_names_are_unique(self):
        from panel_readable import branch_svg
        names=[name for branches in BRANCHES.values() for name,_ in branches]
        self.assertEqual(len(names),8)
        self.assertEqual(len(names),len(set(names)))
        root=ET.fromstring(branch_svg())
        self.assertEqual(len({n.text for n in root.iter() if n.tag.endswith('text') and n.text and n.text.startswith('W15.')}),6)

    def test_load_budget_keeps_two_machines_and_local_overload(self):
        rows = {r[0]:r for r in scenario_rows()}
        self.assertEqual(rows['Стирка + сушка + ПММ'][2], '7,8')
        self.assertEqual(rows['Варочная + три машины'][2], '11,3')
        self.assertEqual(rows['Все нагреватели кухонных приборов'][2], '5,75')
        self.assertIn('перегрузка QF9 C16', rows['Все нагреватели кухонных приборов'][4])
        self.assertNotIn('charge', {r[0] for r in LOADS})
        by_id = {r[0]:r for r in LOADS}
        self.assertEqual(by_id['floor'][2], '15')
        self.assertEqual(by_id['ac_living'][2], '20')
        self.assertEqual(by_id['network'][2], '8')


if __name__ == '__main__':
    unittest.main()
