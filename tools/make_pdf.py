"""PDF для печати: планы вариантов (A3, масштаб 1:50), разделы (план A3 + таблицы A4),
щит, коллектор, шкаф (A4) и альбом варианта со всеми листами.

    python3 tools/make_pdf.py            # все объекты → projects/<объект>/pdf/*.pdf
    python3 tools/make_pdf.py kvartira-95

Нужны Node.js и Playwright с Chromium (npm i playwright && npx playwright install chromium).
Сам сайт по-прежнему собирается без них: build.py просто копирует готовые PDF и ставит ссылки.
"""
import datetime
import base64
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import site_gen as G  # noqa: E402

E = G.E
TMP = ROOT / "tmp" / "print"
SCALES = (50, 75, 100)               # масштабы плана, 1:N
A3_FIELD = (273, 330)                # место под план на листе A3, мм


def plan_svg_print(svg, vb):
    """План в точном масштабе: ширина и высота в мм, без подложки застройщика."""
    x, y, w, h = vb
    for n in SCALES:
        wm, hm = w * 10 / n, h * 10 / n
        if wm <= A3_FIELD[0] and hm <= A3_FIELD[1]:
            break
    s = re.sub(r'<image class="orig"[^>]*/>', "", svg)
    s = s.replace("<svg ", f'<svg width="{wm:.1f}mm" height="{hm:.1f}mm" ', 1)
    return s, n


def blocks_print(blocks):
    out = []
    for b in blocks:
        kind = b[0]
        if kind == "links":
            _, title, links = b
            items=[]
            for label, href, description in links:
                name=f'<b>{E(label)}</b>'
                if href.startswith(('https://','http://')):
                    name=f'<a href="{E(href, quote=True)}">{name}</a>'
                items.append(f'<li>{name}: {E(description)}</li>')
            out.append(f'<h3>{E(title)}</h3><ul>' + ''.join(items) + '</ul>')
        elif kind == "image":
            _, title, data, caption = b
            file = Path(data["file"])
            if file.exists():
                source = 'data:image/png;base64,' + base64.b64encode(file.read_bytes()).decode()
                out.append(f'<div class="pdiag"><h3>{E(title)}</h3><img src="{source}" style="display:block;max-width:100%;height:175mm;object-fit:contain;margin:auto"><p class="sub">{caption}</p></div>')
        elif kind == "cards":
            out.append('<div class="pcards">' + "".join(G.note_card(t, m, lis) for t, m, lis in b[1]) + "</div>")
        elif kind == "details":
            out.append(f'<h2>{E(b[2])}</h2>'+blocks_print(b[3]))
        elif kind == "sheet":
            _, key, title, children = b
            out.append(f'<section class="pdetail" id="{E(key)}"><h2>{E(title)}</h2>'
                       f'{blocks_print(children)}</section>')
        elif kind == "table":
            out.append(G.table_html(*b[1:]))
        elif kind == "filter_table":
            title, heads, rows, note = b[1:]
            compact = [[row[i] for i in (0, 1, 2, 5, 6, 7)] for row in rows]
            out.append(G.table_html(title, ['Код', 'Этап', 'Позиция', 'Купить', '₽/уп.', 'Итого ₽'], compact,
                                    'Источники, формулы расхода и примечания — в Excel/CSV и на странице закупок. Цены — предварительные допуски.'))
        elif kind == "circuit_browser":
            _, title, circuits, info = b
            out.append(f'<h3>{E(title)}</h3><p class="sub">В печати: управление разгрузкой и соединения блоков групповой защиты. Адреса клемм и кабелей — в таблицах.</p>')
            for c in circuits:
                if c.get("print"):
                    out.append(f'<div class="pdiag"><h3>{E(c["title"])}</h3><div class="pd-fig">{c["svg"]}</div></div>')
            items = "".join(f'<div class="pi"><h4>{t} <span class="m">{sub}</span></h4>{body}</div>' for k, t, sub, body in info)
            out.append(f'<div class="pinfo"><h3>Аппараты щита</h3>{items}</div>')
        elif kind == "diagram":
            _, title, svg, note, *rest = b
            info = rest[0] if rest else None
            out.append(f'<div class="pdiag"><h3>{E(title)}</h3><div class="pd-fig">{svg}</div>'
                       + (f'<p class="sub">{note}</p>' if note else "") + "</div>")
            if info:
                items = "".join(f'<div class="pi"><h4>{t} <span class="m">{sub}</span></h4>{body}</div>' for k, t, sub, body in info)
                out.append(f'<div class="pinfo"><h3>Аппараты щита</h3>{items}</div>')
        elif kind == "p":
            out.append(f"<p>{b[1]}</p>")
        elif kind == "h2":
            out.append(f"<h2>{E(b[1])}</h2>")
    return "".join(out)


def head(eyebrow, title, sub=""):
    s = f'<p class="sub">{sub}</p>' if sub else ""
    return f'<header class="sh-head"><div class="eyebrow">{E(eyebrow)}</div><h1>{E(title)}</h1>{s}</header>'


