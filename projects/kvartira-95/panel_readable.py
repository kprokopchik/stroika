"""Векторные схемы щита: обзор, монтажный вид, четыре блока и управление.

Все соединения функциональные; заводские номера клемм назначаются после
выбора аппаратов. Цветная точка означает соединение, пересечение без точки — нет.
"""
from html import escape
from textwrap import wrap
import eng_svg as S
from panel_model import BANKS, BANK_OF, GROUPS, SHORT, DEV, PANEL_ROWS, FEED_KIND, BRANCHES, device_type

INK = "#233945"
COL = {"L": "#AD432D", "N": "#167CB5", "PE": "#34874F"}


class Sheet:
    def __init__(self, title, height=900, width=1280):
        self.width, self.height = width, height
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">', f'<rect width="{width}" height="{height}" fill="#FFFFFF"/>']

    def text(self, x, y, text, size=15, color=INK, anchor="middle", bold=False):
        self.parts.append(S.txt(x, y, text, fs=size, font=S.SANS, fill=color, anchor=anchor, weight=700 if bold else 500, halo=False))

    def lines(self, x, y, text, width=24, size=15, color=INK, anchor="middle"):
        for i, line in enumerate(wrap(text, width)):
            self.text(x, y+i*(size+6), line, size, color, anchor)

    def box(self, x, y, w, h, title="", sub="", fill="#F2F6F7", dashed=False):
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="#A3B5BE" stroke-width="1.4"{dash}/>')
        if title:
            self.text(x+w/2, y+28, title, 17, bold=True)
        if sub:
            self.text(x+w/2, y+53, sub, 13)

    def wire(self, pol, points, thick=3):
        self.parts.append(S.path(points, "#FFFFFF", sw=thick+3))
        self.parts.append(S.path(points, COL[pol], sw=thick))
        if pol == "PE":
            self.parts.append(S.path(points, "#E7CA38", sw=1.3, dash="7 5"))

    def dot(self, x, y, pol):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{COL[pol]}"/>')

    def pin(self, x, y, pol, label=None):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="5" fill="white" stroke="{COL[pol]}" stroke-width="2"/>')
        if label:
            self.text(x, y+21, label, 12, COL[pol])

    def header(self, title, sub):
        self.text(self.width/2, 36, title, 25, bold=True)
        self.text(self.width/2, 66, sub, 15, "#5B737E")

    def end(self):
        return "\n".join(line.rstrip() for line in "".join(self.parts).splitlines())+"</svg>"


