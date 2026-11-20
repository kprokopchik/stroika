"""Проверки читаемых листов щита: python3 projects/kvartira-95/test_panel_mount.py."""
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import eng
from panel_readable import circuit_pages, overview_svg, COL


class ReadablePanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = circuit_pages(eng.GROUPS, eng.DEV, eng.PANEL_ROWS)

    def test_every_overview_button_has_a_circuit(self):
        ids = {p["id"] for p in self.pages}
        self.assertEqual(ids, {"inlet", "ups"} | {str(g) for g in range(1,18)})
        self.assertEqual(len(self.pages), len(ids))
        svg = ET.fromstring(overview_svg(eng.PANEL_ROWS, eng.DEV))
        triggers = [el.attrib["data-circuit"] for el in svg.iter() if "data-circuit" in el.attrib]
        self.assertTrue(set(triggers) <= ids)
        self.assertTrue({str(g) for g in range(1,18)} <= set(triggers))

    def test_group_addresses_and_backup_source(self):
        for g in range(1,18):
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
            self.assertEqual(len(paths),8)
            for path in paths:
                points = [tuple(map(float,s.split(','))) for s in path.attrib["points"].split()]
                self.assertEqual(len(points),2)
                self.assertEqual(points[0][0],points[1][0])
                self.assertLessEqual(abs(points[0][1]-points[1][1]),330)

    def test_print_set_and_all_svg_are_valid(self):
        self.assertEqual([p["id"] for p in self.pages if p["print"]],["inlet","1","ups"])
        for p in self.pages:ET.fromstring(p["svg"])


if __name__ == "__main__":
    unittest.main()
