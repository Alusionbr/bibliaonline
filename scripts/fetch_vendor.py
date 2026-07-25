#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baixa as bibliotecas de terceiros para dentro do site.

Motivo: o supabase-js vinha de cdn.jsdelivr.net. Mesmo com `defer`, um script
assim roda antes do DOMContentLoaded, então o carregamento de todas as 32 mil
páginas dependia de um host de terceiros — que também via o IP de cada
visitante. Servido da própria origem, some a dependência e some o vazamento.

O preço de trazer para dentro: o Dependabot deste repositório cobre
github-actions e pip, não npm, então este arquivo NÃO recebe alerta automático
de vulnerabilidade. Por isso a versão está no nome do arquivo e aqui em cima —
atualizar é uma decisão explícita, não algo que acontece sozinho. Confira
https://github.com/supabase/supabase-js/releases de tempos em tempos.

Uso (só ao trocar de versão):
    python scripts/fetch_vendor.py
"""
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "site" / "assets"

SUPABASE_VERSION = "2.45.4"

# O sufixo .min.js não é enfeite: identifica o arquivo como bundle minificado
# de terceiro, que é o que o CodeQL usa para não gastar análise (e não abrir
# alerta) em código que não é nosso e não podemos corrigir.
VENDORED = [
    (f"vendor-supabase-{SUPABASE_VERSION}.min.js",
     f"https://cdn.jsdelivr.net/npm/@supabase/supabase-js@{SUPABASE_VERSION}"
     f"/dist/umd/supabase.min.js"),
]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def main():
    for old in OUT_DIR.glob("vendor-*.js"):
        old.unlink()
    for name, url in VENDORED:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=90) as r:
            data = r.read()
        (OUT_DIR / name).write_bytes(data)
        print(f"OK: {name} ({len(data) // 1024} KB) de {url}")


if __name__ == "__main__":
    sys.exit(main())
