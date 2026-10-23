#!/usr/bin/env python3
"""Gera os dois PDFs de impressão a partir de data/cartas.json.

Uso:
  uv run --with segno python3 make_pdfs.py [--cartas data/cartas.json] [--copiar-para PASTA]

Saída em docs/pdf/:
  baralho-democratico-duplex.pdf       A4 paisagem, 8 cartas por folha, versos espelhados (duplex, borda longa)
  baralho-democratico-4-por-folha.pdf  A4 retrato, 4 cartas grandes por folha, versos espelhados, marcas de corte
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import segno

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))
import cartas as C  # noqa: E402

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
RODAPE = (
    "Uso pessoal, não distribuir impresso. Baralho Democrático, versão de Luan Araújo baseada no "
    "Baralho 2026 do Coletivo do Baralho (linktr.ee/nossobaralho). Fontes: luanharaujo.github.io/baralho-democratico"
)


def qr_svg(url):
    q = segno.make(url, error="q", micro=False, boost_error=False)
    return q.svg_inline(border=2, omitsize=True, dark="#000000")


RODAPE_CURTO = "Uso pessoal, não distribuir impresso. Baralho Democrático (Luan Araújo, baseado no Baralho 2026). Fontes: luanharaujo.github.io/baralho-democratico"


def pagina(conteudo, cls, rodape=RODAPE):
    return f'<section class="pg {cls}">{conteudo}<p class="rodape">{C.esc(rodape)}</p></section>'


MANIFESTO = []  # (documento, página, x, y, largura, altura, url esperada) para o teste dos QR


def pos(x, y, html):
    return f'<div class="slot" style="left:{x:.2f}mm;top:{y:.2f}mm">{html}</div>'


def grade(cartas_html, colunas, linhas, cw, ch, gx, gy, pw, ph, espelhar, urls=None, doc=None, pg=None):
    """Posiciona até colunas x linhas cartas. Com espelhar, inverte as colunas (verso para duplex de borda longa)."""
    mx = (pw - (colunas * cw + (colunas - 1) * gx)) / 2
    my = (ph - (linhas * ch + (linhas - 1) * gy)) / 2
    out = []
    for i, h in enumerate(cartas_html):
        if h is None:
            continue
        lin, col = divmod(i, colunas)
        if espelhar:
            col = colunas - 1 - col
        x, y = mx + col * (cw + gx), my + lin * (ch + gy)
        out.append(pos(x, y, h))
        if urls and urls[i]:
            MANIFESTO.append({"doc": doc, "pagina": pg, "x": x, "y": y, "w": cw, "h": ch, "pw": pw, "ph": ph, "url": urls[i]})
    return "".join(out), mx, my


def marcas_corte(colunas, linhas, cw, ch, gx, gy, pw, ph, mx, my):
    """Linhas curtas nas margens, alinhadas às bordas das cartas."""
    xs, ys = [], []
    for c in range(colunas):
        x0 = mx + c * (cw + gx)
        xs += [x0, x0 + cw]
    for r in range(linhas):
        y0 = my + r * (ch + gy)
        ys += [y0, y0 + ch]
    folga = 2.0
    linhas_svg = []
    for x in xs:
        linhas_svg.append(f'<line x1="{x:.2f}" y1="2" x2="{x:.2f}" y2="{my - folga:.2f}"/>')
        linhas_svg.append(f'<line x1="{x:.2f}" y1="{ph - my + folga:.2f}" x2="{x:.2f}" y2="{ph - 7:.2f}"/>')
    for y in ys:
        linhas_svg.append(f'<line x1="2" y1="{y:.2f}" x2="{mx - folga:.2f}" y2="{y:.2f}"/>')
        linhas_svg.append(f'<line x1="{pw - mx + folga:.2f}" y1="{y:.2f}" x2="{pw - 2:.2f}" y2="{y:.2f}"/>')
    return (
        f'<svg class="marcas" viewBox="0 0 {pw} {ph}" width="{pw}mm" height="{ph}mm" '
        f'stroke="#000" stroke-width="0.2">{"".join(linhas_svg)}</svg>'
    )


def documento(paginas, pw, ph, cw, extra_css=""):
    fontes = C.css_fontes("../src/fonts/")
    carta_css = (RAIZ / "src" / "carta.css").read_text(encoding="utf-8")
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Baralho Democrático</title>
<style>
{fontes}
{carta_css}
@page {{ size: {pw}mm {ph}mm; margin: 0; }}
html, body {{ margin: 0; padding: 0; background: #fff; }}
.pg {{ position: relative; width: {pw}mm; height: {ph}mm; overflow: hidden; page-break-after: always; break-after: page; }}
.pg:last-child {{ page-break-after: auto; break-after: auto; }}
.slot {{ position: absolute; }}
.slot .carta {{ --cw: {cw}mm; }}
.rodape {{ position: absolute; left: 0; right: 0; bottom: 3.2mm; margin: 0; text-align: center;
  font: 6.5pt 'Aileron', Arial, sans-serif; color: #555; }}
.marcas {{ position: absolute; left: 0; top: 0; }}
{extra_css}
</style></head><body>
{"".join(paginas)}
{C.SCRIPT_AJUSTE}
</body></html>"""