def supply_svg():
    d = Sheet("Упрощённый щит — 13 линий и одна ступень", 1150, 1520)
    d.header("13 линий · 4 групповых УЗО · 1 ступень разгрузки", "1 фаза 230 В / 50 А — допущение; выделено 10 кВт. Обзор L/N, подробные соединения — на отдельных листах.")
    for x, w, title, sub, dash in ((30, 325, "Этажный щит · допущение", "QF0 50 А · счётчик · УЗО 100/300 мА S", True), (410, 200, "QS · 2P 63 А", "Выключатель нагрузки", False), (680, 260, "KV · 63 А*", "Реле напряжения · L", False), (1050, 400, "XD · Распределительный блок L/N", "Закрытые блоки ≥ 63 А*", False)):
        d.box(x, 110, w, 82, title, sub, dashed=dash)
    for a, b in ((355,410),(610,680),(940,1050)):
        d.wire("L", [(a,140),(b,140)])
    d.wire("N", [(355,174),(410,174)])
    d.wire("N", [(610,174),(640,174),(640,205),(1020,205),(1020,174),(1050,174)])
    d.wire("N", [(810,205),(810,192)])
    d.dot(810,205,"N")
    d.text(650, 218, "TA1 на L после QS, до разветвлений → KP: общая мощность; PE отдельно", 14)
    d.wire("L", [(1250,192),(1250,260)], 5)
    d.wire("N", [(1340,192),(1340,285)], 5)
    d.wire("L", [(40,260),(1490,260)], 5)
    d.wire("N", [(40,285),(1490,285)], 5)
    d.dot(1250,260,"L"); d.dot(1340,285,"N")
    d.text(1490,244,"XD.L",15,COL["L"],anchor="end",bold=True)
    d.text(1490,310,"XD.N",15,COL["N"],anchor="end",bold=True)
    for i, (bank, (title, groups, neutral, comb)) in enumerate(BANKS.items()):
        x = 30+i*375
        d.box(x, 315, 350, 690, fill="#FFF8EE" if bank == "QD4" else "#F8FAFB")
        d.text(x+175,340,title,14,bold=True)
        d.box(x+60,365,230,78,bank,"УЗО 2P · 63 А · 30 мА A*")
        for pol, px, target, yy in (("L",x+30,x+115,260),("N",x+320,x+235,285)):
            d.wire(pol,[(px,yy),(px,354),(target,354),(target,365)]); d.dot(px,yy,pol)
        y = 443
        if bank == "QD4":
            d.wire("L",[(x+115,y),(x+115,475)])
            d.wire("N",[(x+235,y),(x+235,475)])
            d.box(x+60,475,230,70,"KM1 · 2NO","Отключает сразу весь блок", "#FFE7C8")
            y = 545
        d.wire("L",[(x+115,y),(x+115,580),(x+30,580),(x+30,945)],5)
        d.wire("N",[(x+235,y),(x+235,563),(x+320,563),(x+320,945)],5)
        d.text(x+175,599,comb+(" · гребёнка" if FEED_KIND[bank]=="comb" else " · перемычки"),13,COL["L"])
        d.text(x+305,550,neutral,14,COL["N"],bold=True)
        entries = list(groups) + ([22] if bank == "QD4" else [])
        for j,g in enumerate(entries):
            yy = 607+j*92
            rating = DEV[str(g)][1] if g != 22 else "C16* · резерв"
            label = SHORT[g] if g != 22 else "Бойлер · не подключён"
            d.wire("L",[(x+30,yy+23),(x+55,yy+23)])
            d.dot(x+30,yy+23,"L")
            d.box(x+55,yy,245,72,f"QF{g} · Автомат" if g!=22 else "QF22 · Резерв автомата", rating+" · "+label, "#FFFFFF", dashed=g==22)
        d.text(x+175,982,f"Нули только → {neutral} · PE → XPE",13,bold=True)
    d.wire("PE",[(40,1040),(1470,1040)],5)
    d.text(760,1067,"XPE · общая защитная шина · без контакторов и перемычек к N",16,COL["PE"],bold=True)
    d.text(760,1100,"B1/B4 — гребёнки; B2/B3 — перемычки. QF3 — 2P; X15.L/X20.L — разветвления после своих автоматов.",14)
    d.text(760,1126,"* Предварительный подбор. УЗИП и его защита — открытый вопрос, в подключённую схему не включены; место оставлено.",14,"#637681")
    return d.end()


