"""Читаемая раскладка с адресами и отдельными листами подключений.

Адресные переходы обозначают электрическую связь, а не маршрут укладки.
Клеммы условные; обозначения L/N/PE сверяются по паспортам аппаратов.
"""
from html import escape

import eng_svg as S
from panel_wiring import ups_wiring_svg

INK = "#26363D"
COL = {"L": "#AD432D", "N": "#1879B5", "PE": "#287B48"}


class Sheet:
    def __init__(self, title, height=760, width=760):
        self.width, self.height = width, height
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">',
                      f'<rect width="{width}" height="{height}" fill="#FFFFFF"/>']

    def text(self, x, y, text, size=15, color=INK, anchor="middle", bold=False):
        self.parts.append(S.txt(x, y, text, fs=size, font=S.SANS, fill=color, anchor=anchor, weight=700 if bold else 500, halo=False))

    def box(self, x, y, w, h, label, fill="#F3F6F7", size=15):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="#BCC9CE" stroke-width="1.3"/>')
        self.text(x + w / 2, y + h / 2, label, size)

    def wire(self, pol, points, dot=False):
        self.parts.append(S.path(points, "#FFFFFF", sw=6))
        self.parts.append(S.path(points, COL[pol], sw=3))
        if pol == "PE":
            self.parts.append(S.path(points, "#E8CA35", sw=1.3, dash="6 4"))
        if dot:
            x, y = points[0]
            self.parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{COL[pol]}"/>')

    def pin(self, x, y, pol, label=None, above=False):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="5" fill="#FFFFFF" stroke="{COL[pol]}" stroke-width="2"/>')
        if label:
            self.text(x, y - 16 if above else y + 17, label, 12, COL[pol])

    def device(self, x, y, w, code, rating, label, circuit=None, h=146, pins=True):
        attrs = f' class="hit" data-info="{escape(code.removeprefix("QF"))}" data-circuit="{circuit}" tabindex="0" role="button" aria-label="Подключение {escape(code)}"' if circuit else ""
        self.parts.append(f'<g{attrs}><rect class="hit-box" x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#FFFFFF" stroke="#71848D" stroke-width="1.5"/>')
        self.text(x + w / 2, y + 30, code, 16, bold=True)
        self.text(x + w / 2, y + 52, rating, 12)
        self.parts.append(f'<rect x="{x+w/2-23}" y="{y+66}" width="46" height="20" rx="3" fill="{"#C27A29" if code == "SA" else "#386E91"}"/>')
        self.text(x + w / 2, y + 106, label, 12)
        if circuit and w >= 80:
            self.text(x + w / 2, y + 128, "открыть цепь", 10, "#55747F")
        self.parts.append('</g>')
        if pins:
            self.pin(x + w * .28, y + 5, "L")
            self.pin(x + w * .72, y + 5, "N")

    def end(self):
        return "".join(self.parts) + "</svg>"