def em_grupos(lista, n):
    return [lista[i:i + n] for i in range(0, len(lista), n)]


def gerar_duplex(jogo, compartilhe, importante):
    pw, ph = 297, 210
    cw, ch = 63, 88
    gx, gy = 5, 6
    paginas = []
    for grupo in em_grupos(jogo, 8):
        frentes = [C.frente(c) for c in grupo]
        versos = [C.verso(c, qr_svg(C.url_carta(c["id"]))) for c in grupo]
        h, _, _ = grade(frentes, 4, 2, cw, ch, gx, gy, pw, ph, False)
        paginas.append(pagina(h, "duplex frente"))
        urls = [C.url_carta(c["id"]) for c in grupo]
        h, _, _ = grade(versos, 4, 2, cw, ch, gx, gy, pw, ph, True, urls, "duplex", len(paginas) + 1)
        paginas.append(pagina(h, "duplex verso"))
    esp = []
    if compartilhe:
        esp += [C.carta_compartilhe(compartilhe, qr_svg(C.url_carta("compartilhe")))] * 4
    if importante:
        esp += [C.carta_importante(importante)] * 4
    if esp:
        urls = [C.url_carta("compartilhe") if "compartilhe" in e else None for e in esp]
        h, _, _ = grade(esp, 4, 2, cw, ch, gx, gy, pw, ph, False, urls, "duplex", len(paginas) + 1)
        paginas.append(pagina(h, "duplex especiais"))
    css = ".duplex .slot .carta { outline: 0.2mm solid #000; outline-offset: 0; }"
    return documento(paginas, pw, ph, cw, css)


def gerar_4(jogo, compartilhe, importante):
    pw, ph = 210, 297
    cw = 90
    ch = cw * 88 / 63
    gx, gy = 6, 6
    paginas = []
    for grupo in em_grupos(jogo, 4):
        frentes = [C.frente(c) for c in grupo]
        versos = [C.verso(c, qr_svg(C.url_carta(c["id"]))) for c in grupo]
        h, mx, my = grade(frentes, 2, 2, cw, ch, gx, gy, pw, ph, False)
        m = marcas_corte(2, 2, cw, ch, gx, gy, pw, ph, mx, my)
        paginas.append(pagina(m + h, "q4 frente", RODAPE_CURTO))
        urls = [C.url_carta(c["id"]) for c in grupo]
        h, _, _ = grade(versos, 2, 2, cw, ch, gx, gy, pw, ph, True, urls, "4-por-folha", len(paginas) + 1)
        paginas.append(pagina(m + h, "q4 verso", RODAPE_CURTO))
    esp = []
    if importante:
        esp += [C.carta_importante(importante)] * 2
    if compartilhe:
        esp += [C.carta_compartilhe(compartilhe, qr_svg(C.url_carta("compartilhe")))] * 2
    if esp:
        urls = [C.url_carta("compartilhe") if "compartilhe" in e else None for e in esp]
        h, mx, my = grade(esp, 2, 2, cw, ch, gx, gy, pw, ph, False, urls, "4-por-folha", len(paginas) + 1)
        paginas.append(pagina(marcas_corte(2, 2, cw, ch, gx, gy, pw, ph, mx, my) + h, "q4 especiais", RODAPE_CURTO))
    return documento(paginas, pw, ph, cw)


def imprimir(html_path, pdf_path):
    antes = pdf_path.stat().st_mtime if pdf_path.exists() else 0
    cmd = [
        CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
        "--virtual-time-budget=15000", "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={pdf_path}", html_path.as_uri(),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if not pdf_path.exists() or pdf_path.stat().st_size == 0 or pdf_path.stat().st_mtime <= antes:
        print(r.stdout, r.stderr)
        raise SystemExit(f"Falhou ao gerar {pdf_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cartas", default=str(RAIZ / "data" / "cartas.json"))
    ap.add_argument("--copiar-para", default=None, help="pasta extra para copiar os PDFs")
    a = ap.parse_args()

    todas = C.carregar(a.cartas)
    jogo = [c for c in todas if C.eh_jogo(c)]
    compartilhe = next((c for c in todas if c["id"] == "compartilhe"), None)
    importante = next((c for c in todas if c["id"] == "importante"), None)

    tmp = RAIZ / "build"
    tmp.mkdir(exist_ok=True)
    saida = RAIZ / "docs" / "pdf"
    saida.mkdir(parents=True, exist_ok=True)
    trabalhos = [
        ("baralho-democratico-duplex", gerar_duplex(jogo, compartilhe, importante)),
        ("baralho-democratico-4-por-folha", gerar_4(jogo, compartilhe, importante)),
    ]
    import json
    (tmp / "manifesto_qr.json").write_text(json.dumps(MANIFESTO, indent=1), encoding="utf-8")
    for nome, html in trabalhos:
        hp = tmp / f"{nome}.html"
        hp.write_text(html, encoding="utf-8")
        pdf = saida / f"{nome}.pdf"
        imprimir(hp, pdf)
        print("ok", pdf)
        if a.copiar_para:
            dest = Path(a.copiar_para)
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pdf, dest / pdf.name)
            print("copiado para", dest / pdf.name)


if __name__ == "__main__":
    main()
