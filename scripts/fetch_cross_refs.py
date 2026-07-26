#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Traz a rede de referências cruzadas do OpenBible.info para dentro do site.

Motivo: site/data/cross-references.json cobria 39 versículos dos 31.173 — 0,125%.
Na prática, cada página de versículo era um beco: o texto estava lá, mas nada
apontava para o resto da Bíblia. O OpenBible publica ~345 mil ligações em CC BY,
com um campo de votos que permite ficar só com as boas.

Como toda fonte externa deste projeto, isto é preparo, não tempo de execução: o
script grava dado curado no repositório e o site nunca fala com o OpenBible.

Uso (só ao atualizar a base):
    python scripts/fetch_cross_refs.py
Gera: site/data/xrefs/<livro>/<capítulo>.json, carregado sob demanda.

O corte é por capítulo, não por livro, porque é assim que se lê: abrir um
versículo de Salmos baixaria 233 KB no corte por livro, contra ~2 KB no corte
por capítulo. O mesmo erro do índice de busca, que pede 6,3 MB para responder
uma consulta, em escala menor.
"""
import io
import json
import re
import shutil
import sys
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_config import BOOK_ORDER, DATA
from build_utils import book_slug

SRC = "https://a.openbible.info/data/cross-references.zip"
OUT_DIR = DATA / "xrefs"

# Só entram ligações com apoio real. O arquivo traz votos negativos (sugestões
# rejeitadas pelos leitores) e um longo rastro de votos 0 — publicá-las encheria
# cada versículo de ruído, que é o oposto do problema que estamos resolvendo.
MIN_VOTES = 5
# Teto por versículo: a página precisa caber na tela e as mais votadas bastam.
MAX_PER_VERSE = 12

# OSIS -> nome do livro no projeto. A ordem é a canônica, a mesma de BOOK_ORDER,
# então o mapa é posicional e não precisa repetir os nomes em português.
OSIS = [
    "Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "Ruth", "1Sam", "2Sam",
    "1Kgs", "2Kgs", "1Chr", "2Chr", "Ezra", "Neh", "Esth", "Job", "Ps", "Prov",
    "Eccl", "Song", "Isa", "Jer", "Lam", "Ezek", "Dan", "Hos", "Joel", "Amos",
    "Obad", "Jonah", "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal", "Matt",
    "Mark", "Luke", "John", "Acts", "Rom", "1Cor", "2Cor", "Gal", "Eph", "Phil",
    "Col", "1Thess", "2Thess", "1Tim", "2Tim", "Titus", "Phlm", "Heb", "Jas",
    "1Pet", "2Pet", "1John", "2John", "3John", "Jude", "Rev",
]
BOOK_BY_OSIS = dict(zip(OSIS, BOOK_ORDER))

REF_RE = re.compile(r"^([1-3]?[A-Za-z]+)\.(\d+)\.(\d+)$")


def parse_ref(raw):
    """"Gen.1.1" -> "Gênesis 1:1". Devolve None para o que não reconhecer."""
    m = REF_RE.match(raw.strip())
    if not m:
        return None
    livro = BOOK_BY_OSIS.get(m.group(1))
    return f"{livro} {int(m.group(2))}:{int(m.group(3))}" if livro else None


def parse_target(raw):
    """O destino pode ser um intervalo ("Ps.148.4-Ps.148.5").

    Guardamos só o versículo inicial: o leitor abre a página dele e segue a
    leitura dali. Guardar o intervalo inteiro multiplicaria o arquivo sem mudar
    para onde a pessoa clica.
    """
    return parse_ref(raw.split("-", 1)[0])


def main():
    with urllib.request.urlopen(SRC, timeout=180) as r:
        blob = r.read()
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        nome = next(n for n in z.namelist() if n.endswith(".txt"))
        texto = z.read(nome).decode("utf-8")

    por_versiculo = defaultdict(list)
    lidas = descartadas = 0
    for linha in texto.splitlines()[1:]:
        partes = linha.split("\t")
        if len(partes) < 3:
            continue
        lidas += 1
        try:
            votos = int(partes[2])
        except ValueError:
            continue
        if votos < MIN_VOTES:
            descartadas += 1
            continue
        origem, destino = parse_ref(partes[0]), parse_target(partes[1])
        if not origem or not destino or origem == destino:
            continue
        por_versiculo[origem].append((votos, destino))

    # ordena por votos e corta; remove repetido preservando a ordem
    por_capitulo = defaultdict(dict)
    total = 0
    for ref, itens in por_versiculo.items():
        vistos, saida = set(), []
        for _, destino in sorted(itens, key=lambda x: -x[0]):
            if destino in vistos:
                continue
            vistos.add(destino)
            saida.append(destino)
            if len(saida) >= MAX_PER_VERSE:
                break
        livro, cap_vs = ref.rsplit(" ", 1)
        capitulo = cap_vs.split(":", 1)[0]
        por_capitulo[(livro, capitulo)][ref] = saida
        total += len(saida)

    shutil.rmtree(OUT_DIR, ignore_errors=True)
    for (livro, capitulo), mapa in por_capitulo.items():
        destino = OUT_DIR / book_slug(livro) / f"{capitulo}.json"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            json.dumps(mapa, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8")

    arquivos = list(OUT_DIR.rglob("*.json"))
    maior = max((f.stat().st_size for f in arquivos), default=0)
    peso = sum(f.stat().st_size for f in arquivos)
    print(f"OK: {len(por_versiculo)} versículos, {total} ligações, "
          f"{len(arquivos)} arquivos em {OUT_DIR.relative_to(DATA.parent.parent)}")
    print(f"    {lidas} linhas lidas, {descartadas} abaixo de {MIN_VOTES} votos")
    print(f"    maior arquivo: {maior // 1024} KB · total {peso // 1024} KB")


if __name__ == "__main__":
    main()
