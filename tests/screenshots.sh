#!/bin/bash
# Screenshots do site em largura de celular (390 px). Uso: tests/screenshots.sh PASTA_SAIDA [pagina ...]
# O Chrome headless não abre janela com menos de 500 px, então a página é carregada num iframe de 390 px.
set -e
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:?pasta de saída}"; shift
mkdir -p "$OUT" "$RAIZ/build"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
H=${ALTURA:-2600}
PAGS=("$@"); [ ${#PAGS[@]} -eq 0 ] && PAGS=("index.html" "c/a/index.html" "c/20/index.html" "correcoes/index.html")
for p in "${PAGS[@]}"; do
  nome=$(echo "$p" | tr '/' '_' | sed 's/_index.html//; s/.html//')
  W="$RAIZ/build/moldura_$nome.html"
  echo "<html><body style='margin:0'><iframe src='file://$RAIZ/docs/$p' style='width:390px;height:${H}px;border:0;display:block'></iframe></body></html>" > "$W"
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --allow-file-access-from-files --window-size=390,$H --virtual-time-budget=5000 \
    --screenshot="$OUT/$nome.png" "file://$W" >/dev/null 2>&1
  echo "$OUT/$nome.png"
done
