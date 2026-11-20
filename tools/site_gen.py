"""Генератор статического сайта для GitHub Pages: projects/* → docs/.

Дерево страниц:
  /                                   все объекты
  /<объект>/                          объект: описание, ссылки застройщика, варианты, сравнение
  /<объект>/v1/                       вариант: план, комнаты, разделы, рендеры
  /<объект>/v1/plan/                  план квартиры с зумом
  /<объект>/v1/3d/                    3D-модель
  /<объект>/v1/komnaty/<комната>/     комната: план с зумом, заметки, рендеры
  /<объект>/v1/<раздел>/              раздел проекта по всей квартире
  /<объект>/v1/<раздел>/<комната>/    раздел по комнате
  /<объект>/v1/<раздел>/<страница>/   щит, коллектор и т. п.
Все ссылки относительные, сайт работает и из подпапки github.io/<репозиторий>/.
"""
import html
import importlib.util
import os
import re
import shutil
import sys
from pathlib import Path

SITE_TITLE = "Стройка"
E = html.escape


# ------------------------------------------------------------------ загрузка объекта
def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class Project:
    def __init__(self, folder):
        self.dir = folder
        slug = folder.name.replace("-", "_")
        sys.path.insert(0, str(folder))
        self.obj = load_module(folder / "object.py", f"obj_{slug}")
        self.layout = load_module(folder / "layout.py", f"layout_{slug}")
        self.content = load_module(folder / "content.py", f"content_{slug}")
        sys.path.remove(str(folder))
        self.meta = self.obj.OBJECT
        self.slug = self.meta["slug"]
        self.variants = self.content.VARIANTS
        self.svg = {}
        for v in self.variants:
            plan = self.layout.VARIANTS[v["n"]]()
            self.svg[v["n"]] = plan.render(self.layout.VIEWBOX, "__PLAN__", f"План, вариант {v['n']}",
                                           getattr(self.layout, "PLAN_IMG_BOX", None))

    def room(self, r, n):
        o = dict(r)
        o.update(r.get("override", {}).get(n, {}))
        return o

    def notes(self, r, n):
        """Группа заметок комнаты в варианте n, иначе — из варианта 1."""
        for vn in (n, 1):
            title = r["notes"].get(vn)
            if not title:
                continue
            v = next(x for x in self.variants if x["n"] == vn)
            for t, meta, lis in v["rooms"]:
                if t == title:
                    return t, meta, lis, vn
        return None


# ------------------------------------------------------------------ html-кусочки
def rel(from_dir, to):
    """Относительная ссылка от папки страницы до пути от корня docs."""
    r = os.path.relpath(to, from_dir or ".")
    return r.replace(os.sep, "/")


def page_path(*parts):
    return "/".join(p for p in parts if p)


class Page:
    def __init__(self, path, title, crumbs, body, kind="", scripts=""):
        self.path = path          # папка страницы от корня docs ("" — корень)
        self.title = title
        self.crumbs = crumbs      # [(название, путь папки)]
        self.body = body
        self.kind = kind
        self.scripts = scripts


def link(page_dir, target_dir, text, cls=""):
    href = rel(page_dir, (target_dir + "/index.html") if target_dir else "index.html")
    c = f' class="{cls}"' if cls else ""
    return f'<a href="{href}"{c}>{text}</a>'


def crumbs_html(page):
    items = []
    for i, (name, path) in enumerate(page.crumbs):
        last = i == len(page.crumbs) - 1
        if last:
            items.append(f'<li aria-current="page">{E(name)}</li>')
        elif path is None:
            items.append(f"<li><span>{E(name)}</span></li>")
        else:
            items.append(f"<li>{link(page.path, path, E(name))}</li>")
    return f'<nav class="crumbs" aria-label="Путь"><ol>{"".join(items)}</ol></nav>'


def svg_with(svg, plan_href, viewbox=None):
    s = svg.replace('href="__PLAN__"', f'href="{plan_href}"')
    if viewbox:
        x, y, w, h = viewbox
        s = re.sub(r'viewBox="[^"]+"', f'viewBox="{x} {y} {w} {h}"', s, count=1)
    return s


def crop_box(rect, pad=45):
    x1, y1, x2, y2 = rect
    return (x1 - pad, y1 - pad, x2 - x1 + 2 * pad, y2 - y1 + 2 * pad)


