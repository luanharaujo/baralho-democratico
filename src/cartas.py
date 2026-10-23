"""Leitura do cartas.json e desenho das cartas em HTML (usado pelo site e pelos PDFs).

As cartas são desenhadas em unidades "em": dentro de .carta, 1em = 1/63 da largura,
ou seja, 1em equivale a 1 mm numa carta de 63 x 88 mm. Assim o mesmo desenho
serve para o PDF duplex (63 mm), para o PDF de 4 por folha (maior) e para o site (px).
"""
import html
import json
import re
from pathlib import Path

BASE_URL = "https://luanharaujo.github.io/baralho-democratico/"

NAIPES = {
    "copas": {"cor": "vermelho", "nome": "copas"},
    "ouros": {"cor": "laranja", "nome": "ouros"},
    "espadas": {"cor": "preto", "nome": "espadas"},
    "paus": {"cor": "preto", "nome": "paus"},
}

CANDIDATOS = {"lula": "LULA", "flavio": "FLÁVIO BOLSONARO"}
CANDIDATOS_NOME = {"lula": "Lula (PT)", "flavio": "Flávio Bolsonaro (PL)"}

SVG_NAIPE = {
    "copas": '<svg viewBox="0 0 100 92" aria-hidden="true"><path d="M50 92C22 68 0 49 0 27 0 11 12 0 27 0c10 0 18 5 23 14C55 5 63 0 73 0c15 0 27 11 27 27 0 22-22 41-50 65z"/></svg>',
    "ouros": '<svg viewBox="0 0 80 100" aria-hidden="true"><path d="M40 0 80 50 40 100 0 50z"/></svg>',
    "espadas": '<svg viewBox="0 0 100 110" aria-hidden="true"><path d="M50 0C42 18 0 40 0 66c0 15 12 25 26 25 9 0 16-4 21-11-1 13-7 23-17 30h40c-10-7-16-17-17-30 5 7 12 11 21 11 14 0 26-10 26-25C100 40 58 18 50 0z"/></svg>',
    "paus": '<svg viewBox="0 0 100 110" aria-hidden="true"><circle cx="50" cy="26" r="24"/><circle cx="24" cy="62" r="24"/><circle cx="76" cy="62" r="24"/><circle cx="50" cy="58" r="14"/><path d="M45 60c0 22-6 38-16 50h42c-10-12-16-28-16-50z"/></svg>',
}


def carregar(caminho):
    cartas = json.loads(Path(caminho).read_text(encoding="utf-8"))
    if isinstance(cartas, dict) and "cartas" in cartas:
        cartas = cartas["cartas"]
    return cartas


def esc(s):
    return html.escape(s or "", quote=True)


def texto(c):
    """Texto impresso: texto_carta, ou o original enquanto o conteúdo não chegou."""
    t = (c.get("texto_carta") or c.get("texto_original") or "").strip()
    return t


def sem_aspas(t):
    t = t.strip()
    t = re.sub(r'^[\s"“”]+', "", t)
    t = re.sub(r'[\s"“”]+$', "", t)
    t = re.sub(r"\s+([.,;:!?])", r"\1", t)  # espaço antes de pontuação
    t = re.sub(r'"([^"]+)"', "‘\\1’", t)  # aspas internas: ‘ ’ (as externas são “ ”)
    return t


def valor(c):
    v = c.get("valor")
    if v:
        return str(v)
    return c["id"].upper() if c["id"] == "a" else c["id"]


def eh_jogo(c):
    return c.get("naipe") in NAIPES


def url_carta(cid):
    return f"{BASE_URL}c/{cid}/"


def titulo_e_corpo(c, titulo_padrao):
    """Separa 'Compartilhe!' ou 'Importante.' do começo do texto."""
    t = texto(c)
    m = re.match(r"^\s*(Compartilhe!|Importante[.:!]?)\s*(.*)$", t, re.S)
    if m:
        return m.group(1).rstrip(".:"), m.group(2).strip()
    return titulo_padrao, t


def _indice(c, pos):
    return (
        f'<div class="idx {pos}"><span class="v{" sub" if valor(c) in ("6", "9") else ""}">{esc(valor(c))}</span>'
        f'<span class="n">{SVG_NAIPE[c["naipe"]]}</span></div>'
    )