def bank_svg(bank):
    title, groups, neutral, comb = BANKS[bank]
    controlled = bank == "QD4"
    entries = list(groups) + ([22] if controlled else [])
    d = Sheet(bank+": проводники", 930)
    d.header(bank+" · "+title, "L — коричневый · N — синий · PE — зелёно-жёлтый. Точка означает соединение; пересечение без точки — нет.")
    d.box(40,120,200,90,bank+" · УЗО","2P · 63 А · 30 мА A*")
    for pol, x in (("L",90),("N",190)):
        d.text(x,98,"XD."+pol,15,COL[pol],bold=True)
        d.wire(pol,[(x,105),(x,120)]); d.pin(x,120,pol)
    y = 210
    if controlled:
        for pol,x in (("L",90),("N",190)):
            d.wire(pol,[(x,210),(x,245)])
        d.box(40,245,200,82,"KM1 · 2NO","Сила L и N", "#FFE9CD")
        d.text(360,275,"Катушка KM1 от QFC / N1 — отдельная цепь управления",15,anchor="start")
        y = 327
    centers = [380+j*230 for j in range(len(entries))]
    end = centers[-1]
    d.wire("N",[(190,y),(190,382),(end+65,382)],5)
    d.wire("L",[(90,y),(90,420),(end,420)],5)
    d.text(275,405,comb,15,COL["L"],bold=True)
    d.text(275,365,neutral,15,COL["N"],bold=True)
    if bank == "QD2":
        d.text(600,263,"B2 — проводные перемычки; QF3.L и QF3.N подключены отдельно.",15,bold=True)
        d.text(600,291,"Не ставить обычную фазную гребёнку через соседнюю клемму QF3.N.",14)
    if bank == "QD1":
        d.text(680,265,"От B1 отдельно: QFC B2 → XC.L; N1 → XC.N.",15,bold=True)
        d.text(680,294,"Это питание KP и катушки KM1, оно не отключается самим KM1.",14)
    for x,g in zip(centers,entries):
        two = g == 3
        d.box(x-62,475,125,110,f"QF{g}", "Автомат" if g!=22 else "Резерв", "#FFFFFF", dashed=g==22)
        d.text(x,558,DEV[str(g)][1] if g!=22 else "C16* · резерв",13)
        d.wire("L",[(x,420),(x,475)]);d.dot(x,420,"L");d.pin(x,475,"L")
        d.pin(x,585,"L")
        if g in BRANCHES:
            d.wire("L",[(x,585),(x,635)])
            d.box(x-50,635,100,48,f"X{g}.L",fill="#FFF0D9")
            d.wire("L",[(x,683),(x,730)])
        else:
            d.wire("L",[(x,585),(x,730)])
        if two:
            d.wire("N",[(x+40,382),(x+40,475)])
            d.dot(x+40,382,"N");d.pin(x+40,475,"N")
            d.wire("N",[(x+40,585),(x+40,650),(x+65,650),(x+65,730)])
            d.pin(x+40,585,"N")
        else:
            d.wire("N",[(x+65,382),(x+65,730)]);d.dot(x+65,382,"N")
        d.wire("PE",[(x+100,785),(x+100,730)])
        d.text(x-12,710,f"W{g} · "+(GROUPS[g][2] if g!=22 else "3×2,5*"),13,anchor="end")
        for pol,px in (("L",x),("N",x+65),("PE",x+100)):
            d.pin(px,730,pol)
            d.text(px+(12 if pol=="PE" else 0),754,f"W{g}."+pol,12,COL[pol],anchor="start" if pol=="PE" else "middle")
        d.lines(x+25,825,GROUPS[g][0] if g!=22 else "Бойлер: место, без подключённого кабеля",25,14)
    d.wire("PE",[(270,785),(1210,785)],5)
    for x in centers:
        d.dot(x+100,785,"PE")
    d.text(200,790,"XPE",15,COL["PE"],bold=True)
    d.text(640,910,"Wg.L/N/PE — жилы кабеля, а не отдельные клеммы. X15.L и X20.L — реальные фазные блоки разветвлений.",14,"#637681")
    return d.end()


