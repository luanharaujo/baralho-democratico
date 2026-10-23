# Baralho Democrático

Site e PDFs de impressão do Baralho Democrático: versão atualizada por Luan Araújo do
[Baralho 2026](https://linktr.ee/nossobaralho) do Coletivo do Baralho (Regiane).
Cada carta tem um QR code que leva a `https://luanharaujo.github.io/baralho-democratico/c/<id>/`,
com explicação, fontes com veículo e data, e um trecho curto de vídeo.

Site estático, sem framework, sem cookies e sem rastreadores. O player do YouTube
(`youtube-nocookie.com`) só carrega quando a pessoa toca para assistir.

## Estrutura

```
data/cartas.json     conteúdo (fonte única; vem de baralho/conteudo/cartas.json)
src/cartas.py        leitura do json e desenho das cartas em HTML (site e PDFs)
src/carta.css        visual da carta (escala por --cw: 1em = 1/63 da largura)
src/site.css         visual do site
src/video.js         carrega o vídeo só ao tocar
src/fonts/           Aileron e IBM Plex Sans (SIL Open Font License)
build.py             gera o site em docs/
make_pdfs.py         gera docs/pdf/*.pdf
tests/               conferência de links, QR e screenshots
docs/                o que o GitHub Pages publica (gerado; não editar à mão)
```

IDs das cartas (fixos, estão impressos nos QR): `a`, `2` ... `32`, `compartilhe`.

## Gerar o site

```bash
python3 build.py "/Users/luanharaujo/Desktop/Em defesa da democracia/baralho/conteudo/cartas.json"
# ou, se data/cartas.json já está atualizado:
python3 build.py
```

Só usa a biblioteca padrão do Python. O build imprime as cartas sem vídeo, sem fonte e o número de alertas.

## Atualizar uma carta

1. Edite a carta em `baralho/conteudo/cartas.json` (campos no `BRIEF.md`: `texto_carta`, `explicacao`, `fontes`, `video`, `verificado_em` ...).
2. Rode `python3 build.py <caminho do cartas.json>`.
3. Se mudou algo que vai impresso (`texto_carta`, `hashtag`, `valor`, `naipe`, `candidato`, textos de Compartilhe/Importante), gere os PDFs de novo.
4. Rode os testes e publique.

Mudar só explicação, fonte ou vídeo não exige reimprimir: o QR continua o mesmo e a página é atualizada.

## Gerar os PDFs

Precisa do Google Chrome instalado e do `uv`.

```bash
uv run --with segno python3 make_pdfs.py \
  --copiar-para "/Users/luanharaujo/Desktop/Em defesa da democracia/baralho/impressao"
```

- `docs/pdf/baralho-democratico-duplex.pdf`: A4 paisagem, 8 cartas por folha, mesmo modelo do original. Páginas ímpares são as frentes e as pares os versos espelhados. Imprimir frente e verso **virando pela borda longa**. A última folha (Compartilhe e Importante) é de um lado só.
- `docs/pdf/baralho-democratico-4-por-folha.pdf`: A4 retrato, 4 cartas grandes por folha (9 x 12,6 cm), com marcas de corte, frente e verso pela borda longa.

QR: nível de correção Q, cerca de 35 mm na carta pequena.

## Testes

```bash
python3 tests/verificar_site.py                                       # todas as páginas e links internos
uv run --with opencv-python-headless python3 tests/verificar_qr.py   # decodifica cada QR dos PDFs
tests/screenshots.sh /tmp/shots                                       # páginas em 390 px de largura
```

`verificar_qr.py` usa `build/manifesto_qr.json`, gravado por `make_pdfs.py` com a posição de cada QR.

## Publicar no GitHub Pages (não feito ainda)

1. Criar o repositório público `luanharaujo/baralho-democratico` no GitHub (vazio, sem README).
2. `git remote add origin git@github.com:luanharaujo/baralho-democratico.git`
3. `git push -u origin main`
4. No GitHub: Settings > Pages > Build and deployment > Source: "Deploy from a branch", Branch `main`, pasta `/docs`. Salvar.
5. Esperar 1 a 2 minutos e abrir `https://luanharaujo.github.io/baralho-democratico/` e uma carta, por exemplo `/c/20/`.
6. Escanear 2 ou 3 QR do PDF impresso para conferir.

Depois, cada atualização: build, testes, `git commit` e `git push`. O Pages republica sozinho.

## Créditos e regras

- Original: Baralho 2026, Coletivo do Baralho / Regiane, linktr.ee/nossobaralho.
- Versão atualizada e mantida por Luan Araújo, como pessoa física.
- Impressão para uso pessoal; não distribuir impresso.
- Só fato verificável, com fonte e data. Nada de vídeo, imagem ou áudio de pessoa real gerado por IA.