def viewer(svg, cls="", overlay=False, note=""):
    """Просмотр плана с зумом: щипок, перетаскивание, колесо, двойной тап, кнопки, полный экран."""
    ov = ('<label class="pz-toggle"><input type="checkbox" data-pz-orig> План застройщика</label>' if overlay else "")
    return f'''<div class="pzw {cls}">
<div class="pz" data-pz>
  <div class="pz-stage">{svg}</div>
  <div class="pz-bar">
    <button type="button" data-pz-in aria-label="Приблизить">+</button>
    <button type="button" data-pz-out aria-label="Отдалить">−</button>
    <button type="button" data-pz-fit>Вписать</button>
    <button type="button" data-pz-full aria-pressed="false">На весь экран</button>
    {ov}
  </div>
</div>
<p class="pz-hint">{note or "Щипок двумя пальцами или колесо мыши — зум, перетаскивание — сдвиг, двойной тап — приблизить."}</p>
</div>'''


def chips(lst):
    return '<div class="chips">' + "".join(f'<span class="chip {c}">{t}</span>' for c, t in lst) + "</div>"


def note_card(title, meta, lis):
    li = "".join(f"<li>{x}</li>" for x in lis)
    m = f'<span class="m">{meta}</span>' if meta else ""
    return f'<div class="card note"><h3>{title}{m}</h3><ul>{li}</ul></div>'


def figure(src, cap, wide=False, w=1200, h=800):
    c = ' class="tall"' if wide else ""
    return f'<figure{c}><a href="{src}"><img src="{src}" alt="{E(cap)}" loading="lazy" width="{w}" height="{h}"></a><figcaption>{cap}</figcaption></figure>'


LEGEND = '''<div class="legend" aria-label="Обозначения">
  <span><i style="background:#BCD5F2;border-color:#4F7DB8"></i>Кровати</span>
  <span><i style="background:#EBD3B1;border-color:#A87A42"></i>Шкафы и полки</span>
  <span><i style="background:#C6E3BA;border-color:#4F8F48"></i>Диваны и стулья</span>
  <span><i style="background:#F7DE98;border-color:#B8902A"></i>Столы</span>
  <span><i style="background:#F5C6AC;border-color:#BA6A45"></i>Кухня</span>
  <span><i style="background:#F4F6F7;border-color:#6F7980"></i>Техника</span>
  <span><i style="background:#D3ECF7;border-color:#3E8DB5"></i>Сантехника</span>
  <span><i style="background:#E4DAF7;border-color:#7A5BBE"></i>Спорт и игры</span>
  <span><i class="bar" style="background:#E07A2E"></i>Новая перегородка</span>
  <span><i class="dash" style="border-color:#D64545"></i>Снос</span>
  <span><i class="arrow"></i>Свободный проход, см</span>
</div>'''


# ------------------------------------------------------------------ дерево навигации
def nav_tree(projects, page):
    cur = page.path

    def a(path, text, extra_cls=""):
        cls = ("cur " if path == cur else "") + extra_cls
        return link(cur, path, text, cls.strip())

    def node(path, text, children, extra_cls=""):
        if not children:
            return f"<li>{a(path, text, extra_cls)}</li>"
        is_open = cur == path or cur.startswith(path + "/")
        o = " open" if is_open else ""
        return f'<li><details{o}><summary>{a(path, text, extra_cls)}</summary><ul>{"".join(children)}</ul></details></li>'

    def group(title, children, path_prefix):
        is_open = cur.startswith(path_prefix + "/")
        o = " open" if is_open else ""
        return f'<li><details{o}><summary><span>{title}</span></summary><ul>{"".join(children)}</ul></details></li>'

    out = []
    for p in projects:
        vs = []
        for v in p.variants:
            n = v["n"]
            vp = f"{p.slug}/v{n}"
            rooms = [f"<li>{a(f'{vp}/komnaty/' + r['id'], E(p.room(r, n)['name']))}</li>" for r in p.obj.ROOMS]
            secs = []
            for s in p.obj.SECTIONS:
                sp = f"{vp}/{s['id']}"
                kids = [f"<li>{a(sp + '/' + x['id'], E(x['name']))}</li>" for x in s.get("extra", [])]
                kids += [f"<li>{a(sp + '/' + r['id'], E(p.room(r, n)['name']))}</li>" for r in p.obj.ROOMS]
                badge = ' <span class="badge">в работе</span>' if s.get("status") == "draft" else ""
                secs.append(node(sp, E(s["name"]) + badge, kids))
            kids = [f"<li>{a(vp + '/plan', 'План квартиры')}</li>", f"<li>{a(vp + '/3d', '3D-модель')}</li>",
                    group("Комнаты", rooms, vp + "/komnaty")] + secs
            vs.append(node(vp, f"Вариант {n} <span class='sub'>· {E(p.obj.VARIANT_SHORT.get(n, ''))}</span>", kids))
        out.append(node(p.slug, E(p.meta["title"]), vs, "obj"))
    home = f'<li>{a("", "Все объекты", "home")}</li>'
    return f'<ul class="tree">{home}{"".join(out)}</ul>'


