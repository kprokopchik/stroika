"""Монтажный вид: проводники на лицевой раскладке аппаратов 4×18.

Контакты функциональные: реальная нумерация и расположение зависят от модели.
У каждой внешней связи есть два именованных конца и электрическая сеть;
это позволяет проверять изоляцию выходных нейтралей и питание группы 17.
"""
from html import escape

import eng_svg as S

COLORS = {"L": "#A53B27", "N": "#1479BE", "PE": "#227A42"}
M = 48
LEFT = 320
ROW_Y = (240, 650, 1060, 1560)
HEIGHT = 180
WIDTH = 1480
BOTTOM = 1905


class Mount:
    def __init__(self, rows, devices):
        self.rows, self.devices = rows, devices
        self.ports, self.links, self.positions, self.routes = {}, [], {}, []
        self.body, self.wires, self.labels = [], [], []
        for ri, row in enumerate(rows):
            x = LEFT
            for key in row:
                self.positions[key] = (x, ROW_Y[ri], devices[key][3] * M)
                x += devices[key][3] * M
            assert x == LEFT + 18 * M

    def text(self, x, y, value, size=12, fill="#243238", anchor="middle", weight=500, target=None):
        (self.labels if target is None else target).append(S.txt(x, y, value, fs=size, fill=fill, font=S.SANS, anchor=anchor, weight=weight, halo=False))

    def port(self, key, x, y, net, label=None, label_y=None):
        assert key not in self.ports, key
        self.ports[key] = (x, y, net)
        net_type = "PE" if net == "PE" else net[0]
        col = COLORS[net_type]
        self.labels.append(f'<g data-port="{escape(key)}" data-net="{net}"><title>{escape(key)}</title>'
                           f'<circle cx="{x}" cy="{y}" r="6" fill="#FFFFFF" stroke="{col}" stroke-width="1.6"/>'
                           f'<circle cx="{x}" cy="{y}" r="2" fill="{col}"/></g>')
        if label:
            self.text(x, label_y if label_y is not None else y + 17, label, 10, col)

    def connect(self, a, b, bends=(), layer="feeds", label=None):
        ax, ay, net = self.ports[a]
        bx, by, other = self.ports[b]
        assert net == other, (a, b, net, other)
        points = [(ax, ay), *bends, (bx, by)]
        self.links.append((a, b, net))
        self.routes.append((a, b, net, points))
        col = COLORS["PE" if net == "PE" else net[0]]
        # Белая подложка делает пересечение без точки видимым как переход.
        attrs = f'class="lyr lyr-{layer}" data-from="{escape(a)}" data-to="{escape(b)}" data-net="{net}"'
        self.wires.append(f'<g {attrs}><title>{escape(a)} → {escape(b)}</title>'
                          + S.path(points, "#FFFFFF", sw=5.8) + S.path(points, col, sw=2.6)
                          + (S.path(points, "#E9C72D", sw=1.25, dash="7 5") if net == "PE" else "") + '</g>')
        if label:
            x, y = points[len(points) // 2]
            self.text(x + 10, y - 10, label, 10, col, anchor="start")

    def panel_device(self, key):
        x, y, w = self.positions[key]
        code, rating, label, mods, kind, title, _ = self.devices[key]
        fill = "#FFF2DF" if kind == "ups" else "#FFFFFF"
        target = self.body
        target.append(f'<g class="hit" data-info="{key}" tabindex="0" role="button" aria-label="{escape(title)}">'
                      f'<rect class="hit-box" x="{x+2}" y="{y}" width="{w-4}" height="{HEIGHT}" rx="5" fill="{fill}" stroke="#63727B" stroke-width="1.7"/>')
        for k in range(1, mods):
            target.append(S.line(x + k * M, y + 44, x + k * M, y + 142, "#DCE2E5", sw=.7))
        self.text(x + w / 2, y + 49, "QF" + code if key.isdigit() else code, 15 if mods > 1 else 11, weight=700, target=target)
        self.text(x + w / 2, y + 68, rating, 11 if mods > 1 else 8, target=target)
        handle_w = min(w - 16, 62)
        handle_col = "#E58520" if kind == "ups" else ("#2465A5" if kind == "rcd" else "#343E45")
        target.append(f'<rect x="{x+(w-handle_w)/2}" y="{y+82}" width="{handle_w}" height="24" rx="3" fill="{handle_col}"/>'
                      f'<rect x="{x+(w-handle_w)/2+4}" y="{y+85}" width="{handle_w-8}" height="6" rx="2" fill="#FFFFFF" opacity=".2"/>')
        words, lines, current = label.split(), [], ""
        limit = max(5, int(w / 7))
        for word in words:
            if current and len(current) + len(word) + 1 > limit:
                lines.append(current)
                current = word
            else:
                current = (current + " " + word).strip()
        if current:
            lines.append(current)
        for i, line in enumerate(lines[:2]):
            self.text(x + w / 2, y + 122 + i * 14, line, 11 if mods > 1 else 8, target=target)
        target.append('</g>')

    def contact(self, dev, name, net, offset, bottom=False, label=None):
        x, y, _ = self.positions[dev]
        py = y + HEIGHT - 10 if bottom else y + 10
        self.port(dev + "." + name, x + offset, py, net, label or name, py - 16 if bottom else py + 17)

    def service(self, a, b, lane):
        """Петля из нижнего контакта в верхний по левому монтажному полю."""
        ax, ay, _ = self.ports[a]
        bx, by, _ = self.ports[b]
        side = 70 + lane * 12
        low = 445 + lane * 8
        high = 225 - lane * 8
        self.connect(a, b, [(ax, low), (side, low), (side, high), (bx, high)])

    def build(self):
        # Лицевые модули сохраняют уже принятую раскладку 4×18.
        for row in self.rows:
            for key in row:
                if self.devices[key][0]:
                    self.panel_device(key)
                elif key.startswith("r") or key == "free2":
                    x, y, w = self.positions[key]
                    self.body.append(f'<rect x="{x+3}" y="{y}" width="{w-6}" height="180" rx="5" fill="#FAFBFC" stroke="#ADB8BF" stroke-dasharray="7 5"/>')
                    self.text(x + w / 2, y + 75, "Резерв" if key.startswith("r") else "Запас", 12, target=self.body)
                    self.text(x + w / 2, y + 96, key.upper() if key.startswith("r") else "2 модуля", 11, target=self.body)

        # Контакты вводной части: имена функциональные, а не заводские номера.
        for name, net, offset, bottom in (("Lвх", "L_in", 24, False), ("Nвх", "N_in", 72, False),
                                          ("Lвых", "L0", 24, True), ("Nвых", "N0", 72, True)):
            self.contact("QS", name, net, offset, bottom)
        for name, net, off, bottom in (("Lвх", "L0", 24, False), ("N", "N0", 72, False), ("Lвых", "Lkv", 120, True)):
            self.contact("KV", name, net, off, bottom)
        self.contact("F1", "Lвх", "L0", 24)
        self.contact("F1", "Lвых", "Lfv", 24, True)
        self.contact("FV", "L", "Lfv", 24)
        self.contact("FV", "N", "N0", 72)
        self.contact("FV", "PE", "PE", 48, True)
        for name, net, off, bottom in (("Lвх", "Lkv", 24, False), ("Nвх", "N0", 72, False),
                                      ("Lвых", "Lgrid", 24, True), ("Nвых", "Ngrid", 72, True)):
            self.contact("QD", name, net, off, bottom)
        for name, net, off, bottom in (("I.L", "Lups", 24, False), ("I.N", "Nups", 72, False),
                                      ("II.L", "Lgrid", 120, False), ("II.N", "Ngrid", 168, False),
                                      ("C.L", "Lreserve", 48, True), ("C.N", "Nreserve", 144, True)):
            self.contact("SA", name, net, off, bottom)

        x, y, _ = self.positions["free1"]
        for i, (name, net) in enumerate((("X0.L", "L0"), ("X0.N", "N0"), ("XL", "Lgrid"), ("XN", "Ngrid"))):
            bx = x + i * M
            self.body.append(f'<rect x="{bx+2}" y="{y}" width="44" height="180" rx="4" fill="#F1F5F7" stroke="#6C7A82"/>')
            self.text(bx + 24, y + 77, name, 12, weight=700, target=self.body)
            self.text(bx + 24, y + 100, "≥63 A", 10, target=self.body)
            self.port(name + ".in", bx + 24, y + 10, net, "вх")
            for j, off in enumerate((12, 24, 36), 1):
                self.port(name + f".{j}", bx + off, y + 170, net)
            # Внутри распределительного блока все контакты одной сети соединены.
            for j in (1, 2, 3):
                self.links.append((name + ".in", name + f".{j}", net))

        # Ввод до QS и защитная шина справа от реек.
        for key, px, net in (("Ввод.L", 344, "L_in"), ("Ввод.N", 392, "N_in")):
            self.port(key, px, 95, net, key.rsplit(".", 1)[1], 80)
            self.connect(key, "QS." + ("Lвх" if net == "L_in" else "Nвх"))
        self.body.append('<rect x="1380" y="248" width="40" height="270" rx="5" fill="#EEF7EA" stroke="#227A42" stroke-width="2"/>')
        self.text(1400, 230, "XPE", 15, weight=700, fill=COLORS["PE"])
        for name, yy in (("in", 268), ("FV", 358), ("groups", 498)):
            self.port("XPE." + name, 1400, yy, "PE")
        self.links.extend([("XPE.in", "XPE.FV", "PE"), ("XPE.in", "XPE.groups", "PE")])
        self.port("Ввод.PE", 440, 95, "PE", "PE", 80)
        self.connect("Ввод.PE", "XPE.in", [(440, 95), (1400, 95)], layer="pe")
        self.connect("FV.PE", "XPE.FV", [(656, 590), (1350, 590), (1350, 358)], layer="pe")
        self.text(344, 116, "От этажного щита: QF0 50 А · 230 В", 14, anchor="start", weight=700)

        for lane, pair in enumerate((("QS.Lвых", "X0.L.in"), ("QS.Nвых", "X0.N.in"),
                                      ("X0.L.1", "KV.Lвх"), ("X0.L.2", "F1.Lвх"),
                                      ("X0.N.1", "KV.N"), ("X0.N.2", "QD.Nвх"),
                                      ("X0.N.3", "FV.N"), ("KV.Lвых", "QD.Lвх"),
                                      ("F1.Lвых", "FV.L"), ("QD.Lвых", "XL.in"),
                                      ("QD.Nвых", "XN.in"), ("XL.3", "SA.II.L"), ("XN.3", "SA.II.N"))):
            self.service(*pair, lane)

        # Две пары входных гребёнок. Группа 17 в гребёнку НЕ включена.
        for ri, groups in ((1, range(1, 10)), (2, range(10, 17))):
            yy = ROW_Y[ri]
            for polarity, dy, source in (("L", 44, "XL"), ("N", 26, "XN")):
                net = polarity + "grid"
                bus = f"B{ri}.{polarity}"
                first = LEFT + (24 if polarity == "L" else 72)
                self.port(bus, first, yy - dy, net)
                last = self.positions[str(max(groups))][0] + (24 if polarity == "L" else 72)
                self.wires.append(f'<g class="lyr lyr-feeds"><title>Входная гребёнка {bus}</title>'
                                  + S.line(first, yy - dy, last, yy - dy, COLORS[polarity], sw=5) + '</g>')
                sx, sy, _ = self.ports[source + f".{ri}"]
                side = 1240 if polarity == "L" else 1260
                lead_y = 550 if polarity == "L" else 568
                self.connect(source + f".{ri}", bus, [(sx, lead_y), (side, lead_y), (side, yy - dy)])
                self.text(LEFT + 20, yy - dy - 13, f"{bus} · {polarity} · входы гр. {min(groups)}–{max(groups)}", 11, COLORS[polarity], anchor="start")
                for g in groups:
                    px, _, _ = self.positions[str(g)]
                    pinx = px + (24 if polarity == "L" else 72)
                    tap = f"B{ri}.{polarity}.{g}"
                    self.port(tap, pinx, yy - dy, net)
                    self.links.append((bus, tap, net))
                    self.contact(str(g), polarity + "вх", net, 24 if polarity == "L" else 72)
                    self.connect(tap, str(g) + "." + polarity + "вх")

        for polarity, off, src, side, yy in (("L", 24, "SA.C.L", 1300, 1012), ("N", 72, "SA.C.N", 1320, 1032)):
            self.contact("17", polarity + "вх", polarity + "reserve", off)
            sx, sy, _ = self.ports[src]
            target = "17." + polarity + "вх"
            tx, ty, _ = self.ports[target]
            lead_y = 560 if polarity == "L" else 578
            self.connect(src, target, [(sx, lead_y), (side, lead_y), (side, yy), (tx, yy)], layer="ups")
        self.text(1040, 990, "QF17: только SA.C", 11, "#B96613", weight=700)

        # Выходы всех групп — отдельные пары проводов до подписанных клемм.
        term_x, term_y, _ = self.positions["term"]
        for g in range(1, 18):
            tx = term_x + (g - 1) * 26
            self.body.append(f'<rect x="{tx+1}" y="{term_y}" width="24" height="112" rx="2" fill="#F4F6F7" stroke="#78868E"/>')
            self.text(tx + 13, term_y + 40, f"X{g}", 10, weight=700, target=self.body)
            for polarity, off in (("L", 6), ("N", 20)):
                net = f"{polarity}{g}"
                pin = f"X{g}.{polarity}"
                self.port(pin, tx + off, term_y + 10, net, polarity)
                self.contact(str(g), polarity + "вых", net, 24 if polarity == "L" else 72, True)
                a = str(g) + "." + polarity + "вых"
                ax, ay, _ = self.ports[a]
                lane = (g - 1) if g <= 9 else g - 10
                near = ay + 24 + lane * 14 + (0 if polarity == "L" else 6)
                side = 72 + g * 9 + (0 if polarity == "L" else 4)
                low = 1426 + g * 6 + (0 if polarity == "L" else 3)
                self.connect(a, pin, [(ax, near), (side, near), (side, low), (tx + off, low)], layer="outputs")
                self.port(f"W{g}.{polarity}", tx + off, 1780, net)
                self.connect(pin, f"W{g}.{polarity}", layer="outputs")
            self.port(f"X{g}.PE", tx + 13, term_y + 85, "PE")
            self.port(f"PE.{g}", tx + 13, 1720, "PE")
            self.connect(f"PE.{g}", f"X{g}.PE", layer="pe")
            self.port(f"W{g}.PE", tx + 13, 1780, "PE")
            self.connect(f"X{g}.PE", f"W{g}.PE", layer="pe")
            self.text(tx + 13, 1802, f"W{g}", 10, weight=700)
        self.port("PE.bus", 1400, 1720, "PE")
        self.connect("XPE.groups", "PE.bus", layer="pe")
        # Общая только PE; индивидуальные N проходят через гребёнку PE без соединения.
        for g in range(1, 18):
            self.connect("PE.bus", f"PE.{g}", layer="pe")

        # Возврат выхода ИБП: отдельные клеммы XU, далее к входу I SA.
        ux = term_x + 17 * 26
        self.body.append(f'<rect x="{ux+1}" y="{term_y}" width="36" height="112" rx="3" fill="#FFF0DD" stroke="#B66D20"/>')
        self.text(ux + 19, term_y + 40, "XU", 11, weight=700, target=self.body)
        for pol, off, side, top, label in (("L", 9, 1340, 105, "SA.I.L"), ("N", 29, 1360, 117, "SA.I.N")):
            pin = "XU." + pol
            self.port(pin, ux + off, term_y + 10, pol + "ups")
            tx, ty, _ = self.ports[label]
            self.connect(pin, label, [(ux + off, 1538 if pol == "L" else 1550), (side, 1538 if pol == "L" else 1550), (side, top), (tx, top)], layer="ups")
            self.port("WU." + pol, ux + off, 1780, pol + "ups")
            self.connect("WU." + pol, pin, layer="ups")
        self.port("XU.PE", ux + 19, term_y + 85, "PE")
        self.port("PE.U", ux + 19, 1720, "PE")
        self.connect("PE.bus", "PE.U", layer="pe")
        self.connect("PE.U", "XU.PE", layer="pe")
        self.port("WU.PE", ux + 19, 1780, "PE")
        self.connect("XU.PE", "WU.PE", layer="pe")
        self.text(ux + 19, 1802, "WU", 11, fill="#B66D13", weight=700)

    def svg(self):
        self.build()
        frame = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {BOTTOM}" role="img" aria-label="Монтажный вид щита: провода на раскладке аппаратов">',
                 f'<rect width="{WIDTH}" height="{BOTTOM}" fill="#FFFFFF"/>',
                 '<rect x="40" y="65" width="1404" height="1685" rx="14" fill="#F9FAFB" stroke="#576671" stroke-width="2"/>']
        for ri, yy in enumerate(ROW_Y):
            frame.append(f'<rect x="310" y="{yy+76}" width="880" height="22" fill="#C8D0D5" stroke="#9AA9B1"/>')
            self.text(1208, yy + 120, f"Рейка {ri+1}", 12, anchor="start")
        self.text(740, 25, "Щит 72 модуля · провода на лицевой раскладке", 22, weight=700)
        self.text(740, 54, "Условные контакты L/N/PE: заводские номера и расположение сверить с выбранными аппаратами", 14)
        self.text(300, 1835, "L — коричневый; N — синий; PE — жёлто-зелёный. Пересечения без точки не соединены.", 14, anchor="start")
        self.text(300, 1859, "W16 → вход ИБП. WU ← выход ИБП. QF17 питается только через SA; его нейтраль отдельная.", 14, anchor="start")
        self.text(300, 1883, "Сеть 230 В, 50 А — допущение. Защиту ИБП на батарее и комплектацию УЗИП подтвердить до монтажа.", 13, anchor="start")
        # Корпуса перекрывают участки внутренних соединений, винты остаются поверх проводов.
        return "".join(frame + self.wires + self.body + self.labels) + "</svg>"


def mounting_svg(rows, devices):
    return Mount(rows, devices).svg()
