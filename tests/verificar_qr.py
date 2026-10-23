#!/usr/bin/env python3
"""Decodifica todos os QR dos PDFs e confere se cada um aponta para a carta certa.

Uso: uv run --with opencv-python-headless python3 tests/verificar_qr.py
(rode make_pdfs.py antes: ele grava build/manifesto_qr.json com a posição de cada QR)
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2

RAIZ = Path(__file__).resolve().parent.parent
DPI = 300
PDFS = {"duplex": "baralho-democratico-duplex.pdf", "4-por-folha": "baralho-democratico-4-por-folha.pdf"}


def main():
    manifesto = json.loads((RAIZ / "build" / "manifesto_qr.json").read_text())
    tmp = Path(tempfile.mkdtemp())
    det = cv2.QRCodeDetector()
    ok, erros = 0, []
    cache = {}
    for m in manifesto:
        chave = (m["doc"], m["pagina"])
        if chave not in cache:
            base = tmp / f"{m['doc']}-{m['pagina']}"
            subprocess.run(["pdftoppm", "-r", str(DPI), "-png", "-singlefile", "-f", str(m["pagina"]), "-l", str(m["pagina"]),
                            str(RAIZ / "docs" / "pdf" / PDFS[m["doc"]]), str(base)], check=True)
            cache[chave] = cv2.imread(str(base) + ".png")
        img = cache[chave]
        k = DPI / 25.4
        x0, y0 = int(m["x"] * k), int(m["y"] * k)
        recorte = img[y0:y0 + int(m["h"] * k), x0:x0 + int(m["w"] * k)]
        txt, _, _ = det.detectAndDecode(recorte)
        if not txt:
            # tenta reduzido (o detector às vezes prefere imagem menor)
            txt, _, _ = det.detectAndDecode(cv2.resize(recorte, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA))
        if txt == m["url"]:
            ok += 1
        else:
            erros.append(f"{m['doc']} pág. {m['pagina']} ({m['x']:.0f},{m['y']:.0f} mm): esperado {m['url']}, lido {txt!r}")
    print(f"{ok}/{len(manifesto)} QR conferem")
    for e in erros:
        print(" ERRO", e)
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()