# ------------------------------------------------------------------ шаблон страницы
def render_page(page, projects, root):
    r = "../" * len(page.path.split("/")) if page.path else ""
    body_cls = f"k-{page.kind}" if page.kind else ""
    return f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(page.title)} · {SITE_TITLE}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Golos+Text:wght@400;500;600;700&family=Unbounded:wght@600;700&family=JetBrains+Mono:wght@500;600&display=swap">
<link rel="stylesheet" href="{r}assets/style.css">
</head>
<body class="{body_cls}">
<header class="topbar">
  <button type="button" class="menu-btn" aria-controls="nav" aria-expanded="false"><span class="ico" aria-hidden="true"></span>Меню</button>
  <a class="brand" href="{r}index.html">{SITE_TITLE}</a>
</header>
<div class="layout">
  <nav id="nav" class="sidenav" aria-label="Все страницы">{nav_tree(projects, page)}</nav>
  <div class="scrim" data-close-nav></div>
  <main class="content">
    {crumbs_html(page)}
    {page.body}
  </main>
</div>
<script src="{r}assets/app.js"></script>
{page.scripts}
</body>
</html>
'''


# ------------------------------------------------------------------ страницы
def pages_for(p, projects):
    o = p.obj
    pages = []
    obj_dir = p.slug
    obj_crumb = (p.meta["title"], obj_dir)
    home = ("Все объекты", "")

    # --- объект
    def asset(page_dir, name):
        return rel(page_dir, f"{obj_dir}/{name}")

    cards = []
    for v in p.variants:
        n = v["n"]
        img = asset(obj_dir, f"renders/v{n}-doll_sw.jpg")
        cards.append(f'''<a class="card vcard" href="{rel(obj_dir, f"{obj_dir}/v{n}/index.html")}">
  <img src="{img}" alt="" loading="lazy" width="1200" height="800">
  <div class="vc-body"><div class="eyebrow">Вариант {n}</div><h3>{v["title"]}</h3>{chips(v["chips"][:3])}</div></a>''')
    links = ""
    if p.meta.get("links"):
        li = "".join(f'<li><a href="{E(u)}" rel="noopener" target="_blank">{E(t)}</a></li>' for t, u in p.meta["links"])
        links = f'<div class="card"><h3>Страницы застройщика</h3><ul class="plain">{li}</ul></div>'
    comp = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>" for a, b, c, d in p.content.COMPARE)
    heads = "".join(f'<th>Вариант {v["n"]}<br><span class="sub">{E(o.VARIANT_SHORT.get(v["n"], ""))}</span></th>' for v in p.variants)
    check = "".join(f'<tr><td>{a}</td><td class="num">{b}</td><td class="num">{c}</td><td class="num">{d}</td></tr>' for a, b, c, d in p.content.CHECK)
    facts = "".join(f'<span class="fact">{E(f)}</span>' for f in p.meta.get("facts", []))
    plan_note = p.meta.get("plan_note", "Размеры на всех чертежах сняты с этого плана: стены обведены по картинке, масштаб подобран по площадям, 0,92 см на пиксель. Точность около ±5 см, перед заказом мебели комнаты стоит перемерить.")
    pw, ph = p.meta.get("plan_size", (1206, 1618))
    body = f'''<header class="phead">
  <div class="eyebrow">Объект</div>
  <h1>{E(p.meta["title"])}</h1>
  <p class="lede">{E(p.meta["about"])}</p>
  <div class="facts">{facts}</div>
</header>
{links}
<section class="block"><h2>Варианты</h2><div class="vcards">{"".join(cards)}</div></section>
<section class="block"><h2>Чем варианты отличаются</h2>
  <div class="tablewrap"><table><thead><tr><th></th>{heads}</tr></thead><tbody>{comp}</tbody></table></div></section>
