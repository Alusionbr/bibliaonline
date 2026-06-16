#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
expand_verses.py — monta o verses.json COMPLETO a partir das fontes baixadas.

Entradas (em raw_materials/, geradas por download_sources.py):
  - morphhb-master.zip      -> hebraico/aramaico (OSIS XML, WLC)
  - nestle1904-master.zip   -> grego (Nestle 1904)
  - almeida_gutenberg_62383.txt OU almeida.json -> português (Almeida domínio público)

Saída:
  - site/data/verses.json (array completo), PRESERVANDO os versículos já
    comentados à mão (mescla por referência: o curado vence).

Importante:
  - Roda offline (só lê arquivos locais). Use depois de download_sources.py.
  - É um ANDAIME testável: o parser de OSHB é o mais sólido (formato estável).
    Nestle e Almeida têm detecção flexível de formato; rode e ajuste se a
    cobertura vier baixa (o script imprime um relatório no fim).
  - NUNCA troque o português por uma revisão protegida (só Almeida 1911/anterior).

Uso:
    python3 scripts/expand_verses.py
"""
import json, re, zipfile, unicodedata, glob, io
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
RAW  = ROOT / "raw_materials"
DATA = ROOT / "site" / "data"
OUT  = DATA / "verses.json"

# ---- mapa de códigos OSIS -> nome em português (e ordem canônica) ----
OSIS_PT = {
 "Gen":"Gênesis","Exod":"Êxodo","Lev":"Levítico","Num":"Números","Deut":"Deuteronômio",
 "Josh":"Josué","Judg":"Juízes","Ruth":"Rute","1Sam":"1 Samuel","2Sam":"2 Samuel",
 "1Kgs":"1 Reis","2Kgs":"2 Reis","1Chr":"1 Crônicas","2Chr":"2 Crônicas","Ezra":"Esdras",
 "Neh":"Neemias","Esth":"Ester","Job":"Jó","Ps":"Salmos","Prov":"Provérbios","Eccl":"Eclesiastes",
 "Song":"Cânticos","Isa":"Isaías","Jer":"Jeremias","Lam":"Lamentações","Ezek":"Ezequiel",
 "Dan":"Daniel","Hos":"Oseias","Joel":"Joel","Amos":"Amós","Obad":"Obadias","Jonah":"Jonas",
 "Mic":"Miquéias","Nah":"Naum","Hab":"Habacuque","Zeph":"Sofonias","Hag":"Ageu","Zech":"Zacarias",
 "Mal":"Malaquias","Matt":"Mateus","Mark":"Marcos","Luke":"Lucas","John":"João","Acts":"Atos",
 "Rom":"Romanos","1Cor":"1 Coríntios","2Cor":"2 Coríntios","Gal":"Gálatas","Eph":"Efésios",
 "Phil":"Filipenses","Col":"Colossenses","1Thess":"1 Tessalonicenses","2Thess":"2 Tessalonicenses",
 "1Tim":"1 Timóteo","2Tim":"2 Timóteo","Titus":"Tito","Phlm":"Filemom","Heb":"Hebreus","Jas":"Tiago",
 "1Pet":"1 Pedro","2Pet":"2 Pedro","1John":"1 João","2John":"2 João","3John":"3 João","Jude":"Judas","Rev":"Apocalipse",
}
NT = {"Matt","Mark","Luke","John","Acts","Rom","1Cor","2Cor","Gal","Eph","Phil","Col","1Thess",
 "2Thess","1Tim","2Tim","Titus","Phlm","Heb","Jas","1Pet","2Pet","1John","2John","3John","Jude","Rev"}

# trechos em aramaico no AT (referência por referência seria ideal; aqui por faixa)
def is_aramaic(osis, ch, vs):
    if osis == "Dan" and ((ch == 2 and vs >= 4) or (3 <= ch <= 7)): return True
    if osis == "Ezra" and ((ch == 4 and vs >= 8) or ch == 5 or (ch == 6 and vs <= 18)
                           or (ch == 7 and 12 <= vs <= 26)): return True
    if osis == "Jer" and ch == 10 and vs == 11: return True
    if osis == "Gen" and ch == 31 and vs == 47: return True
    return False

CANTILLATION = dict.fromkeys(range(0x0591, 0x05B0))  # te'amim (acentos de cantilação)
def strip_cantillation(s):
    return "".join(c for c in s if ord(c) not in CANTILLATION)

def slugify(book_pt, ch, vs):
    base = unicodedata.normalize("NFKD", book_pt).encode("ascii","ignore").decode().lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return f"{base}-{ch}-{vs}"

# ---------------- OSHB (hebraico/aramaico) ----------------
def parse_oshb(zip_path, keep_cantillation=False):
    out = {}
    if not zip_path.exists():
        print("  ! OSHB ausente:", zip_path.name); return out
    with zipfile.ZipFile(zip_path) as z:
        xmls = [n for n in z.namelist() if re.search(r"/wlc/[^/]+\.xml$", n)]
        for name in xmls:
            try:
                root = ET.fromstring(z.read(name))
            except Exception as e:
                print("  ! erro XML", name, e); continue
            for v in root.iter():
                tag = v.tag.split("}")[-1]
                if tag != "verse": continue
                osisID = v.attrib.get("osisID","")
                m = re.match(r"([\w]+)\.(\d+)\.(\d+)", osisID)
                if not m: continue
                book, ch, vs = m.group(1), int(m.group(2)), int(m.group(3))
                if book not in OSIS_PT: continue
                words = []
                for w in v.iter():
                    if w.tag.split("}")[-1] == "w" and w.text:
                        words.append(w.text.replace("/", ""))
                text = " ".join(words).strip()
                if not keep_cantillation:
                    text = strip_cantillation(text)
                out[(book, ch, vs)] = text
    print("  OSHB: %d versículos (AT)" % len(out))
    return out

# ---------------- Nestle 1904 (grego) ----------------
def parse_nestle(zip_path):
    out = {}
    if not zip_path.exists():
        print("  ! Nestle ausente:", zip_path.name); return out
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        # estratégia 1: XML com osisID
        xmls = [n for n in names if n.lower().endswith(".xml")]
        for name in xmls:
            try: root = ET.fromstring(z.read(name))
            except Exception: continue
            for v in root.iter():
                if v.tag.split("}")[-1] != "verse": continue
                m = re.match(r"([\w]+)\.(\d+)\.(\d+)", v.attrib.get("osisID",""))
                if not m: continue
                book, ch, vs = m.group(1), int(m.group(2)), int(m.group(3))
                if book not in NT: continue
                txt = "".join(w.text or "" for w in v.iter() if w.tag.split("}")[-1]=="w").strip()
                if txt: out[(book, ch, vs)] = txt
        if out:
            print("  Nestle (xml): %d versículos (NT)" % len(out)); return out
        # estratégia 2: TSV/CSV/txt "Book Chapter:Verse ... palavra grega"
        # procura um arquivo grande de texto e agrupa por (livro,cap,vers)
        cand = sorted([n for n in names if n.lower().endswith((".tsv",".csv",".txt"))],
                      key=lambda n: -z.getinfo(n).file_size)
        BOOKNUM = {  # ordem dos livros do NT no Nestle1904 morfológico (book number 1..27)
            1:"Matt",2:"Mark",3:"Luke",4:"John",5:"Acts",6:"Rom",7:"1Cor",8:"2Cor",9:"Gal",
            10:"Eph",11:"Phil",12:"Col",13:"1Thess",14:"2Thess",15:"1Tim",16:"2Tim",17:"Titus",
            18:"Phlm",19:"Heb",20:"Jas",21:"1Pet",22:"2Pet",23:"1John",24:"2John",25:"3John",26:"Jude",27:"Rev"}
        for name in cand:
            raw = z.read(name).decode("utf-8", "ignore")
            tmp = {}
            for line in raw.splitlines():
                # formatos comuns: "010401 ... Ἐν" (bbccvv...) ou "Matt 1:1\tἈν..."
                m = re.match(r"^\s*(\d{2})(\d{2})(\d{2})\D", line)
                if m:
                    bk = BOOKNUM.get(int(m.group(1)))
                    if not bk: continue
                    ch, vs = int(m.group(2)), int(m.group(3))
                    word = line.split()[-1]
                    tmp.setdefault((bk,ch,vs), []).append(word)
                    continue
                m = re.match(r"^([1-3]?\s?[A-Za-z]+)\s+(\d+):(\d+)\s+(.*)$", line)
                if m:
                    # mapeia nome inglês -> osis (parcial); pula se não bater
                    pass
            if tmp:
                out = {k:" ".join(v) for k,v in tmp.items()}
                print("  Nestle (%s): %d versículos (NT)" % (Path(name).name, len(out)))
                return out
    print("  ! Nestle: formato não reconhecido — ajuste parse_nestle()")
    return out

# ---------------- Almeida (português) ----------------
def parse_almeida():
    # preferir JSON estruturado, se existir
    j = RAW / "almeida.json"
    if j.exists():
        data = json.loads(j.read_text(encoding="utf-8"))
        out = {}
        # aceita formatos {livro:{cap:{vers:texto}}} ou lista de {book,chapter,verse,text}
        if isinstance(data, dict):
            for book, chaps in data.items():
                for ch, verses in chaps.items():
                    for vs, txt in verses.items():
                        out[(book, int(ch), int(vs))] = txt
        else:
            for r in data:
                out[(r["book"], int(r["chapter"]), int(r["verse"]))] = r["text"]
        print("  Almeida (json): %d versículos" % len(out)); return out, "json"
    # senão, tentar o txt do Gutenberg (heurística — CONFERIR resultado!)
    t = RAW / "almeida_gutenberg_62383.txt"
    if not t.exists():
        print("  ! Almeida ausente (nem almeida.json nem o .txt do Gutenberg)")
        return {}, None
    out = {}
    cur_ch = None
    raw = t.read_text(encoding="utf-8", errors="ignore")
    # heurística: linhas "1:1 No princípio..." ou "1 No princípio" sob um cabeçalho de capítulo
    for line in raw.splitlines():
        line = line.strip()
        m = re.match(r"^(\d+):(\d+)\s+(.+)$", line)
        if m:
            out[("?", int(m.group(1)), int(m.group(2)))] = m.group(3).strip()
    print("  Almeida (gutenberg txt): %d linhas no formato cap:vers — CONFERIR e mapear livros!" % len(out))
    return out, "gutenberg"

# ---------------- montagem ----------------
def main():
    print("Expandindo verses.json a partir de raw_materials/ ...")
    he = parse_oshb(RAW / "morphhb-master.zip")
    gr = parse_nestle(RAW / "nestle1904-master.zip")
    pt, pt_fmt = parse_almeida()

    # TRAVA DE SEGURANÇA: sem nenhuma fonte, não escreve nada (não apaga curados)
    if not he and not gr and not pt:
        print("\n! Nenhuma fonte encontrada em raw_materials/.")
        print("  Rode primeiro: python3 scripts/download_sources.py")
        print("  (verses.json NÃO foi alterado.)")
        return

    # carrega curados (preserva comentário/manuscrito feitos à mão)
    curated = {}
    if OUT.exists():
        for v in json.loads(OUT.read_text(encoding="utf-8")):
            curated[v["referencia"]] = v
    print("  Curados preservados: %d" % len(curated))

    FONTE_HE = "Westminster Leningrad Codex (Open Scriptures Hebrew Bible) — domínio público."
    FONTE_GR = "Novum Testamentum Graece, ed. Eberhard Nestle (1904) — domínio público."
    FONTE_PT = "João Ferreira de Almeida, Revista e Corrigida (1911) — domínio público no Brasil."

    verses = []
    # universo de referências = tudo que tem português (a tradução guia o site)
    refs = set(pt.keys())
    # se o português veio do Gutenberg sem livro mapeado, caímos para o universo dos originais
    if pt_fmt == "gutenberg":
        print("  ! Português sem livro mapeado: gere almeida.json estruturado para alinhar. "
              "Usando originais como universo por enquanto.")
        refs = set(he.keys()) | set(gr.keys())

    for (book, ch, vs) in sorted(refs, key=lambda k: (list(OSIS_PT).index(k[0]) if k[0] in OSIS_PT else 999, k[1], k[2])):
        if book not in OSIS_PT:  # ignora refs sem livro resolvido
            continue
        book_pt = OSIS_PT[book]
        ref = f"{book_pt} {ch}:{vs}"
        if ref in curated:                       # mantém o curado intacto
            verses.append(curated[ref]); continue
        if book in NT:
            original, fonte, idioma, direction = gr.get((book,ch,vs),""), FONTE_GR, "grego", "ltr"
        elif is_aramaic(book, ch, vs):
            original, fonte, idioma, direction = he.get((book,ch,vs),""), FONTE_HE, "aramaico", "rtl"
        else:
            original, fonte, idioma, direction = he.get((book,ch,vs),""), FONTE_HE, "hebraico", "rtl"
        verses.append({
            "slug": slugify(book_pt, ch, vs), "referencia": ref, "livro": book_pt,
            "tema": "", "idioma": idioma, "dir": direction,
            "original": original, "original_fonte": fonte if original else "",
            "transliteracao": "", "texto_pt": pt.get((book,ch,vs),""), "texto_pt_fonte": FONTE_PT,
            "palavras": [], "contexto": "", "origem": "", "judaismo": False, "leitura_judaica": "",
            "manuscrito": {"tipo":"Não disponível com licença confirmada","imagem":None,
                           "legenda":"Imagem de manuscrito pendente de licença para este versículo.",
                           "licenca":"A confirmar.","fonte_nome":"","fonte_url":""},
            "artigos": []
        })

    # garante que nenhum curado se perca (mesmo que não esteja nas fontes)
    present = {v["referencia"] for v in verses}
    for ref, cv in curated.items():
        if ref not in present:
            verses.append(cv)
    # ordena tudo em ordem bíblica
    def _key(v):
        bi = list(OSIS_PT.values()).index(v["livro"]) if v["livro"] in OSIS_PT.values() else 999
        m = re.search(r"(\d+):(\d+)", v["referencia"]); 
        return (bi, int(m.group(1)), int(m.group(2))) if m else (bi, 0, 0)
    verses.sort(key=_key)

    OUT.write_text(json.dumps(verses, ensure_ascii=False, indent=2), encoding="utf-8")
    # relatório
    com_orig = sum(1 for v in verses if v["original"])
    com_pt = sum(1 for v in verses if v["texto_pt"])
    print("\nRelatório:")
    print("  total de versículos: %d" % len(verses))
    print("  com texto original : %d" % com_orig)
    print("  com tradução PT    : %d" % com_pt)
    print("  curados mantidos   : %d" % len(curated))
    print("\nSalvo em %s" % OUT)
    print("Agora rode: python3 scripts/build.py")
    if com_orig < len(verses)*0.5 or com_pt < len(verses)*0.5:
        print("\n! COBERTURA BAIXA. Verifique o formato das fontes (parse_nestle/parse_almeida).")

if __name__ == "__main__":
    main()
