#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baixa as fontes externas usadas pelo pipeline.

Saidas em raw_materials/:
  - almeida_gutenberg_62383.txt
  - morphhb-master.zip
  - nestle1904-master.zip

O script apenas baixa os arquivos. A leitura, parsing e validacao ficam em
expand_verses.py, fill_pt.py e nos testes.
"""
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw_materials"

SOURCES = [
    {
        "name": "Almeida Gutenberg",
        "url": "https://www.gutenberg.org/files/62383/62383-0.txt",
        "path": RAW / "almeida_gutenberg_62383.txt",
    },
    {
        "name": "Open Scriptures Hebrew Bible",
        "url": "https://github.com/openscriptures/morphhb/archive/refs/heads/master.zip",
        "path": RAW / "morphhb-master.zip",
    },
    {
        "name": "Nestle 1904",
        "url": "https://github.com/biblicalhumanities/Nestle1904/archive/refs/heads/master.zip",
        "path": RAW / "nestle1904-master.zip",
    },
]


def download_file(url, path, timeout=120):
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Baixando {url}")
    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        with path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 128):
                if chunk:
                    handle.write(chunk)
    print(f"OK: {path.relative_to(ROOT)}")


def main():
    for source in SOURCES:
        print(f"\nFonte: {source['name']}")
        download_file(source["url"], source["path"])


if __name__ == "__main__":
    main()
