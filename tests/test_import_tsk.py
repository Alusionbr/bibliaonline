# -*- coding: utf-8 -*-
"""Testes do importador do TSK (scripts/import_tsk.py).

Roda inteiramente contra um dataset minúsculo em memória (sem baixar nada
nem tocar site/data/ real) — cobre o parser de referências e o filtro que
nunca deixa passar um link para um versículo inexistente.
"""
import json


def test_parse_ref_versiculo_simples(import_tsk):
    assert import_tsk.parse_ref("Gen 1:1", import_tsk.EN_TO_PT) == ["Gênesis 1:1"]


def test_parse_ref_intervalo_expande_dentro_do_capitulo(import_tsk):
    assert import_tsk.parse_ref("John 1:1-3", import_tsk.EN_TO_PT) == [
        "João 1:1", "João 1:2", "João 1:3",
    ]


def test_parse_ref_livro_desconhecido_e_ignorado(import_tsk):
    assert import_tsk.parse_ref("Naoexiste 9:9", import_tsk.EN_TO_PT) == []


def test_parse_ref_formato_invalido_e_ignorado(import_tsk):
    assert import_tsk.parse_ref("isto não é uma referência", import_tsk.EN_TO_PT) == []


def test_parse_ref_intervalo_absurdo_e_ignorado(import_tsk):
    # intervalo maior que 30 versículos provavelmente é erro de parsing, não
    # um cross-reference real — descarta em vez de arriscar um link estranho.
    assert import_tsk.parse_ref("Gen 1:1-40", import_tsk.EN_TO_PT) == []


def test_mapeamento_cobre_o_canone_inteiro(import_tsk):
    from build_config import BOOK_ORDER
    assert set(BOOK_ORDER) <= set(import_tsk.EN_TO_PT.values())


def test_main_gera_json_e_descarta_alvos_fora_do_dataset(import_tsk, tmp_path, monkeypatch, capsys):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    verses = [
        {"referencia": "Gênesis 1:1"}, {"referencia": "João 1:1"},
        {"referencia": "João 1:2"}, {"referencia": "Salmos 33:6"},
    ]
    (data_dir / "verses.json").write_text(json.dumps(verses, ensure_ascii=False), "utf-8")
    monkeypatch.setattr(import_tsk, "DATA", data_dir)

    src = tmp_path / "tsk.txt"
    src.write_text(
        "Gen 1:1\tPs 33:6; John 1:1-3; Naoexiste 9:9\n"
        "\n"  # linha em branco é ignorada
        "sem tabulação\n",  # linha sem TAB é ignorada
        "utf-8",
    )
    monkeypatch.setattr("sys.argv", ["import_tsk.py", str(src)])
    import_tsk.main()

    out = json.loads((data_dir / "tsk-crossrefs.json").read_text("utf-8"))
    # João 1:3 não existe no dataset de teste -> descartado (nunca um link quebrado)
    assert out == {"Gênesis 1:1": ["Salmos 33:6", "João 1:1", "João 1:2"]}


def test_main_limita_referencias_por_ancora(import_tsk, tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    alvos = [f"Salmos 1:{n}" for n in range(1, 26)]
    verses = [{"referencia": "Gênesis 1:1"}] + [{"referencia": r} for r in alvos]
    (data_dir / "verses.json").write_text(json.dumps(verses, ensure_ascii=False), "utf-8")
    monkeypatch.setattr(import_tsk, "DATA", data_dir)

    src = tmp_path / "tsk.txt"
    linha_alvos = "; ".join("Ps 1:" + str(n) for n in range(1, 26))
    src.write_text(f"Gen 1:1\t{linha_alvos}\n", "utf-8")
    monkeypatch.setattr("sys.argv", ["import_tsk.py", str(src)])
    import_tsk.main()

    out = json.loads((data_dir / "tsk-crossrefs.json").read_text("utf-8"))
    assert len(out["Gênesis 1:1"]) == import_tsk.MAX_REFS
