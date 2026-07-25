#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baixa as fontes do Google Fonts para dentro do site.

Motivo: o <link> para fonts.googleapis.com bloqueia a renderização de todas as
32 mil páginas. É um terceiro na rota crítica — se ele estiver lento, bloqueado
ou fora do ar, o site inteiro fica sem pintar, e não há plano B. Servindo os
mesmos arquivos da própria origem, a primeira pintura passa a depender só do
nosso servidor.

As famílias e pesos são exatamente os que o site já carregava: isto é uma
mudança de entrega, não de desenho. Nenhuma das cinco famílias é decorativa —
Frank Ruhl Libre desenha o hebraico e Gentium Book Plus o grego, que são o
motivo de o site existir.

Uso (só quando mudar a lista de fontes):
    python scripts/fetch_fonts.py
Gera: site/assets/fonts/*.woff2 e site/assets/fonts.css
"""
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "site" / "assets" / "fonts"
OUT_CSS = ROOT / "site" / "assets" / "fonts.css"

# Mesma consulta que estava no <link> do head(), família por família para
# conseguir filtrar os subconjuntos de cada uma separadamente.
# Pesos apurados carregando as páginas de verdade e anotando quais arquivos o
# navegador chega a pedir: Frank Ruhl 500, Gentium 700 e Spectral 500 estavam
# sendo baixados do Google sem nunca serem usados por regra nenhuma do CSS.
FAMILIES = [
    "Fraunces:opsz,wght@9..144,500;9..144,600",
    "Spectral:wght@400;600",
    "Inter:wght@400;600;700",
    "Frank+Ruhl+Libre:wght@400;700",
    "Gentium+Book+Plus:wght@400",
]

# Subconjuntos que este site realmente usa. O css2 devolve também cyrillic,
# vietnamese e afins, que só pesariam sem nunca serem pedidos.
#
# latin-ext (U+0100-02BA) fica de fora de propósito: era o grupo mais pesado
# (~500 KB), e uma varredura em verses.json achou UM único caractere acima de
# U+00FF em todas as traduções e transliterações — e ele já está em latin.
# Português acentuado inteiro cabe em latin (U+0000-00FF).
#
# Frank Ruhl e Gentium também ficam SEM latin: são fontes de escrita, e o
# pouco de pontuação latina que aparece dentro de um trecho hebraico ou grego
# cai no Spectral seguinte da pilha, que já está carregado. Só esses dois
# arquivos custavam ~90 KB para desenhar vírgulas.
KEEP = {
    "Frank Ruhl Libre": {"hebrew"},
    "Gentium Book Plus": {"greek", "greek-ext"},
}
DEFAULT_KEEP = {"latin"}

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def fetch(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return data if binary else data.decode("utf-8")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.woff2"):
        old.unlink()

    blocks, n_bytes = [], 0
    for family in FAMILIES:
        css = fetch(f"https://fonts.googleapis.com/css2?family={family}&display=swap")
        # o css2 antecede cada @font-face com um comentário nomeando o subconjunto
        for subset, face in re.findall(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{[^}]*\})", css):
            name = re.search(r"font-family:\s*'([^']+)'", face).group(1)
            if subset not in KEEP.get(name, DEFAULT_KEEP):
                continue
            weight = re.search(r"font-weight:\s*([\d ]+)", face).group(1).strip().replace(" ", "-")
            url = re.search(r"url\((https://[^)]+\.woff2)\)", face).group(1)
            fname = f"{slug(name)}-{weight}-{subset}.woff2"
            data = fetch(url, binary=True)
            (OUT_DIR / fname).write_bytes(data)
            n_bytes += len(data)
            face = face.replace(url, f"fonts/{fname}")
            # font-display:swap mantém o texto legível na fonte de sistema
            # enquanto a nossa carrega, em vez de deixar a página em branco
            if "font-display" not in face:
                face = face.replace("@font-face {", "@font-face {\n  font-display: swap;")
            blocks.append(f"/* {name} {weight} — {subset} */\n{face}")

    header = ("/* Fontes servidas pela própria origem. Gerado por\n"
              "   scripts/fetch_fonts.py — não editar à mão. */\n")
    OUT_CSS.write_text(header + "\n".join(blocks) + "\n", encoding="utf-8")
    print(f"OK: {len(blocks)} arquivos, {n_bytes // 1024} KB em {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
