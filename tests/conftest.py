"""Configuração comum dos testes.

Os scripts em scripts/ não formam um pacote instalável: cada um é um módulo
solto que guarda seus efeitos colaterais atrás de `if __name__ == "__main__"`.
Aqui carregamos cada script como um módulo isolado por caminho de arquivo, sem
executar o respectivo main(), para podermos testar suas funções puras.
"""
import importlib.util
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def gen_translit():
    return _load("gen_translit")


@pytest.fixture(scope="session")
def fill_pt():
    return _load("fill_pt")


@pytest.fixture(scope="session")
def expand_verses():
    return _load("expand_verses")


@pytest.fixture(scope="session")
def build():
    return _load("build")