def sheet_plan(eyebrow, title, svg, vb, legend, note="", eng=False):
    s, n = plan_svg_print(svg, vb)
    return (f'<section class="sheet a3{" engplan" if eng else ""}">{head(eyebrow, title, f"Масштаб 1:{n} на листе A3. Размеры в сантиметрах. {note}")}'
            f'<div class="pfig">{s}</div>{legend}</section>')


def sheet_text(eyebrow, title, lede, blocks):
    return f'<section class="sheet a4">{head(eyebrow, title, E(lede))}{blocks_print(blocks)}</section>'


def html_doc(title, sections):
    css = (ROOT / "site_assets" / "print.css").read_text(encoding="utf-8")
    body = re.sub(r"Нажмите на [^.<]*?\.\s*", "", "".join(sections))   # на бумаге нажимать некуда
    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>{E(title)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Golos+Text:wght@400;500;600;700&family=Unbounded:wght@600;700&family=JetBrains+Mono:wght@500;600&display=swap">
<style>{css}</style></head><body>{body}</body></html>'''


def sheets_for(p):
    """Документы объекта: [(имя файла без .pdf, заголовок, [секции])]."""
    o = p.obj
    docs = []
    for v in p.variants:
        n = v["n"]
        eb = f'{p.meta["title"]} · вариант {n}'
        album = []
        svg = p.svg[n]
        vb = p.layout.VIEWBOX
        sec = sheet_plan(eb, f"План расстановки: {v['title']}", svg, vb, G.LEGEND)
        docs.append((f"v{n}-plan", f"План расстановки, вариант {n}", [sec]))
        album.append(sec)
        for s in o.SECTIONS:
            D = p.sec(s, n)
            if not D:
                continue
            plan = sheet_plan(eb, s["name"], G.with_overlay(svg, D["overlay"]), vb, G.legend_html(D["legend"]),
                              "Номера в серых кружках — группы щита." if s["id"] == "elektrika" else "", eng=True)
            text = sheet_text(eb, f'{s["name"]}: пояснения', D["lede"], D["blocks"])
            section_sheets = [text] if D.get("hide_plan") else [plan, text]
            docs.append((f"v{n}-{s['id']}", f'{s["name"]}, вариант {n}', section_sheets))
            album += section_sheets
            for x in s.get("extra", []):
                X = D["extras"].get(x["id"])
                if not X:
                    continue
                t = sheet_text(eb, x["name"], X["lede"], X.get("pdf_blocks", X["blocks"]))
                extra_sheets = []
                if X.get("overlay"):
                    extra_sheets.append(sheet_plan(eb, x["name"], G.with_overlay(svg, X["overlay"]), vb, G.legend_html(X.get("legend", [])), eng=True))
                extra_sheets.append(t)
                docs.append((f"v{n}-{s['id']}-{x['id']}", f'{x["name"]}, вариант {n}', extra_sheets))
                album += extra_sheets
        if len(album) > 1:
            items = "".join(f"<li>{E(t)}</li>" for name, t, _ in docs if name.startswith(f"v{n}-") and name != f"v{n}-album")
            cover = (f'<section class="sheet a4 cover">{head(p.meta["title"], f"Вариант {n}: все листы", E(v["title"]))}'
                     f'<p>{E(p.meta["about"])}</p><h2>Состав</h2><ol>{items}</ol>'
                     f'<p class="sub">Собрано {datetime.date.today().strftime("%d.%m.%Y")}. Живая версия с зумом — на сайте проекта.</p></section>')
            docs.append((f"v{n}-album", f"Вариант {n}: все листы", [cover] + album))
    return docs


def main(only=None):
    projects = [G.Project(d) for d in sorted((ROOT / "projects").iterdir()) if (d / "object.py").exists()]
    if only:
        projects = [p for p in projects if p.slug in only]
    if TMP.exists():
        shutil.rmtree(TMP)
    jobs = []
    date = datetime.date.today().strftime("%d.%m.%Y")
    for p in projects:
        out = p.dir / "pdf"
        if out.exists():
            shutil.rmtree(out)
        out.mkdir()
        (TMP / p.slug).mkdir(parents=True)
        for name, title, sections in sheets_for(p):
            h = TMP / p.slug / f"{name}.html"
            h.write_text(html_doc(title, sections), encoding="utf-8")
            jobs.append({"html": str(h), "pdf": str(out / f"{name}.pdf"),
                         "footer": f'Стройка · {p.meta["title"]} · {title} · {date}'})
    manifest = TMP / "manifest.json"
    manifest.write_text(json.dumps(jobs, ensure_ascii=False, indent=1), encoding="utf-8")
    subprocess.run(["node", str(ROOT / "tools" / "pdf.js"), str(manifest)], check=True)
    total = sum(Path(j["pdf"]).stat().st_size for j in jobs)
    print(f"PDF: {len(jobs)} файлов, {total / 1e6:.1f} МБ. Теперь python3 build.py")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