<section class="block"><h2>План застройщика</h2>
  <p>{E(plan_note)}</p>
  <div class="two">
    <a class="card planimg" href="{asset(obj_dir, p.meta["plan_image"])}"><img src="{asset(obj_dir, p.meta["plan_image"])}" alt="План застройщика" loading="lazy" width="{pw}" height="{ph}"></a>
    <div class="tablewrap"><table class="narrow"><thead><tr><th>Помещение</th><th>На плане, м²</th><th>Размер, см</th><th>По размерам, м²</th></tr></thead><tbody>{check}</tbody></table></div>
  </div>
</section>'''
    pages.append(Page(obj_dir, p.meta["title"], [home, obj_crumb], body, "object"))

    # --- варианты
    for v in p.variants:
        n = v["n"]
        vdir = f"{obj_dir}/v{n}"
        vname = f"Вариант {n}"
        v_crumb = (vname, vdir)
        svg = p.svg[n]

        # вариант
        rooms_cards = []
        for r in o.ROOMS:
            rr = p.room(r, n)
            nt = p.notes(r, n)
            first = nt[2][0] if nt else ""
            first = re.sub(r"<[^>]+>", "", first)
            rooms_cards.append(f'''<a class="card rcard" href="{rel(vdir, f"{vdir}/komnaty/{r['id']}/index.html")}">
  <h3>{E(rr["name"])}<span class="m">{E(rr["area"])}</span></h3><p>{E(first)}</p></a>''')
        sec_cards = []
        for s in o.SECTIONS:
            badge = '<span class="badge">в работе</span>' if s.get("status") == "draft" else ""
            sec_cards.append(f'''<a class="card rcard" href="{rel(vdir, f"{vdir}/{s['id']}/index.html")}">
  <h3>{E(s["name"])}{badge}</h3><p>{E(s["about"])}</p></a>''')
        gal = gallery_html(p, vdir, n, v["gallery"])
        preview = svg_with(svg, asset(vdir, p.meta["plan_image"]))
        body = f'''<header class="phead">
  <div class="eyebrow">{E(p.meta["title"])} · {vname}</div>
  <h1>{v["title"]}</h1>
  <p class="lede">{v["lede"]}</p>
  {chips(v["chips"])}
</header>
<section class="block vplan">
  <a class="card preview" href="{rel(vdir, f"{vdir}/plan/index.html")}" aria-label="Открыть план с зумом">{preview}<span class="open">Открыть план с зумом →</span></a>
  <div class="notes">{"".join(note_card(*g) for g in v["rooms"])}</div>
</section>
<section class="block"><h2>Комнаты</h2><div class="rcards">{"".join(rooms_cards)}</div></section>
<section class="block"><h2>Разделы проекта</h2><div class="rcards">{"".join(sec_cards)}</div></section>
<section class="block"><h2>В объёме</h2>
  <p>{link(vdir, vdir + "/3d", "Открыть 3D-модель →", "btn")}</p>
  {gal}
</section>'''
        pages.append(Page(vdir, f"{vname}: {v['title']}", [home, obj_crumb, v_crumb], body, "variant"))

        # план целиком
        pdir = f"{vdir}/plan"
        body = f'''<header class="phead compact"><h1>План квартиры</h1><p class="lede">{vname} · {E(o.VARIANT_SHORT.get(n, ""))}. Размеры в сантиметрах.</p></header>
{viewer(svg_with(svg, asset(pdir, p.meta["plan_image"])), "pz-main", overlay=True)}
{LEGEND}
<section class="block"><h2>Комнаты</h2><div class="rcards">{"".join(x.replace('href="', 'href="../') for x in rooms_cards)}</div></section>'''
        pages.append(Page(pdir, f"План квартиры, {vname.lower()}", [home, obj_crumb, v_crumb, ("План квартиры", pdir)], body, "plan"))

        # 3D
        ddir = f"{vdir}/3d"
        model = asset(ddir, f"models/v{n}.glb")
        body = f'''<header class="phead compact"><h1>3D-модель</h1><p class="lede">{vname}. Тяните, чтобы повернуть, щипок или колесо мыши приближают. Потолка нет, стены срезаны на высоте 2,1 м.</p></header>
<div class="viewer3d" data-model="{model}" data-poster="{asset(ddir, f"renders/v{n}-doll_sw.jpg")}"><p class="v3-status">Загружаю модель…</p></div>'''
        scripts = '''<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/examples/js/loaders/GLTFLoader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/examples/js/controls/OrbitControls.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/examples/js/environments/RoomEnvironment.js"></script>
