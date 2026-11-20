"""Проверки читаемых листов щита: python3 projects/kvartira-95/test_panel_mount.py."""
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import eng
from panel_readable import circuit_pages, overview_svg, COL
from load_priority import CONTROLLED
from power_budget import scenario_rows


class ReadablePanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = circuit_pages(eng.GROUPS, eng.DEV, eng.PANEL_ROWS)

    def test_every_overview_button_has_a_circuit(self):
        ids = {p["id"] for p in self.pages}
        self.assertEqual(ids, {"inlet", "ups", "priority"} | {str(g) for g in eng.GROUPS})
        self.assertEqual(len(self.pages), len(ids))
        svg = ET.fromstring(overview_svg(eng.PANEL_ROWS, eng.DEV))
        triggers = [el.attrib["data-circuit"] for el in svg.iter() if "data-circuit" in el.attrib]
        self.assertTrue(set(triggers) <= ids)
        info_keys = {el.attrib["data-info"] for el in svg.iter() if "data-info" in el.attrib}
        self.assertTrue(info_keys <= set(eng.DEV))
        self.assertTrue({str(g) for g in eng.GROUPS} <= set(triggers))

    def test_group_addresses_and_backup_source(self):
        for g in eng.GROUPS:
            root = ET.fromstring(next(p["svg"] for p in self.pages if p["id"]==str(g)))
            labels = [el.text or "" for el in root.iter() if el.tag.endswith("text")]
            for pol in ("L","N","PE"):
                self.assertIn(f"X{g}.{pol}", labels)
            self.assertTrue(any(t.startswith(f"W{g} ·") for t in labels))
            self.assertIn("XPE",labels)
            if g==17:
                self.assertIn("SA.C.L",labels);self.assertIn("SA.C.N",labels)
                self.assertNotIn("XL",labels);self.assertNotIn("XN",labels)
            else:
                self.assertIn("XL",labels);self.assertIn("XN",labels)

    def test_group_wire_paths_stay_short_and_parallel(self):
        # У каждого группового листа только прямые вертикальные L/N/PE.
        # Это не позволяет незаметно вернуть обходы через другие рейки.
        for p in self.pages:
            if not p["id"].isdigit():continue
            paths = [el for el in ET.fromstring(p["svg"]).iter() if el.tag.endswith("polyline") and el.attrib.get("stroke") in COL.values()]
            switched = p["id"] in ("9", "15", "19")
            self.assertEqual(len(paths),12 if switched else 8)
            for path in paths:
                points = [tuple(map(float,s.split(','))) for s in path.attrib["points"].split()]
                self.assertEqual(len(points),2)
                if points[0][0] != points[1][0]:
                    self.assertTrue(switched)
                    self.assertEqual(path.attrib["stroke"],COL["L"])
                    self.assertLess(abs(points[0][0]-points[1][0]),20)
                self.assertLessEqual(abs(points[0][1]-points[1][1]),450)

    def test_consumer_lines_match_requested_separation(self):
        appl = {p["code"]:p["g"] for p in eng.EL if p["t"] == "appl"}
        for code,g in {"Хол":10,"СВЧ":9,"Выт":9,"Дух":11,"Вар":12,"Стир":14,"Суш":18}.items():
            self.assertEqual(appl[code],g)
        bath_sockets = [p for p in eng.EL if p["t"]=="sock" and p["room"].startswith("su-")]
        self.assertTrue(bath_sockets)
        self.assertTrue(all(p["g"]==15 for p in bath_sockets))
        self.assertEqual(set(CONTROLLED),{9,15,19,20,21})
        self.assertEqual([g for g,_ in sorted(CONTROLLED.items(),key=lambda item:item[1][1])],[15,19,20,21,9])
        for g in (10,11,12,13,14,16,17,18):
            self.assertNotIn(g,CONTROLLED)

    def test_panel_has_room_and_every_group_once(self):
        for row in eng.PANEL_ROWS:
            self.assertEqual(sum(eng.DEV[k][3] for k in row),18)
        self.assertEqual(len(eng.PANEL_ROWS),6)
        groups=[int(k) for row in eng.PANEL_ROWS for k in row if k.isdigit()]
        self.assertEqual(sorted(groups),list(range(1,22)))
        self.assertEqual(eng.DEV["free2"][3],10)

    def test_switched_lines_keep_neutrals_and_ac_supply_separate(self):
        for g,(actor,order,method,restore) in CONTROLLED.items():
            root=ET.fromstring(next(p["svg"] for p in self.pages if p["id"]==str(g)))
            labels=[el.text or "" for el in root.iter() if el.tag.endswith("text")]
            self.assertTrue(any(actor in t for t in labels))
            self.assertIn("XN",labels)
            self.assertIn(f"X{g}.N",labels)
            self.assertTrue(any("XC.N" in t for t in labels))
            if g in (20,21):
                self.assertIn("Питание L/N здесь не разрывается",labels)
            else:
                self.assertIn(actor,labels)

    def test_budget_accounts_for_two_machines_and_local_kitchen_limit(self):
        rows={r[0]:r for r in scenario_rows()}
        self.assertEqual(rows["Стирка + сушка + ПММ"][2],"7,8")
        self.assertEqual(rows["Варочная + три машины"][2],"11,3")
        self.assertIn("перегрузка QF9 C16",rows["Все нагреватели кухонных приборов"][4])
        self.assertEqual(rows["Все нагреватели кухонных приборов"][2],"5,75")

    def test_print_set_and_all_svg_are_valid(self):
        self.assertEqual([p["id"] for p in self.pages if p["print"]],["inlet","priority","1","9","15","20","ups"])
        for p in self.pages:ET.fromstring(p["svg"])


if __name__ == "__main__":
    unittest.main()
