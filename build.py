#!/usr/bin/env python3
"""Gera o site estático em docs/ a partir de data/cartas.json.

Uso:
  python3 build.py                      # usa data/cartas.json
  python3 build.py /caminho/cartas.json # copia esse arquivo para data/cartas.json e gera

Só biblioteca padrão. Os PDFs são gerados à parte por make_pdfs.py (ficam em docs/pdf/).
"""
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse, parse_qs

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))
import cartas as C  # noqa: E402

DOCS = RAIZ / "docs"
ORIGINAL = "https://linktr.ee/nossobaralho"
CREDITO = (
    'Baseado no <a href="https://linktr.ee/nossobaralho">Baralho 2026</a> do Coletivo do Baralho / Regiane '
    '(linktr.ee/nossobaralho). Versão atualizada por Luan Araújo.'
)
PDF_DUPLEX = "pdf/baralho-democratico-duplex.pdf"
PDF_4 = "pdf/baralho-democratico-4-por-folha.pdf"

ACABAMENTO = [
    ("9", "O número do canto de baixo, de cabeça para baixo, parecia um “6” (e o da carta 6 parecia um “9”). Agora 6 e 9 têm um traço embaixo, como nos baralhos comuns, e o canto de baixo é o mesmo bloco do canto de cima girado."),
    ("27", "Havia um “8” sobreposto ao naipe no canto de baixo. Removido."),
    ("todas", "Os QR codes do original levavam a um encurtador do Linktree. Agora levam a uma página deste site, com a fonte, a data e um vídeo curto, que pode ser atualizada se uma matéria sair do ar."),
    ("todas", "Pontuação revisada (aspas que não fechavam, espaço antes do ponto)."),
]


# ---------------- utilidades ----------------

def data_br(s):
    if not s:
        return ""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(3)}/{m.group(2)}/{m.group(1)}"
    m = re.match(r"^(\d{4})-(\d{2})$", s)
    if m:
        return f"{m.group(2)}/{m.group(1)}"
    return C.esc(s)