def overview_svg(rows, devices):
    d = Sheet("Щит: расположение аппаратов и адреса подключений", 1120, 1160)
    left, module = 52, 56
    ys = (135, 370, 605, 860)
    d.text(580, 31, "Расположение аппаратов · 4 рейки по 18 модулей", 23, bold=True)
    d.text(580, 65, "Нажмите на аппарат: откроется только его цепь с проводами и клеммами", 16, "#526A74")
    d.parts.append('<rect x="28" y="98" width="1104" height="930" rx="12" fill="#FAFCFC" stroke="#A5B5BC" stroke-width="1.5"/>')
    names = {1:"Свет комнат",2:"Свет кухни",3:"Свет холла",4:"Спальня",5:"Детская 1",6:"Детская 2",7:"Холл",8:"Гостиная",9:"Столешница",10:"Холод./СВЧ",11:"Духовка",12:"Варочная",13:"ПММ",14:"Стир.-суш.",15:"Санузлы",16:"Вход ИБП",17:"Линия ИБП"}
    for ri, row in enumerate(rows):
        y, x = ys[ri], left
        d.text(1110, y + 70, str(ri + 1), 16, "#72858D", bold=True)
        d.parts.append(f'<rect x="{left}" y="{y+69}" width="1008" height="16" fill="#D7E0E4"/>')
        if ri in (1, 2):
            end = left + (18 if ri == 1 else 14) * module - 28
            for pol, yy in (("L", y - 24), ("N", y - 12)):
                d.wire(pol, [(left+28, yy), (end, yy)])
            d.text(left, y - 42, "XL / XN → входные гребёнки", 13, anchor="start", bold=True)
            if ri == 2:
                d.text(left+15*module, y-30, "SA.C → QF17", 13, "#A9691F", bold=True)
        for key in row:
            code, rating, label, mods, kind, title, _ = devices[key]
            w = mods * module
            if key.isdigit():
                g = int(key)
                d.device(x+3, y, w-6, "QF"+key, rating, names[g], circuit=key)
                if g != 17:
                    for pol, px, yy in (("L", x+3+(w-6)*.28, y-24), ("N", x+3+(w-6)*.72, y-12)):
                        d.wire(pol, [(px, yy), (px, y+5)])
                        d.pin(px,y+5,pol)
                d.box(x+10, y+158, w-20, 28, "→ X"+key, "#EDF4F7", 13)
            elif code:
                short = {"QS":"Ввод", "KV":"Напряжение", "F1":"FV", "FV":"УЗИП", "QD":"100 мА S", "SA":"ИБП / сеть"}[key]
                d.device(x+3,y,w-6,key,rating,short,circuit="ups" if key=="SA" else "inlet",pins=False)
            elif key == "free1":
                for i, name in enumerate(("X0.L", "X0.N", "XL", "XN")):
                    d.box(x+5,y+i*36,w-10,30,name,"#EAF2F5",13)
            elif key == "term":
                d.box(x+4,y,w-8,146,"", "#EDF4F7")
                d.text(x+w/2,y+26,"Выходные клеммы",16,bold=True)
                for j in range(17):
                    cx=x+35+(j%9)*58;cy=y+64+(j//9)*36
                    d.box(cx-24,cy-13,48,26,f"X{j+1}","#FFFFFF",12)
                d.text(x+w-36,y+115,"XU",13,"#A9691F",bold=True)
            else:
                d.box(x+4,y,w-8,146,"Резерв" if key.startswith("r") else "Запас",size=13)
            x += w
    d.box(53,1042,190,36,"XPE · общая PE", "#EFF7EE",15)
    d.text(267,1060,"Одинаковые адреса соединены: «→ X5» ведёт к клеммам X5.",15,anchor="start")
    d.text(580,1095,"Длинные провода между рейками заменены адресами. Порядок соединений — на выбранном листе ниже.",14,"#526A74")
    return d.end()


def group_svg(g, groups, devices, rows):
    name, protection, cable, _ = groups[g]
    rail = next(i+1 for i,row in enumerate(rows) if str(g) in row)
    d = Sheet(f"Подключение группы {g}",690)
    d.text(380,31,f"QF{g} · {devices[str(g)][2]}",20,bold=True)
    d.text(380,61,f"Рейка {rail} · {devices[str(g)][1]} · тип A",15,"#526A74")
    source = ("SA.C.L","SA.C.N") if g==17 else ("XL","XN")
    for pol,x,label in (("L",220,source[0]),("N",330,source[1]),("PE",580,"XPE")):
        d.box(x-48,102,96,38,label,"#EFF6F8",16)
        d.wire(pol,[(x,140),(x,200 if pol!="PE" else 468)])
    d.device(160,200,230,f"QF{g}",devices[str(g)][1],"Дифавтомат · тип A",h=176,pins=False)
    for pol,x in (("L",220),("N",330)):
        d.pin(x,200,pol,pol+" вход")
        d.pin(x,376,pol,pol+" выход",above=True)
        d.wire(pol,[(x,376),(x,468)])
    d.box(150,450,480,77,"", "#F0F4F5")
    for pol,x in (("L",220),("N",330),("PE",580)):
        d.pin(x,468,pol,f"X{g}.{pol}")
        d.wire(pol,[(x,527),(x,578)])
    d.box(150,578,480,48,f"W{g} · {cable}","#F8FAFA",16)
    d.text(380,650,"N этой линии не соединяется с выходами N других дифавтоматов.",14,bold=True)
    d.text(380,675,"L/N/PE — функциональные обозначения; заводские номера клемм уточняются по модели.",12,"#526A74")
    return d.end()


def inlet_svg():
    d = Sheet("Ввод: только связи вводных аппаратов",840)
    d.text(380,30,"Ввод · QS → KV → QD → XL / XN",20,bold=True)
    d.text(380,62,"Ответвление F1 / FV — отдельная ветвь. Это схема связей, не маршрут укладки проводов.",13,"#526A74")
    for pol,x in (("L",200),("N",265)):
        d.text(x,94,pol,16,COL[pol],bold=True)
        d.wire(pol,[(x,108),(x,135)])
    d.device(155,135,155,"QS","2P 63 А","Ввод",h=130,pins=False)
    for pol,x in (("L",200),("N",265)):
        d.pin(x,135,pol);d.pin(x,265,pol)
    d.device(155,335,155,"KV","63 А","Реле напряжения",h=130,pins=False)
    d.pin(200,335,"L");d.pin(265,335,"N");d.pin(200,465,"L")
    d.wire("L",[(200,265),(200,335)])
    d.wire("N",[(265,265),(265,310),(335,310),(335,515),(265,515),(265,540)])
    d.wire("N",[(265,310),(265,335)],dot=True)
    d.wire("L",[(200,290),(510,290),(510,335)],dot=True)
    d.wire("N",[(265,310),(600,310),(600,540)],dot=True)
    d.text(137,290,"X0.L",13,COL["L"])
    d.text(390,328,"X0.N",13,COL["N"])
    d.device(460,335,100,"F1","по FV","Защита FV",h=130,pins=False)
    d.pin(510,335,"L");d.pin(510,465,"L")
    d.device(155,540,155,"QD","63 А · 100 мА S","УЗО типа A",h=130,pins=False)
    d.device(455,540,190,"FV","T2 · 1P+N","УЗИП",h=130,pins=False)
    d.wire("L",[(200,465),(200,540)])
    d.wire("L",[(510,465),(510,540)])
    for pol,x in (("L",200),("N",265)):
        d.pin(x,540,pol);d.pin(x,670,pol)
        d.wire(pol,[(x,670),(x,735)])
        d.box(x-27,735,54,38,"XL" if pol=="L" else "XN","#EFF6F8",15)
    for pol,x in (("L",510),("N",600)):
        d.pin(x,540,pol,pol+" вход")
    d.wire("PE",[(550,670),(550,735)])
    d.pin(550,670,"PE")
    d.text(580,690,"PE",13,COL["PE"])
    d.box(500,735,100,38,"XPE","#EFF7EE",15)
    d.text(380,807,"N до QD — X0.N. N после QD — XN. С PE их не соединять.",14,bold=True)
    d.text(380,830,"Ввод 230 В, 50 А принят условно; F1/FV и защиту ИБП подтвердить до монтажа.",12,"#526A74")
    return d.end()


def circuit_pages(groups, devices, rows):
    pages = [{"id":"inlet","title":"Ввод, реле напряжения и УЗИП","svg":inlet_svg(),"print":True}]
    for g in groups:
        pages.append({"id":str(g),"title":f"QF{g} — {groups[g][0]}","svg":group_svg(g,groups,devices,rows),"print":g==1})
    pages.append({"id":"ups","title":"ИБП и переключатель SA","svg":ups_wiring_svg(),"print":True})
    return pages
