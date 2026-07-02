"""Configuracao estatica do gerador do site.

Este modulo guarda valores de dominio que mudam pouco: URL publica, nome do
site, ordem canonica dos livros, linha do tempo e links externos.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DATA = SITE / "data"

BASE_URL = "https://alusionbr.github.io/bibliaonline"
SITE_NAME = "Bíblia em Contexto"

SEFARIA = {
    "Gênesis": "Genesis",
    "Êxodo": "Exodus",
    "Levítico": "Leviticus",
    "Números": "Numbers",
    "Deuteronômio": "Deuteronomy",
    "Josué": "Joshua",
    "Juízes": "Judges",
    "Rute": "Ruth",
    "1 Samuel": "I Samuel",
    "2 Samuel": "II Samuel",
    "1 Reis": "I Kings",
    "2 Reis": "II Kings",
    "1 Crônicas": "I Chronicles",
    "2 Crônicas": "II Chronicles",
    "Esdras": "Ezra",
    "Neemias": "Nehemiah",
    "Ester": "Esther",
    "Jó": "Job",
    "Salmos": "Psalms",
    "Provérbios": "Proverbs",
    "Eclesiastes": "Ecclesiastes",
    "Cânticos": "Song of Songs",
    "Isaías": "Isaiah",
    "Jeremias": "Jeremiah",
    "Lamentações": "Lamentations",
    "Ezequiel": "Ezekiel",
    "Daniel": "Daniel",
    "Oseias": "Hosea",
    "Joel": "Joel",
    "Amós": "Amos",
    "Obadias": "Obadiah",
    "Jonas": "Jonah",
    "Miquéias": "Micah",
    "Naum": "Nahum",
    "Habacuque": "Habakkuk",
    "Sofonias": "Zephaniah",
    "Ageu": "Haggai",
    "Zacarias": "Zechariah",
    "Malaquias": "Malachi",
}

MANUSCRITO_FACSIMILE = "https://commons.wikimedia.org/wiki/Leningrad_Codex"

BOOK_ORDER = [
    "Gênesis", "Êxodo", "Levítico", "Números", "Deuteronômio", "Josué",
    "Juízes", "Rute", "1 Samuel", "2 Samuel", "1 Reis", "2 Reis",
    "1 Crônicas", "2 Crônicas", "Esdras", "Neemias", "Ester", "Jó",
    "Salmos", "Provérbios", "Eclesiastes", "Cânticos", "Isaías",
    "Jeremias", "Lamentações", "Ezequiel", "Daniel", "Oseias", "Joel",
    "Amós", "Obadias", "Jonas", "Miquéias", "Naum", "Habacuque",
    "Sofonias", "Ageu", "Zacarias", "Malaquias", "Mateus", "Marcos",
    "Lucas", "João", "Atos", "Romanos", "1 Coríntios", "2 Coríntios",
    "Gálatas", "Efésios", "Filipenses", "Colossenses",
    "1 Tessalonicenses", "2 Tessalonicenses", "1 Timóteo", "2 Timóteo",
    "Tito", "Filemom", "Hebreus", "Tiago", "1 Pedro", "2 Pedro",
    "1 João", "2 João", "3 João", "Judas", "Apocalipse",
]

# Linha do tempo didatica. Datas aproximadas; nao altera o texto biblico.
TIMELINE = [
    {"nome": "Primórdios", "periodo": "antes de ~2000 a.C.", "descricao": "Da criação ao dilúvio e à dispersão dos povos.", "livros": ["Gênesis"]},
    {"nome": "Patriarcas", "periodo": "~2000–1700 a.C.", "descricao": "Abraão, Isaque, Jacó e José — as promessas a Israel.", "livros": ["Jó"]},
    {"nome": "Êxodo e a Lei", "periodo": "~1500–1400 a.C.", "descricao": "A saída do Egito, a aliança e a Lei no Sinai.", "livros": ["Êxodo", "Levítico", "Números", "Deuteronômio"]},
    {"nome": "Conquista e Juízes", "periodo": "~1400–1050 a.C.", "descricao": "A entrada em Canaã e o período dos juízes.", "livros": ["Josué", "Juízes", "Rute"]},
    {"nome": "Monarquia Unida", "periodo": "~1050–930 a.C.", "descricao": "Saul, Davi e Salomão; salmos e sabedoria.", "livros": ["1 Samuel", "2 Samuel", "1 Reis", "1 Crônicas", "Salmos", "Provérbios", "Eclesiastes", "Cânticos"]},
    {"nome": "Reinos Divididos e Profetas", "periodo": "~930–586 a.C.", "descricao": "Israel e Judá se dividem; os profetas advertem.", "livros": ["2 Reis", "2 Crônicas", "Isaías", "Jeremias", "Lamentações", "Oseias", "Joel", "Amós", "Obadias", "Jonas", "Miquéias", "Naum", "Habacuque", "Sofonias"]},
    {"nome": "Exílio", "periodo": "~586–538 a.C.", "descricao": "Judá no cativeiro na Babilônia.", "livros": ["Ezequiel", "Daniel"]},
    {"nome": "Pós-exílio e Restauração", "periodo": "~538–430 a.C.", "descricao": "O retorno, a reconstrução de Jerusalém e do Templo.", "livros": ["Esdras", "Neemias", "Ester", "Ageu", "Zacarias", "Malaquias"]},
    {"nome": "Período intertestamentário", "periodo": "~430–6 a.C.", "descricao": "Cerca de 400 anos entre Malaquias e os Evangelhos (sem livros no cânon protestante).", "livros": []},
    {"nome": "Vida de Jesus", "periodo": "~6 a.C.–30 d.C.", "descricao": "O nascimento, ministério, morte e ressurreição de Jesus.", "livros": ["Mateus", "Marcos", "Lucas", "João"]},
    {"nome": "Igreja primitiva", "periodo": "~30–95 d.C.", "descricao": "A expansão da Igreja e as cartas apostólicas.", "livros": ["Atos", "Romanos", "1 Coríntios", "2 Coríntios", "Gálatas", "Efésios", "Filipenses", "Colossenses", "1 Tessalonicenses", "2 Tessalonicenses", "1 Timóteo", "2 Timóteo", "Tito", "Filemom", "Hebreus", "Tiago", "1 Pedro", "2 Pedro", "1 João", "2 João", "3 João", "Judas"]},
    {"nome": "Visão final", "periodo": "~95 d.C.", "descricao": "A revelação do fim e da nova criação.", "livros": ["Apocalipse"]},
]

CHRON_INDEX = {
    book: index
    for index, book in enumerate(book for era in TIMELINE for book in era["livros"])
}

GENERATED_DIRS = (
    "versiculos",
    "artigos",
    "ler",
    "anotacoes",
    "estudar",
    "workspace",
    "comunidade",
    "biblioteca",
    "colecoes",
    "cadernos",
    "planos",
    "privacidade",
)