def frente(c, extra_cls=""):
    """Lado da pergunta: 'Isso é bom ou ruim?' + texto + hashtag."""
    t = sem_aspas(texto(c))
    tag = esc(c.get("hashtag") or "")
    return (
        f'<div class="carta frente n-{c["naipe"]} {extra_cls}" data-id="{esc(c["id"])}">'
        f'<div class="borda">'
        f'{_indice(c, "tl")}{_indice(c, "br")}'
        f'<div class="corpo"><p class="q1">Isso é</p><p class="q2">bom ou ruim?</p>'
        f'<p class="txt">“{esc(t)}”</p></div>'
        f'<p class="tag">{tag}</p>'
        f"</div></div>"
    )


def verso(c, qr_svg=None, extra_cls=""):
    """Lado da resposta: candidato + QR (no site, sem QR)."""
    nome = CANDIDATOS.get(c.get("candidato") or "", "?")
    nome_html = "<br>".join(esc(p) for p in nome.split(" ", 1)) if " " in nome else esc(nome)
    if qr_svg:
        meio = (
            f'<div class="qr">{qr_svg}</div>'
            f'<p class="dica">Aponte a câmera e veja a fonte</p>'
        )
    else:
        meio = '<p class="dica site">Veja abaixo a fonte e o vídeo</p>'
    return (
        f'<div class="carta verso n-{c["naipe"]} {extra_cls}" data-id="{esc(c["id"])}">'
        f'<div class="borda">'
        f'{_indice(c, "tl")}{_indice(c, "br")}'
        f'<p class="nome">{nome_html}</p>{meio}'
        f"</div></div>"
    )


def carta_compartilhe(c, qr_svg=None, extra_cls=""):
    titulo, corpo = titulo_e_corpo(c, "Compartilhe!")
    qr = f'<div class="qr">{qr_svg}</div>' if qr_svg else ""
    return (
        f'<div class="carta especial compartilhe {extra_cls}" data-id="compartilhe"><div class="borda">'
        f'<div class="corpo"><p class="titulo">{esc(titulo)}</p><p class="txt">{esc(corpo)}</p></div>'
        f"{qr}</div></div>"
    )


def carta_importante(c, extra_cls=""):
    titulo, corpo = titulo_e_corpo(c, "Importante")
    return (
        f'<div class="carta especial importante {extra_cls}" data-id="importante"><div class="borda">'
        f'<div class="corpo"><p class="titulo">{esc(titulo)}</p><p class="txt">{esc(corpo)}</p></div>'
        f"</div></div>"
    )


# Ajusta o tamanho do texto para caber na carta (roda no navegador e no Chrome headless).
SCRIPT_AJUSTE = """
<script>
(function(){
  function cabe(el){ return el.scrollHeight <= el.clientHeight + 1 && el.scrollWidth <= el.clientWidth + 1; }
  function ajustar(){
    document.querySelectorAll('.carta .corpo').forEach(function(corpo){
      var t = corpo.querySelector('.txt'); if(!t) return;
      var base = parseFloat(getComputedStyle(t).getPropertyValue('--fs')) || 4.3;
      var fs = base;
      t.style.fontSize = fs + 'em';
      while(!cabe(corpo) && fs > 2.4){ fs -= 0.1; t.style.fontSize = fs.toFixed(2) + 'em'; }
    });
    document.documentElement.setAttribute('data-ajustado', '1');
  }
  if (document.fonts && document.fonts.ready) { document.fonts.ready.then(ajustar); } else { ajustar(); }
  window.addEventListener('load', ajustar);
})();
</script>
"""


def css_fontes(prefixo):
    return f"""
@font-face {{ font-family: 'Aileron'; font-weight: 400; font-display: swap; src: url({prefixo}aileron-latin-400-normal.woff2) format('woff2'); }}
@font-face {{ font-family: 'Aileron'; font-weight: 700; font-display: swap; src: url({prefixo}aileron-latin-700-normal.woff2) format('woff2'); }}
@font-face {{ font-family: 'Plex'; font-weight: 400; font-display: swap; src: url({prefixo}ibm-plex-sans-latin-400-normal.woff2) format('woff2'); }}
"""
