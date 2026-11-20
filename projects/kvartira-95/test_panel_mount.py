"""Проверка электрических связей и чтения проводов на монтажном рисунке.

Запуск: python3 projects/kvartira-95/test_panel_mount.py
"""
import math
from pathlib import Path
import sys
import unittest
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import eng
from panel_mount import Mount


class PanelConnections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mount = Mount(eng.PANEL_ROWS, eng.DEV)
        cls.mount.svg()
        cls.adj = defaultdict(set)
        for a, b, _ in cls.mount.links:
            cls.adj[a].add(b)
            cls.adj[b].add(a)

    def reachable(self, start):
        found, stack = {start}, [start]
        while stack:
            for other in self.adj[stack.pop()] - found:
                found.add(other)
                stack.append(other)
        return found

    def test_group_outputs_do_not_share_neutrals(self):
        for g in range(1, 18):
            for pol in ("L", "N"):
                with self.subTest(group=g, pole=pol):
                    network = self.reachable(f"{g}.{pol}вых")
                    self.assertIn(f"X{g}.{pol}", network)
                    self.assertIn(f"W{g}.{pol}", network)
                    self.assertFalse(network & {"XL.in", "XN.in", "XPE.in"})
                    for other in range(1, 18):
                        if other != g:
                            self.assertNotIn(f"{other}.{pol}вых", network)

    def test_backup_group_is_not_on_mains_comb(self):
        for g in range(1, 17):
            self.assertIn(f"{g}.Lвх", self.reachable("XL.in"))
            self.assertIn(f"{g}.Nвх", self.reachable("XN.in"))
        for pol, bus in (("L", "XL.in"), ("N", "XN.in")):
            self.assertNotIn(f"17.{pol}вх", self.reachable(bus))
            self.assertIn(f"17.{pol}вх", self.reachable(f"SA.C.{pol}"))
            self.assertIn(f"SA.I.{pol}", self.reachable(f"WU.{pol}"))
            self.assertIn(f"SA.II.{pol}", self.reachable(bus))

    def test_protective_earth_is_continuous(self):
        network = self.reachable("Ввод.PE")
        for g in range(1, 18):
            self.assertIn(f"W{g}.PE", network)
        for pin in ("FV.PE", "XU.PE", "WU.PE"):
            self.assertIn(pin, network)
        self.assertFalse(network & {"XN.in", "X0.N.in"})

    def test_no_wire_touches_an_unrelated_contact(self):
        # Иначе винт/точка создаёт ложное соединение на рисунке, даже если
        # логическая таблица сетей верна. Кружок контакта имеет радиус 6.
        for a, b, net, points in self.mount.routes:
            for pin, (x, y, other_net) in self.mount.ports.items():
                if other_net == net:
                    continue
                for (x1, y1), (x2, y2) in zip(points, points[1:]):
                    dx, dy = x2 - x1, y2 - y1
                    t = max(0, min(1, ((x-x1)*dx + (y-y1)*dy) / (dx*dx + dy*dy))) if dx or dy else 0
                    distance = math.hypot(x - x1 - t*dx, y - y1 - t*dy)
                    self.assertGreaterEqual(distance, 6, (a, b, pin))


if __name__ == "__main__":
    unittest.main()
