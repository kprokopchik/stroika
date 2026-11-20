"""Читаемая раскладка с адресами и отдельными листами подключений.

Адресные переходы обозначают электрическую связь, а не маршрут укладки.
Клеммы условные; обозначения L/N/PE сверяются по паспортам аппаратов.
"""
from html import escape

import eng_svg as S
from panel_wiring import ups_wiring_svg
from load_priority import CONTROLLED

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
        attrs = f' class="hit" data-info="{escape(code[2:] if code.startswith("QF") and code[2:].isdigit() else code)}" data-circuit="{circuit}" tabindex="0" role="button" aria-label="Подключение {escape(code)}"' if circuit else ""
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
    d = Sheet("Щит: аппараты, реле приоритета и адреса подключений", 1590, 1160)
    left, module = 52, 56
    d.text(580, 31, "Расположение аппаратов · 6 реек по 18 модулей", 23, bold=True)
    d.text(580, 65, "Нажмите аппарат: откроется одна цепь. KP / KM / KA — лист разгрузки.", 16, "#526A74")
    d.parts.append('<rect x="28" y="98" width="1104" height="1410" rx="12" fill="#FAFCFC" stroke="#A5B5BC" stroke-width="1.5"/>')
    for ri, row in enumerate(rows):
        y, x = 135 + ri * 230, left
        d.text(1110, y + 70, str(ri + 1), 16, "#72858D", bold=True)
        d.parts.append(f'<rect x="{left}" y="{y+69}" width="1008" height="16" fill="#D7E0E4"/>')
        group_keys = [key for key in row if key.isdigit() and key != "17"]
        if group_keys:
            end = left + sum(devices[k][3] for k in row[:row.index(group_keys[-1])+1]) * module - 28
            for pol, yy in (("L", y - 24), ("N", y - 12)):
                d.wire(pol, [(left+28, yy), (end, yy)])
            d.text(left, y - 42, "XL / XN → входы групп", 13, anchor="start", bold=True)
        for key in row:
            code, rating, label, mods, kind, title, _ = devices[key]
            w = mods * module
            if key.isdigit():
                g = int(key)
                d.device(x+3, y, w-6, "QF"+key, rating, label, circuit=key)
                if g != 17:
                    for pol, px, yy in (("L", x+3+(w-6)*.28, y-24), ("N", x+3+(w-6)*.72, y-12)):
                        d.wire(pol, [(px, yy), (px, y+5)])
                        d.pin(px,y+5,pol)
                else:
                    d.text(x+w/2,y-38,"SA.C → QF17",12,"#A9691F",bold=True)
                actor = CONTROLLED[g][0] if g in CONTROLLED else None
                address = (actor + " → " if actor and actor.startswith("KM") else "→ ") + "X"+key
                d.box(x+7, y+158, w-14, 28, address, "#FFF1DE" if actor else "#EDF4F7", 12)
            elif code:
                control = key in ("KP", "PM", "QFC", "KA3", "KA4", "KM1", "KM2", "KM5")
                short = {"QS":"Ввод", "KV":"Напряжение", "F1":"FV", "FV":"УЗИП", "QD":"100 мА S", "SA":"ИБП / сеть"}.get(key, label)
                d.device(x+3,y,w-6,key,rating,short,circuit="priority" if control else ("ups" if key=="SA" else "inlet"),pins=False)
                if key == "KP":
                    d.text(x+w/2,y+164,"DO1 с/у → DO2 полы → DO3/4 кондиционеры → DO5 кухня",15,bold=True)
                elif key.startswith("KM") or key.startswith("KA"):
                    d.text(x+w/2,y+166,"KP.DO"+key[-1],12,"#A9691F",bold=True)
            elif key == "free1":
                for i, name in enumerate(("X0.L", "X0.N", "XL", "XN")):
                    d.box(x+5,y+i*36,w-10,30,name,"#EAF2F5",13)
            elif key == "term":
                d.box(x+4,y,w-8,146,"", "#EDF4F7")
                d.text(x+w/2,y+23,"Выходные клеммы · изолированные N каждой группы",14,bold=True)
                for j in range(21):
                    cx=x+45+(j%7)*82;cy=y+54+(j//7)*33
                    d.box(cx-29,cy-12,58,24,f"X{j+1}","#FFFFFF",12)
                d.text(x+w-38,y+125,"XU",12,"#A9691F",bold=True)
            else:
                d.box(x+4,y,w-8,146,"Резерв бойлера" if key.startswith("r") else "Запас 10 модулей",size=12)
            x += w
    d.box(53,1528,190,36,"XPE · общая PE", "#EFF7EE",15)
    d.text(267,1547,"→ Xg — адрес клемм. TA1 — на вводной фазе после QS.",15,anchor="start")
    d.text(580,1580,"108 модулей — предварительно: габариты аппаратов, клемм и корпуса проверить до закупки.",14,"#526A74")
    return d.end()


def group_svg(g, groups, devices, rows):
    name, protection, cable, _ = groups[g]
    rail = next(i+1 for i,row in enumerate(rows) if str(g) in row)
    ctrl = CONTROLLED.get(g)
    switched = ctrl and ctrl[2] == "силовой контакт L"
    ac = ctrl and not switched
    d = Sheet(f"Подключение группы {g}",880)
    d.text(380,31,f"QF{g} · {devices[str(g)][2]}",20,bold=True)
    d.text(380,61,f"Рейка {rail} · {devices[str(g)][1]} · тип A",15,"#526A74")
    source = ("SA.C.L","SA.C.N") if g==17 else ("XL","XN")
    for pol,x,label in (("L",220,source[0]),("N",330,source[1]),("PE",700,"XPE")):
        d.box(x-48,102,96,38,label,"#EFF6F8",16)
        d.wire(pol,[(x,140),(x,200 if pol!="PE" else 588)])
    d.device(160,200,230,f"QF{g}",devices[str(g)][1],"Дифавтомат · тип A",h=176,pins=False)
    for pol,x in (("L",220),("N",330)):
        d.pin(x,200,pol,pol+" вход")
        d.pin(x,376,pol,pol+" выход",above=True)
    if switched:
        actor, order, method, restore = ctrl
        d.wire("L",[(220,376),(220,427)])
        d.box(160,427,120,100,"", "#FFF1DE")
        d.text(185,450,actor,16,bold=True)
        # Нормально разомкнутый силовой контакт в фазе этой группы.
        d.wire("L",[(220,427),(220,465)])
        d.wire("L",[(220,494),(220,527)])
        d.wire("L",[(220,494),(236,469)])
        d.pin(220,465,"L");d.pin(220,494,"L")
        d.wire("L",[(220,527),(220,588)])
        d.box(412,432,240,84,"", "#F2F5F7")
        d.text(532,454,f"KP.DO{order} → {actor}.A1",14,bold=True)
        d.text(532,481,f"{actor}.A2 → XC.N",14)
        d.text(532,504,"Катушка от QFC; свой N",12)
        d.text(400,550,f"Ступень {order} · возврат вручную" if g in (9,15) else f"Ступень {order} · возврат автоматически",14,bold=True,anchor="start")
    else:
        d.wire("L",[(220,376),(220,588)])
        if ac:
            actor, order, method, restore = ctrl
            d.box(414,414,278,127,"", "#FFF1DE")
            d.text(553,438,f"KP.DO{order} → {actor}",15,bold=True)
            d.text(553,463,"Изолированный сухой контакт",13)
            d.text(553,486,"→ вход разрешения кондиционера",12)
            d.text(553,512,"Питание L/N здесь не разрывается",12,bold=True)
            d.text(380,782,"Остановка и повторный пуск через вход / адаптер по паспорту модели.",13)
    d.wire("N",[(330,376),(330,588)])
    d.box(150,570,600,77,"", "#F0F4F5")
    for pol,x in (("L",220),("N",330),("PE",700)):
        d.pin(x,588,pol,f"X{g}.{pol}")
        d.wire(pol,[(x,647),(x,698)])
    d.box(150,698,600,48,f"W{g} · {cable}","#F8FAFA",16)
    if g in (9,15):
        d.text(380,782,"C16: около 3,7 кВт на всю линию при 230 В. Все мощные приборы вместе не включать.",12,bold=True)
    elif g in (14,18):
        d.text(380,782,"QF14 — стиральная; QF18 — сушильная. Две розетки, два кабеля; без разгрузки.",12,bold=True)
    d.text(380,826,"N этой линии не соединяется с выходами N других дифавтоматов или XC.N.",13,bold=True)
    d.text(380,856,"L/N/PE и контакты — функциональные обозначения; заводские клеммы уточняются по модели.",12,"#526A74")
    return d.end()


def priority_svg():
    d = Sheet("Разгрузка: измерение, реле приоритета и исполнительные цепи",1120,1040)
    d.text(520,30,"KP · пять ступеней разгрузки",23,bold=True)
    d.text(520,62,"Силовые цепи — на листах групп. Здесь показано управление и адреса проводов.",15,"#526A74")
    d.box(40,98,280,70,"", "#EFF6F8")
    d.text(180,121,"TA1 · только L после QS",15,bold=True)
    d.text(180,149,"До X0.L, KV и всех ответвлений",13)
    d.box(400,98,260,70,"", "#EFF6F8")
    d.text(530,121,"PM · общие P и I",16,bold=True)
    d.text(530,149,"Измерительный вход от TA1",13)
    d.parts.append(S.path([(320,132),(400,132)],"#6D6E89",sw=2,dash="5 4"))
    d.box(40,212,280,90,"", "#EFF6F8")
    d.text(180,239,"XL / XN → QFC",16,bold=True)
    d.text(180,265,"C2 · 30 мА A → XC.L / XC.N",13)
    d.text(180,288,"Питание KP, PM и катушек",13)
    d.box(400,212,600,104,"", "#FFF1DE")
    d.text(700,239,"KP · программируемое реле приоритета",18,bold=True)
    d.text(700,267,"PM ↔ KP: RS-485 A / B / COM",15)
    d.text(700,294,"SB1 → DI1 · SB5 → DI5 · общий входов по паспорту",13)
    d.parts.append(S.path([(530,168),(530,212)],"#6D6E89",sw=2,dash="5 4"))
    d.parts.append(S.path([(320,258),(400,258)],"#6D6E89",sw=2))
    labels={15:("Санузлы", "L: QF15 → KM1 → X15.L", "SB1: ручное разрешение"),19:("Тёплые полы", "L: QF19 → KM2 → X19.L", "Автоматический возврат"),20:("Кондиционер спальни", "KA3 → вход разрешения AC20", "Пауза повторного пуска по модели"),21:("Кондиционер гостиной", "KA4 → вход разрешения AC21", "Пауза повторного пуска по модели"),9:("Вся кухонная линия", "L: QF9 → KM5 → X9.L", "SB5: ручное разрешение")}
    for g,(actor,order,method,restore) in CONTROLLED.items():
        y=366+(order-1)*115
        d.box(40,y,124,76,f"KP.DO{order}","#FFF1DE",16)
        d.box(260,y,160,76,"", "#FFF1DE")
        d.text(340,y+24,actor,17,bold=True)
        d.text(340,y+48,"A1: от DO"+str(order),13)
        d.text(340,y+67,"A2: XC.N",13)
        d.wire("L",[(164,y+38),(260,y+38)])
        title, path, back=labels[g]
        d.box(510,y,490,76,"", "#F3F6F7")
        d.text(755,y+20,f"{order}. {title}",16,bold=True)
        d.text(755,y+43,path,14)
        d.text(755,y+65,back,12)
        # Только адресная связь: катушка и силовой/сухой контакт гальванически разделены.
        d.parts.append(S.path([(420,y+38),(510,y+38)],"#6D6E89",sw=2,dash="5 4"))
    d.text(520,1008,"DO — коммутируемая XC.L для катушек, не выход силового питания потребителей.",14,bold=True)
    d.text(520,1038,"KA3/KA4: контакты изолированы от катушки и сети; разомкнуто = запрет работы кондиционера.",13)
    d.text(520,1068,"После каждой ступени — повторное измерение. Возврат по одному с запасом и выдержкой.",14)
    d.text(520,1098,"Модели, заводские клеммы, программа KP и уставки уточняются до монтажа.",13,"#526A74")
    return d.end()


def inlet_svg():
    d = Sheet("Ввод: только связи вводных аппаратов",840)
    d.text(380,30,"Ввод · QS → KV → QD → XL / XN",20,bold=True)
    d.text(380,62,"Ответвление F1 / FV — отдельная ветвь. Это схема связей, не маршрут укладки проводов.",13,"#526A74")
    for pol,x in (("L",200),("N",265)):
        d.text(x,94,pol,16,COL[pol],bold=True)
        d.wire(pol,[(x,108),(x,135)])
    d.parts.append('<circle cx="200" cy="278" r="7" fill="none" stroke="#6D6E89" stroke-width="2"/>')
    d.text(109,275,"TA1 → PM",12,"#6D6E89")
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
    d.text(380,830,"Выделено 10 кВт; 1ф 230 В / 50 А условно. F1/FV и защиту ИБП подтвердить.",12,"#526A74")
    return d.end()


def circuit_pages(groups, devices, rows):
    pages = [{"id":"inlet","title":"Ввод, реле напряжения и УЗИП","svg":inlet_svg(),"print":True},
             {"id":"priority","title":"KP: реле приоритета и пять ступеней разгрузки","svg":priority_svg(),"print":True}]
    for g in groups:
        pages.append({"id":str(g),"title":f"QF{g} — {groups[g][0]}","svg":group_svg(g,groups,devices,rows),"print":g in (1,9,15,20)})
    pages.append({"id":"ups","title":"ИБП и переключатель SA","svg":ups_wiring_svg(),"print":True})
    return pages