<script src="''' + rel(ddir, "assets/viewer3d.js") + '''"></script>'''
        pages.append(Page(ddir, f"3D-модель, {vname.lower()}", [home, obj_crumb, v_crumb, ("3D-модель", ddir)], body, "model", scripts))

        # комнаты
        room_ids = [r["id"] for r in o.ROOMS]
        for i, r in enumerate(o.ROOMS):
            rr = p.room(r, n)
            rdir = f"{vdir}/komnaty/{r['id']}"
            nt = p.notes(r, n)
            notes = ""
            if nt:
                t, meta, lis, from_v = nt
                hint = f'<p class="sub">Как в варианте {from_v}.</p>' if from_v != n else ""
                notes = note_card(t, meta, lis) + hint
            shots = [s for s in r.get("shots", {}).get(n, []) if (p.dir / "renders" / f"{s}.jpg").exists()]
            figs = "".join(figure(asset(rdir, f"renders/{s}.jpg"), caption_for(p, s)) for s in shots)
            gal = f'<section class="block"><h2>Рендеры</h2><div class="gallery">{figs}</div></section>' if figs else ""
            secs = "".join(f'<li>{link(rdir, f"{vdir}/{s["id"]}/{r["id"]}", E(s["name"]))}</li>' for s in o.SECTIONS)
            prev_id = room_ids[i - 1]
            next_id = room_ids[(i + 1) % len(room_ids)]
            prev_r = p.room(o.ROOMS[i - 1], n)
            next_r = p.room(o.ROOMS[(i + 1) % len(room_ids)], n)
            pager = f'''<nav class="pager" aria-label="Соседние комнаты">
  {link(rdir, f"{vdir}/komnaty/{prev_id}", "← " + E(prev_r["name"]))}
  {link(rdir, f"{vdir}/komnaty/{next_id}", E(next_r["name"]) + " →")}
</nav>'''
            body = f'''<header class="phead compact"><div class="eyebrow">{vname}</div><h1>{E(rr["name"])}<span class="m">{E(rr["area"])}</span></h1></header>
{viewer(svg_with(svg, asset(rdir, p.meta["plan_image"]), crop_box(rr["rect"])), "pz-room")}
<section class="block two-col">{notes}<div class="card"><h3>Разделы по комнате</h3><ul class="plain">{secs}</ul></div></section>
{gal}
{pager}'''
            pages.append(Page(rdir, f"{rr['name']}, {vname.lower()}", [home, obj_crumb, v_crumb, ("Комнаты", None), (rr["name"], rdir)], body, "room"))

        # разделы
        for s in o.SECTIONS:
            sdir = f"{vdir}/{s['id']}"
            s_crumb = (s["name"], sdir)
            draft = s.get("status") == "draft"
            items = "".join(f"<li>{E(x)}</li>" for x in s.get("plan_items", []))
            status = f'''<div class="card draft"><h3>Раздел в работе</h3><p>Пока на плане только расстановка как подложка. Здесь появятся:</p><ul>{items}</ul></div>''' if draft else ""
            extra = "".join(f'<a class="card rcard" href="{rel(sdir, f"{sdir}/{x["id"]}/index.html")}"><h3>{E(x["name"])}</h3><p>{E(x["about"])}</p></a>' for x in s.get("extra", []))
            rooms_l = "".join(f'<li>{link(sdir, f"{sdir}/{r["id"]}", E(p.room(r, n)["name"]))}</li>' for r in o.ROOMS)
            body = f'''<header class="phead compact"><div class="eyebrow">{vname} · раздел</div><h1>{E(s["name"])}</h1><p class="lede">{E(s["about"])}</p></header>
<div class="underlay">{viewer(svg_with(svg, asset(sdir, p.meta["plan_image"])), "pz-main")}</div>
<section class="block two-col">{status}<div class="card"><h3>По комнатам</h3><ul class="plain cols">{rooms_l}</ul></div></section>
<section class="block"><div class="rcards">{extra}</div></section>'''
            pages.append(Page(sdir, f"{s['name']}, {vname.lower()}", [home, obj_crumb, v_crumb, s_crumb], body, "section"))
            for x in s.get("extra", []):
                xdir = f"{sdir}/{x['id']}"
                xi = "".join(f"<li>{E(t)}</li>" for t in x.get("items", []))
                body = f'''<header class="phead compact"><div class="eyebrow">{vname} · {E(s["name"])}</div><h1>{E(x["name"])}</h1><p class="lede">{E(x["about"])}</p></header>
