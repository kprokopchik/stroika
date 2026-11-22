"""Отдельный комплект SVG/HTML для обсуждения щита, без публикации.

python3 projects/kvartira-95/export_panel.py /workspace/visualizations/kvartira-95/panel-simplified
"""
from pathlib import Path
from html import escape
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from panel_readable import supply_svg, overview_svg, priority_svg, bank_svg, branch_svg
from panel_model import BANKS
import eng


def export(destination):
    destination.mkdir(parents=True, exist_ok=True)
    sheets = [
        ("01-overview", "Общая схема", supply_svg()),
        ("02-mounting", "Расположение аппаратов и гребёнки", overview_svg()),
        ("03-control", "Управление единственной ступенью", priority_svg()),
    ]
    sheets += [(f"0{i+4}-{bank.lower()}", bank+" · "+data[0], bank_svg(bank))
               for i, (bank, data) in enumerate(BANKS.items())]
    sheets += [("08-cabinet", "Техническая секция", eng.cabinet_svg())]
    sheets += [("09-branches", "Локальные разветвления санузлов и кондиционеров", branch_svg())]
    for name, _, svg in sheets:
        (destination / (name+".svg")).write_text(svg, encoding="utf-8")
    html = '''<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Квартира 95,7 м² · упрощённый щит</title><style>
body{font:16px Arial,sans-serif;color:#233945;background:#edf2f4;margin:0}
main{max-width:1600px;margin:auto;padding:24px}h1{font-size:30px}
p{line-height:1.6;max-width:1100px}section{background:white;margin:24px 0;padding:18px;border:1px solid #ccd6dc;border-radius:12px}
svg{display:block;width:100%;height:auto}nav{display:flex;flex-wrap:wrap;gap:14px}a{color:#126987}
@media print{@page{size:A3 landscape;margin:10mm}body{background:white}main{padding:0}header{display:none}
section{break-before:page;border:none;margin:0;padding:0;break-inside:avoid}section:first-of-type{break-before:auto}
h2{font-size:14px;margin:0 0 4mm}section svg{max-height:255mm;width:100%;height:255mm}}
@media(max-width:600px){main{padding:10px}section{padding:8px}h1{font-size:23px}}
</style><main><header><h1>Щит: 13 линий, 4 УЗО, одна ступень разгрузки</h1>
<p>1 фаза 230 В / 50 А — допущение, выделено 10 кВт. Корпус предварительно 54 модуля.
Санузлы с полами объединены в QF15, два кондиционера — в QF20. Техника связи и защита
от протечек питаются от QF8. УЗО ввода предполагается в этажном щите. УЗИП — резерв
до уточнения защиты здания. Маркировки клемм функциональные; аппараты, токи утечки,
допустимость отключения кондиционеров и настройки проверяются до монтажа.</p><nav>'''
    html += "".join(f'<a href="#{name}">{escape(title)}</a>' for name, title, _ in sheets)
    html += '</nav><p><a href="panel-final.pdf">Все листы PDF</a></p></header>'
    html += "".join(f'<section id="{name}"><h2>{escape(title)}</h2>{svg}</section>' for name, title, svg in sheets)
    html += "</main></html>"
    (destination / "index.html").write_text(html, encoding="utf-8")
    return sheets


if __name__ == "__main__":
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tmp/panel-review")
    print(f"{len(export(destination))} листов: {destination.resolve()}")