def inline_md(t):
    t = C.esc(t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    return t


def md(texto):
    """Markdown simples: parágrafos, listas com '- ', **negrito**, *itálico*, [link](url)."""
    if not texto:
        return ""
    if isinstance(texto, list):
        texto = "\n\n".join(texto)
    out = []
    for bloco in re.split(r"\n\s*\n", texto.strip()):
        linhas = [l.rstrip() for l in bloco.splitlines() if l.strip()]
        if linhas and all(re.match(r"^\s*[-*] ", l) for l in linhas):
            itens = "".join(f"<li>{inline_md(re.sub(r'^\s*[-*] ', '', l))}</li>" for l in linhas)
            out.append(f"<ul>{itens}</ul>")
        else:
            out.append(f"<p>{inline_md(' '.join(l.strip() for l in linhas))}</p>")
    return "\n".join(out)


def youtube_id(url):
    if not url:
        return None
    u = urlparse(url)
    host = u.netloc.lower()
    if "youtu.be" in host:
        return u.path.strip("/").split("/")[0] or None
    if "youtube" in host:
        if u.path.startswith("/watch"):
            return parse_qs(u.query).get("v", [None])[0]
        m = re.match(r"^/(embed|shorts|live|v)/([^/?]+)", u.path)
        if m:
            return m.group(2)
    return None


def segundos(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def mmss(s):
    return f"{s // 60}:{s % 60:02d}"


# ---------------- pedaços de página ----------------

def cabecalho(pref, titulo, descricao):
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{C.esc(titulo)}</title>
<meta name="description" content="{C.esc(descricao)}">
<meta name="referrer" content="no-referrer">
<meta name="color-scheme" content="light">
<link rel="icon" href="{pref}assets/icone.svg" type="image/svg+xml">
<link rel="stylesheet" href="{pref}assets/estilo.css">
</head>
<body>
<a class="pular" href="#conteudo">Pular para o conteúdo</a>
<header class="topo"><a href="{pref}" class="marca"><span class="marca-naipes" aria-hidden="true">♥ ♠ ♦ ♣</span> Baralho Democrático</a></header>
<main id="conteudo">
"""


def rodape(pref):
    return f"""</main>
<footer class="rodape">
<p>{CREDITO}</p>
<p>Site mantido por <strong>Luan Araújo</strong>, como cidadão, sem impulsionamento pago. Não usa cookies nem rastreadores; os vídeos só carregam do YouTube se você tocar para assistir.</p>
<p><a href="{pref}">Início</a> · <a href="{pref}correcoes/">O que mudou em relação ao original</a> · <a href="{pref}#baixar">Baixar o baralho</a></p>
</footer>
{C.SCRIPT_AJUSTE}
<script src="{pref}assets/video.js" defer></script>
</body>
</html>
"""


def bloco_video(v):
    if not v:
        return ""
    url = v.get("url") or ""
    plataforma = (v.get("plataforma") or "").lower()
    ini = segundos(v.get("inicio_s"))
    fim = segundos(v.get("fim_s"))
    titulo = v.get("titulo") or "Vídeo"
    meta = []
    if v.get("canal"):
        meta.append(C.esc(v["canal"]))
    if v.get("data"):
        meta.append(data_br(v["data"]))
    trecho = ""
    if ini is not None and fim is not None and fim > ini:
        trecho = f"Trecho de {mmss(ini)} a {mmss(fim)} ({fim - ini} s)"
    legenda = f'<p class="video-meta">{" · ".join(meta)}{" · " if meta and trecho else ""}{trecho}</p>'
    oque = f'<p class="video-oque">{C.esc(v["o_que_mostra"])}</p>' if v.get("o_que_mostra") else ""
    yid = youtube_id(v.get("embed")) or youtube_id(url)
    if plataforma in ("youtube", "") and yid:
        params = ["rel=0", "playsinline=1", "autoplay=1"]
        if ini is not None:
            params.append(f"start={ini}")
        if fim is not None:
            params.append(f"end={fim}")
        emb = f"https://www.youtube-nocookie.com/embed/{yid}?{'&amp;'.join(params)}"
        link = url or f"https://www.youtube.com/watch?v={yid}"
        if ini:
            link_t = f"https://www.youtube.com/watch?v={yid}&amp;t={ini}s"
        else:
            link_t = C.esc(link)
        return f"""<section class="video" aria-labelledby="tit-video">
<h2 id="tit-video">Vídeo</h2>
<div class="video-caixa" data-embed="{emb}" data-titulo="{C.esc(titulo)}">
<a class="video-play" href="{link_t}" target="_blank" rel="noopener">
<span class="play" aria-hidden="true">▶</span>
<span class="video-tit">{C.esc(titulo)}</span>
<span class="video-aviso">Tocar para assistir (carrega o player do YouTube)</span>
</a>
</div>
{legenda}{oque}
</section>"""
    rotulo = {"instagram": "Instagram"}.get(plataforma, "site de origem")
    return f"""<section class="video" aria-labelledby="tit-video">
<h2 id="tit-video">Vídeo</h2>
<p><a class="botao" href="{C.esc(url)}" target="_blank" rel="noopener">▶ {C.esc(titulo)} (abre no {rotulo})</a></p>
{legenda}{oque}
</section>"""


def bloco_fontes(fontes):
    if not fontes:
        return '<section class="fontes"><h2>Fontes</h2><p class="pendente">Fontes em verificação.</p></section>'
    itens = []
    for f in fontes:
        sel = ' <span class="selo">oficial</span>' if f.get("oficial") else ""
        veic = C.esc(f.get("veiculo") or "")
        dt = data_br(f.get("data"))
        quem = " · ".join(x for x in [f"<strong>{veic}</strong>" if veic else "", dt] if x)
        itens.append(
            f'<li><a href="{C.esc(f.get("url") or "#")}" target="_blank" rel="noopener">{C.esc(f.get("titulo") or f.get("url") or "")}</a>'
            f'<span class="fonte-meta">{quem}{sel}</span></li>'
        )
    return f'<section class="fontes"><h2>Fontes</h2><ol>{"".join(itens)}</ol></section>'


def navegacao(pref, jogo, i):
    ant = jogo[i - 1] if i > 0 else None
    prox = jogo[i + 1] if i + 1 < len(jogo) else None
    partes = []
    if ant:
        partes.append(f'<a class="nav-ant" href="{pref}c/{ant["id"]}/">← Carta {C.esc(C.valor(ant))}</a>')
    else:
        partes.append("<span></span>")
    partes.append(f'<a class="nav-todas" href="{pref}#cartas">Todas</a>')
    if prox:
        partes.append(f'<a class="nav-prox" href="{pref}c/{prox["id"]}/">Carta {C.esc(C.valor(prox))} →</a>')
    else:
        partes.append("<span></span>")
    return f'<nav class="nav-cartas" aria-label="Outras cartas">{"".join(partes)}</nav>'


def mini_lista(pref, jogo, atual=None):
    itens = []
    for c in jogo:
        cur = ' aria-current="page"' if atual and c["id"] == atual else ""
        itens.append(
            f'<li><a href="{pref}c/{c["id"]}/"{cur} class="mini n-{c["naipe"]}">'
            f'<span class="mini-v">{C.esc(C.valor(c))}</span><span class="mini-n">{C.SVG_NAIPE[c["naipe"]]}</span></a></li>'
        )
    return f'<ul class="grade-mini">{"".join(itens)}</ul>'


# ---------------- páginas ----------------

def pagina_carta(c, jogo, i):
    pref = "../../"
    t = C.sem_aspas(C.texto(c))
    cand = C.CANDIDATOS_NOME.get(c.get("candidato") or "", "")
    titulo = c.get("titulo_pagina") or f"Carta {C.valor(c)}: {t}"
    status = c.get("status")
    aviso = ""
    if status in ("ajustada", "reescrita"):
        rot = "reescrita" if status == "reescrita" else "ajustada"
        mot = f" {C.esc(c['motivo_mudanca'])}" if c.get("motivo_mudanca") else ""
        aviso = (
            f'<aside class="aviso"><p><strong>Carta {rot} nesta versão.</strong>{mot} '
            f'<a href="{pref}correcoes/#c-{c["id"]}">Ver o texto original</a>.</p></aside>'
        )
    explic = md(c.get("explicacao")) or '<p class="pendente">Explicação em preparação.</p>'
    atualizado = data_br(c.get("verificado_em")) or "em verificação"
    return (
        cabecalho(pref, f"Carta {C.valor(c)} · Baralho Democrático", t)
        + f"""<article class="carta-pagina">
<div class="dupla">
<figure class="lado"><figcaption>Frente</figcaption>{C.frente(c)}</figure>
<figure class="lado"><figcaption>Verso</figcaption>{C.verso(c)}</figure>
</div>
<p class="quem">Quem propõe ou fez: <strong class="cand-{C.esc(c.get('candidato') or '')}">{C.esc(cand)}</strong></p>
<h1>{C.esc(titulo)}</h1>
{aviso}
<div class="explicacao">{explic}</div>
{bloco_video(c.get("video"))}
{bloco_fontes(c.get("fontes"))}
<p class="atualizado">Conferido em <strong>{atualizado}</strong>. Achou erro ou link quebrado? Avise Luan Araújo.</p>
{navegacao(pref, jogo, i)}
<section class="todas"><h2>Outras cartas</h2>{mini_lista(pref, jogo, c["id"])}</section>
</article>
"""
        + rodape(pref)
    )


def pagina_compartilhe(c):
    pref = "../../"
    titulo, corpo = C.titulo_e_corpo(c, "Compartilhe!") if c else ("Compartilhe!", "")
    return (
        cabecalho(pref, "Compartilhe · Baralho Democrático", "Baixe e compartilhe o Baralho Democrático")
        + f"""<article class="carta-pagina">
<h1>{C.esc(titulo)}</h1>
<p>{C.esc(corpo)}</p>
{bloco_baixar(pref)}
<p><a class="botao" href="{pref}">Conhecer o jogo e ver todas as cartas</a></p>
</article>
"""
        + rodape(pref)
    )


def bloco_baixar(pref):
    return f"""<section id="baixar" class="baixar">
<h2>Baixar o baralho</h2>
<ul class="downloads">
<li><a class="botao" href="{pref}{PDF_DUPLEX}" download>Baralho completo (PDF, 8 cartas por folha)</a>
<span>Mesmo formato do original: A4 deitado, imprimir frente e verso virando pela borda longa.</span></li>
<li><a class="botao" href="{pref}{PDF_4}" download>Cartas grandes (PDF, 4 por folha)</a>
<span>Mais fácil de ler. A4 em pé, frente e verso pela borda longa, com marcas de corte.</span></li>
</ul>
<p class="nota">Para uso pessoal, para jogar em casa. Não distribua impresso.</p>
</section>"""


def pagina_inicio(jogo, importante):
    pref = ""
    _, regra = C.titulo_e_corpo(importante, "Importante") if importante else ("", "")
    itens = []
    for c in jogo:
        itens.append(
            f'<li><a href="c/{c["id"]}/" class="item n-{c["naipe"]}">'
            f'<span class="item-idx"><span class="mini-v">{C.esc(C.valor(c))}</span><span class="mini-n">{C.SVG_NAIPE[c["naipe"]]}</span></span>'
            f'<span class="item-txt">{C.esc(C.sem_aspas(C.texto(c)))}</span></a></li>'
        )
    exemplo = C.frente(jogo[0]) if jogo else ""
    return (
        cabecalho(pref, "Baralho Democrático", "Um jogo de cartas para conversar sobre propostas: isso é bom ou ruim?")
        + f"""<section class="hero">
<div class="hero-txt">
<h1>Baralho Democrático</h1>
<p class="lead">Um jogo de cartas para conversar sobre propostas, sem briga: primeiro você julga a ideia, depois descobre de quem ela é.</p>
<p>Cada carta tem uma frase. Você lê e responde: <strong>isso é bom ou ruim?</strong> Depois vira a carta e vê se é de Lula ou de Flávio Bolsonaro. O QR code do verso leva a uma página com a fonte, a data e um vídeo curto.</p>
</div>
<div class="hero-carta" aria-hidden="true">{exemplo}</div>
</section>
<section class="como">
<h2>Como jogar</h2>
<p>{C.esc(regra)}</p>
<ol>
<li>Embaralhe e mostre só a frente da carta (a frase).</li>
<li>A pessoa diz se acha aquilo bom ou ruim, por conta própria.</li>
<li>Vire a carta: veja quem defende ou fez aquilo.</li>
<li>Ficou na dúvida? Aponte a câmera do celular para o QR code e veja a fonte.</li>
</ol>
</section>
{bloco_baixar(pref)}
<section id="cartas" class="cartas">
<h2>As cartas</h2>
<p>Toque numa carta para ver a explicação, a fonte e o vídeo.</p>
<ul class="lista-cartas">{"".join(itens)}</ul>
</section>
<section class="sobre">
<h2>Sobre esta versão</h2>
<p>Esta é uma versão atualizada do <a href="{ORIGINAL}">Baralho 2026</a>, criado pelo Coletivo do Baralho (Regiane). As cartas de Lula foram mantidas; as frases atribuídas a Flávio Bolsonaro que não tinham fonte ou repetiam boatos foram reescritas no mesmo tema, com fato verificável e fonte. <a href="correcoes/">Veja o que mudou</a>.</p>
<p>O jogo original, com o PDF e a versão online, está em <a href="{ORIGINAL}">linktr.ee/nossobaralho</a>.</p>
</section>
"""
        + rodape(pref)
    )


def pagina_correcoes(todas, jogo):
    pref = "../"
    mudadas = [c for c in jogo if c.get("status") in ("ajustada", "reescrita")]
    pont = [
        c for c in jogo
        if c.get("status") not in ("ajustada", "reescrita")
        and c.get("texto_carta")
        and C.sem_aspas(c["texto_carta"]) != (c.get("texto_original") or "").strip()
    ]
    linhas = []
    for c in mudadas:
        rot = "Reescrita" if c["status"] == "reescrita" else "Ajustada"
        linhas.append(f"""<article class="corr" id="c-{c['id']}">
<h3><a href="{pref}c/{c['id']}/">Carta {C.esc(C.valor(c))}</a> <span class="selo st-{c['status']}">{rot}</span></h3>
<dl>
<dt>No original</dt><dd class="riscado">“{C.esc(C.sem_aspas(c.get('texto_original') or ''))}”</dd>
<dt>Nesta versão</dt><dd>“{C.esc(C.sem_aspas(C.texto(c)))}”</dd>
{f"<dt>Por quê</dt><dd>{C.esc(c['motivo_mudanca'])}</dd>" if c.get('motivo_mudanca') else ""}
</dl>
</article>""")
    if not linhas:
        linhas.append('<p class="pendente">Lista em preparação.</p>')
    pont_html = ""
    if pont:
        li = "".join(
            f'<li id="c-{c["id"]}"><a href="{pref}c/{c["id"]}/">Carta {C.esc(C.valor(c))}</a>: “{C.esc(C.sem_aspas(c["texto_carta"]))}”</li>'
            for c in pont
        )
        pont_html = f"<h2>Ajustes de redação</h2><p>Mesmo sentido, só revisão de texto ou pontuação.</p><ul>{li}</ul>"
    acab = "".join(
        f"<li><strong>{'Todas as cartas' if k == 'todas' else 'Carta ' + k}:</strong> {C.esc(v)}</li>" for k, v in ACABAMENTO
    )
    return (
        cabecalho(pref, "O que mudou · Baralho Democrático", "Correções em relação ao Baralho 2026 original")
        + f"""<article class="correcoes">
<h1>O que mudou em relação ao original</h1>
<p>O <a href="{ORIGINAL}">Baralho 2026</a> original tem 32 cartas. Esta versão mantém os mesmos temas e a mesma ordem. Corrigimos as frases que não tinham fonte, que repetiam boatos já desmentidos ou que atribuíam a uma pessoa algo que ela não disse. Num jogo cujo ponto é “confira a fonte”, cada carta precisa se sustentar.</p>
<h2>Cartas com texto novo</h2>
{"".join(linhas)}
{pont_html}
<h2>Acabamento</h2>
<ul>{acab}</ul>
</article>
"""
        + rodape(pref)
    )


ICONE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect x="10" y="4" width="44" height="56" rx="7" fill="#fff" stroke="#1d1d1d" stroke-width="4"/><path fill="#9b1b30" d="M32 47C21 38 16 32 16 25c0-5 4-9 9-9 3 0 6 2 7 5 1-3 4-5 7-5 5 0 9 4 9 9 0 7-5 13-16 22z"/></svg>"""


def main():
    origem = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    dados = RAIZ / "data" / "cartas.json"
    if origem:
        dados.parent.mkdir(exist_ok=True)
        shutil.copy2(origem, dados)
        print("copiado:", origem, "->", dados)
    todas = C.carregar(dados)
    jogo = [c for c in todas if C.eh_jogo(c)]
    compartilhe = next((c for c in todas if c["id"] == "compartilhe"), None)
    importante = next((c for c in todas if c["id"] == "importante"), None)

    DOCS.mkdir(exist_ok=True)
    assets = DOCS / "assets"
    (assets / "fontes").mkdir(parents=True, exist_ok=True)
    for f in (RAIZ / "src" / "fonts").glob("*.woff2"):
        shutil.copy2(f, assets / "fontes" / f.name)
    css = C.css_fontes("fontes/") + (RAIZ / "src" / "carta.css").read_text(encoding="utf-8") + (RAIZ / "src" / "site.css").read_text(encoding="utf-8")
    (assets / "estilo.css").write_text(css, encoding="utf-8")
    shutil.copy2(RAIZ / "src" / "video.js", assets / "video.js")
    (assets / "icone.svg").write_text(ICONE, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    def gravar(rel, conteudo):
        p = DOCS / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(conteudo, encoding="utf-8")

    gravar("index.html", pagina_inicio(jogo, importante))
    gravar("correcoes/index.html", pagina_correcoes(todas, jogo))
    for i, c in enumerate(jogo):
        gravar(f"c/{c['id']}/index.html", pagina_carta(c, jogo, i))
    gravar("c/compartilhe/index.html", pagina_compartilhe(compartilhe))
    gravar("404.html", cabecalho("/baralho-democratico/", "Página não encontrada", "")
           + '<h1>Página não encontrada</h1><p><a href="/baralho-democratico/">Voltar ao início</a></p>'
           + rodape("/baralho-democratico/"))

    # resumo para quem roda o build
    sem_video = [c["id"] for c in jogo if not c.get("video")]
    sem_fonte = [c["id"] for c in jogo if not c.get("fontes")]
    alertas = [(c["id"], a) for c in todas for a in (c.get("alertas") or [])]
    print(f"{len(jogo)} cartas + compartilhe geradas em {DOCS}")
    print("sem vídeo:", ", ".join(sem_video) or "nenhuma")
    print("sem fonte:", ", ".join(sem_fonte) or "nenhuma")
    print(f"alertas: {len(alertas)}")
    if not (DOCS / PDF_DUPLEX).exists():
        print("aviso: PDFs ainda não gerados (rode make_pdfs.py)")


if __name__ == "__main__":
    main()