def priority_svg():
    d = Sheet("Управление общей ступенью разгрузки", 850)
    d.header("Одна команда KP → один контактор KM1", "Ручной возврат SB1 и самоподхват KM1a. Цепь управления полностью после QD1 / QFC.")
    d.box(45,115,330,85,"TA1 · общий ток квартиры","Только L после QS, до разветвлений")
    d.box(520,115,360,85,"KP · измерение P / I","Питание XC.L / XC.N; совместимый TA1")
    d.parts.append(S.path([(375,155),(520,155)], "#7256A8", sw=2, dash="6 4"))
    d.text(450,139,"датчик*",13)
    d.text(210,235,"B1 → QFC B2 → XC.L",15,COL["L"],bold=True)
    d.text(1070,235,"XC.N ← N1",15,COL["N"],bold=True)
    d.wire("L",[(100,265),(100,700)],4)
    d.wire("N",[(1170,265),(1170,700)],4)
    d.wire("L",[(100,370),(240,370)])
    d.box(240,320,180,95,"KP · PERMIT","NO · разрешение")
    d.wire("L",[(420,370),(470,370)])
    d.box(470,320,150,95,"SB0 · Стоп","NC · разрыв цепи")
    d.wire("L",[(620,370),(670,370),(670,320),(730,320)])
    d.wire("L",[(670,370),(670,475),(730,475)])
    d.dot(670,370,"L")
    d.box(730,275,190,85,"SB1 · Возврат","NO · нажать вручную")
    d.box(730,435,190,85,"KM1a · 1NO","Замыкается вместе с KM1")
    d.wire("L",[(920,320),(970,320),(970,370)])
    d.wire("L",[(920,475),(970,475),(970,370),(1010,370)])
    d.dot(970,370,"L")
    d.box(1010,320,100,100,"KM1","Катушка 230 В")
    d.wire("N",[(1110,370),(1170,370)])
    d.text(1005,303,"A1",13,COL["L"]);d.text(1123,303,"A2",13,COL["N"])
    d.text(640,592,"Перегрузка → PERMIT разомкнут → KM1 отпал → KM1a разомкнулся.",18,bold=True)
    d.text(640,628,"После снижения нагрузки PERMIT может вернуться, но KM1 ждёт SB1.",17)
    d.text(640,664,"После исчезновения питания — тот же ручной возврат. Кнопки вне мокрых зон.",16)
    d.box(130,725,1020,85,fill="#FFF7E9")
    d.text(640,752,"KP: задержка и гистерезис, снятие разрешения при неисправности, пауза повторного пуска кондиционеров.",15,bold=True)
    d.text(640,780,"A2 катушки подключать к N1 через XC.N, а не к отключаемой N4S. TA1 и клеммы — по паспорту выбранной модели.",14)
    return d.end()


def overview_svg(rows=PANEL_ROWS, devices=DEV):
    d = Sheet("Монтажная раскладка на 54 модуля", 950, 1520)
    d.header("Монтажный вид · 3 рейки × 18 модулей", "Тип устройства указан словами. B1/B4 — гребёнки; B2/B3 — проводные перемычки.")
    left, module = 95, 72
    positions = {}
    for ri,row in enumerate(rows):
        y, x = 150+ri*225, left
        d.box(45,y-45,1430,207,fill="#F8FAFB")
        d.text(70,y+65,str(ri+1),18,bold=True)
        d.parts.append(f'<rect x="{left}" y="{y+48}" width="1296" height="12" fill="#CDD7DC"/>')
        for key in row:
            code, rating, label, mods, kind, title, _ = devices[key]
            w = mods*module
            positions[key]=(x,y,w)
            circuit = BANK_OF[int(key)] if key.isdigit() else (key if key in BANKS else ("branches" if key in ("X15","X20") else ("priority" if key in ("KP","QFC","KM1","KAUX") else "inlet")))
            d.parts.append(f'<g class="hit" data-info="{key}" data-circuit="{circuit}" tabindex="0" role="button" aria-label="{escape(title)}">')
            fill = "#FFEBD1" if key in ("QD4","KM1","KAUX","9","15","20","X15","X20") else ("#FFFFFF" if code else "#EDF1F3")
            d.box(x+3,y,w-6,125,fill=fill,dashed=code is None)
            shown_code = "QF"+key if key.isdigit() else (code or ("QF22" if key=="r1" else "Резерв"))
            d.text(x+w/2,y+22,shown_code,14 if w<=80 else 16,bold=True)
            typ=device_type(key)
            d.text(x+w/2,y+44,typ,9 if w<=80 else 12)
            d.text(x+w/2,y+66,rating.split(" · ")[0] if w<=80 else rating,11 if w<=80 else 12)
            d.lines(x+w/2,y+91,label,10 if w<=80 else max(12,int(w/8)),9 if w<=80 else 11)
            d.parts.append('</g>')
            if key.isdigit():
                g=int(key)
                d.text(x+w/2,y+146,"→ "+(f"X{g}.L" if g in BRANCHES else f"W{g}"),12)
            x+=w
    for bank,(_,groups,neutral,comb) in BANKS.items():
        ids = [str(g) for g in groups if g != 3]
        x0,y,_=positions[ids[0]]
        x1,_,w1=positions[ids[-1]]
        yy=y-15
        thick = 5 if FEED_KIND[bank]=="comb" else 2.5
        d.wire("L",[(x0+16,yy),(x1+w1-16,yy)],thick)
        for key in ids:
            x,_,w=positions[key]
            d.wire("L",[(x+w/2,yy),(x+w/2,y)],thick)
            d.dot(x+w/2,yy,"L")
        label = comb+(" · гребёнка" if FEED_KIND[bank]=="comb" else " · перемычки")
        d.text((x0+x1+w1)/2,yy-12,label,12,COL["L"],bold=True)
    x,y,w=positions["3"]
    d.text(x+w/2,y-25,"QD2.L / N2",12,bold=True)
    for pol,px in (("L",x+w*.3),("N",x+w*.7)):
        d.wire(pol,[(px,y-15),(px,y)])
    for j,label in enumerate(("N1 ← QD1", "N2 ← QD2", "N3 ← QD3", "N4S ← KM1", "XPE · общая PE")):
        x=75+j*285
        d.box(x,825,265,48,fill="#EDF7FA" if j<4 else "#EEF8EC")
        d.text(x+132,855,label,16,COL["N" if j<4 else "PE"],bold=True)
    d.text(760,908,"Вместо общего клеммного ряда — прямые подключения и два локальных блока X15.L/X20.L. Маркировать каждый кабель.",15)
    d.text(760,932,"Габариты корпуса, держателей шин, фазных блоков и аппаратов предварительные; проверить до закупки.",14)
    return d.end()