<div class="card draft"><h3>Страница в работе</h3><p>Здесь появятся:</p><ul>{xi}</ul></div>'''
                pages.append(Page(xdir, f"{x['name']}, {vname.lower()}", [home, obj_crumb, v_crumb, s_crumb, (x["name"], xdir)], body, "extra"))
            for r in o.ROOMS:
                rr = p.room(r, n)
                xdir = f"{sdir}/{r['id']}"
                body = f'''<header class="phead compact"><div class="eyebrow">{vname} · {E(s["name"])}</div><h1>{E(rr["name"])}<span class="m">{E(rr["area"])}</span></h1></header>
<div class="underlay">{viewer(svg_with(svg, asset(xdir, p.meta["plan_image"]), crop_box(rr["rect"])), "pz-room")}</div>
<section class="block two-col">{status}<div class="card"><h3>Эта комната</h3><ul class="plain"><li>{link(xdir, f"{vdir}/komnaty/{r['id']}", "Расстановка и заметки")}</li><li>{link(xdir, sdir, E(s["name"]) + " по всей квартире")}</li></ul></div></section>'''
                pages.append(Page(xdir, f"{s['name']}: {rr['name']}", [home, obj_crumb, v_crumb, s_crumb, (rr["name"], xdir)], body, "section"))
    return pages


def caption_for(p, shot):
    n = int(shot[1])
    key = shot.split("-", 1)[1]
    v = next(x for x in p.variants if x["n"] == n)
    return dict(v["gallery"]).get(key, key)


def gallery_html(p, page_dir, n, shots):
    shots = [(k, c) for k, c in shots if (p.dir / "renders" / f"v{n}-{k}.jpg").exists()]
    if not shots:
        return ""
    src = lambda k: rel(page_dir, f"{p.slug}/renders/v{n}-{k}.jpg")  # noqa: E731
    cap = dict(shots)
    hero, used = "", set()
    if "top" in cap and "doll_sw" in cap:
        side = figure(src("doll_sw"), cap["doll_sw"]) + (figure(src("doll_ne"), cap["doll_ne"]) if "doll_ne" in cap else "")
        hero = f'<div class="gallery-hero">{figure(src("top"), cap["top"], True, 900, 1170)}<div class="stack">{side}</div></div>'
        used = {"top", "doll_sw", "doll_ne"}
    rest = "".join(figure(src(k), c) for k, c in shots if k not in used)
    return f'{hero}<div class="gallery">{rest}</div>'


def index_page(projects):
    cards = []
    for p in projects:
        cards.append(f'''<a class="card vcard" href="{p.slug}/index.html">
  <img src="{p.slug}/{p.meta["cover"]}" alt="" loading="lazy" width="1200" height="800">
  <div class="vc-body"><div class="eyebrow">Объект</div><h3>{E(p.meta["title"])}</h3><p>{E(p.meta["subtitle"])}</p></div></a>''')
    body = f'''<header class="phead">
  <div class="eyebrow">Проекты</div>
  <h1>{SITE_TITLE}</h1>
  <p class="lede">Планировки, варианты отделки и проектная документация по объектам: расстановка мебели, 3D, электрика, сантехника и водопровод по всей квартире и по комнатам.</p>
</header>
<section class="block"><div class="vcards">{"".join(cards)}</div></section>'''
    return Page("", SITE_TITLE, [("Все объекты", "")], body, "home")


# ------------------------------------------------------------------ сборка
def build_site(root: Path):
    root = root.resolve()
    sys.path.insert(0, str(root / "tools"))
    out = root / "docs"
    projects = [Project(d) for d in sorted((root / "projects").iterdir()) if (d / "object.py").exists()]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    (out / ".nojekyll").write_text("")
    shutil.copytree(root / "site_assets", out / "assets")
    pages = [index_page(projects)]
    for p in projects:
        dst = out / p.slug
        dst.mkdir(parents=True)
        shutil.copy(p.dir / p.meta["plan_image"], dst / p.meta["plan_image"])
        for sub in ("renders", "models"):
            if (p.dir / sub).exists():
                shutil.copytree(p.dir / sub, dst / sub)
        pages += pages_for(p, projects)
    for pg in pages:
        d = out / pg.path if pg.path else out
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(render_page(pg, projects, out), encoding="utf-8")
    size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    print(f"docs/: {len(pages)} страниц, {size / 1e6:.1f} МБ")
    return pages
