#!/usr/bin/env python3
"""Serve docs/ em /baralho-democratico/ (como no GitHub Pages) e confere todos os links internos.

Uso: python3 tests/verificar_site.py
"""
import functools
import http.server
import re
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
PREFIXO = "/baralho-democratico/"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        for k in ("href", "src", "data-embed"):
            if a.get(k):
                self.links.append(a[k])


def main():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "baralho-democratico").symlink_to(DOCS)
    class Quieto(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    handler = functools.partial(Quieto, directory=str(tmp))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"

    paginas = sorted(DOCS.rglob("*.html"))
    erros, externos, vistos, ids = [], set(), {}, {}
    for p in paginas:
        rel = p.relative_to(DOCS).as_posix()
        url = base + PREFIXO + (rel[:-len("index.html")] if rel.endswith("index.html") else rel)
        try:
            corpo = urllib.request.urlopen(url).read().decode("utf-8")
        except urllib.error.HTTPError as e:
            erros.append(f"{url}: HTTP {e.code}")
            continue
        parser = Links()
        parser.feed(corpo)
        ids[url] = parser.ids
        if "—" in corpo:
            erros.append(f"{rel}: contém travessão")
        for l in parser.links:
            alvo = urljoin(url, l.replace("&amp;", "&"))
            u = urlparse(alvo)
            if u.scheme in ("http", "https") and u.netloc != urlparse(base).netloc:
                externos.add(u.netloc)
                continue
            if u.scheme not in ("http", "https"):
                continue
            vistos.setdefault(alvo.split("#")[0], []).append((rel, alvo))
    for alvo, origens in vistos.items():
        try:
            urllib.request.urlopen(alvo).read()
        except urllib.error.HTTPError as e:
            erros.append(f"{alvo} (de {origens[0][0]}): HTTP {e.code}")
    # âncoras internas
    for alvo, origens in vistos.items():
        for _, completo in origens:
            if "#" in completo:
                ancora = completo.split("#", 1)[1]
                pag = completo.split("#")[0]
                if ancora and pag in ids and ancora not in ids[pag]:
                    erros.append(f"âncora #{ancora} não existe em {pag}")
    srv.shutdown()
    (tmp / "baralho-democratico").unlink()
    print(f"{len(paginas)} páginas, {len(vistos)} alvos internos, domínios externos: {', '.join(sorted(externos))}")
    if erros:
        print("ERROS:")
        for e in sorted(set(erros)):
            print(" -", e)
        sys.exit(1)
    print("OK: nenhum link interno quebrado")


if __name__ == "__main__":
    main()