def group_svg(g, groups=GROUPS, devices=DEV, rows=PANEL_ROWS):
    # Полный лист блока лучше показывает общую гребёнку и правильную нейтраль.
    return bank_svg(BANK_OF[g])


def branch_svg():
    d=Sheet("Разветвления санузлов и кондиционеров",1080,1380)
    d.header("Локальные фазные блоки у захода кабелей", "Физически у ввода кабелей в корпус, электрически после соответствующих автоматов. Общего выходного клеммного ряда нет.")
    for i,(g,branches) in enumerate(BRANCHES.items()):
        x=45+i*680
        d.box(x,110,620,880,fill="#FAFBFC")
        d.box(x+25,150,175,85,f"QF{g} · Автомат","C16 · выход L")
        d.wire("L",[(x+200,190),(x+245,190)])
        d.box(x+245,150,180,85,f"X{g}.L","Изолированный блок", "#FFF0D9")
        d.wire("L",[(x+335,235),(x+335,280),(x+70,280),(x+70,880)],5)
        d.wire("N",[(x+490,280),(x+490,880)],5)
        d.wire("PE",[(x+575,280),(x+575,880)],5)
        d.text(x+490,260,"N4S",15,COL["N"],bold=True)
        d.text(x+575,260,"XPE",15,COL["PE"],bold=True)
        for j,(code,label) in enumerate(branches):
            yy=320+j*95
            d.wire("L",[(x+70,yy),(x+140,yy)]);d.dot(x+70,yy,"L")
            d.wire("N",[(x+490,yy+20),(x+455,yy+20)]);d.dot(x+490,yy+20,"N")
            d.wire("PE",[(x+575,yy+40),(x+455,yy+40)]);d.dot(x+575,yy+40,"PE")
            d.box(x+140,yy-14,315,65,code+" · 3×2,5",label, "#FFFFFF")
        d.text(x+310,949,"Каждая ветвь подписана с двух концов",16,bold=True)
    d.text(690,1026,"X15.L и X20.L между собой не соединять. N всех этих ветвей только от N4S после QD4 и KM1; PE непрерывен.",15)
    d.text(690,1055,"Для обычной одиночной линии: выход автомата → кабель; N → шина своего УЗО; PE → XPE.",15)
    return d.end()


def circuit_pages(groups=GROUPS, devices=DEV, rows=PANEL_ROWS):
    pages = []
    for bank,(title,_,_,_) in BANKS.items():
        pages.append({"id":bank,"title":bank+" · "+title,"svg":bank_svg(bank),"print":True})
    pages.append({"id":"branches","title":"Разветвления X15.L / X20.L","svg":branch_svg(),"print":True})
    pages.append({"id":"priority", "title":"Управление разгрузкой", "svg":priority_svg(), "print":True})
    pages.append({"id":"inlet", "title":"Общая схема", "svg":supply_svg(), "print":False})
    return pages
