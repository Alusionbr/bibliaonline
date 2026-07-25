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

# Fac-símile do códice que corresponde a CADA idioma. Antes havia um único
# link (Leningrado) para todo o site — mas Leningrado é o texto massorético
# hebraico, e apontá-lo a partir de um versículo grego é simplesmente errado.
# O Novo Testamento vai para o Sinaítico, já declarado em sources.json.
MANUSCRITO_FACSIMILE = {
    "hebraico": ("Códice de Leningrado", "https://commons.wikimedia.org/wiki/Leningrad_Codex"),
    "aramaico": ("Códice de Leningrado", "https://commons.wikimedia.org/wiki/Leningrad_Codex"),
    "grego": ("Códice Sinaítico", "https://www.codexsinaiticus.org/en/manuscript.aspx"),
}

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

# livro -> (indice da era em TIMELINE, era). Usado para dar contexto histórico
# por livro na listagem (/ler/) e para o acento visual por era na linha do
# tempo — sem duplicar a lista de eras.
BOOK_ERA = {
    book: (era_idx, era)
    for era_idx, era in enumerate(TIMELINE)
    for book in era["livros"]
}

# Referências curadas para o "Versículo do dia" (rotação estável, um por dia).
# Versículos conhecidos e encorajadores, cobrindo Lei, Salmos, Sabedoria,
# Profetas, Evangelhos e Cartas. O build resolve slug/texto a partir de
# verses.json e ignora silenciosamente qualquer referência ausente.
DAILY_VERSES = [
    "Gênesis 1:1", "Josué 1:9", "Deuteronômio 31:6", "Êxodo 14:14",
    "Números 6:24", "Salmos 23:1", "Salmos 23:4", "Salmos 27:1",
    "Salmos 34:8", "Salmos 37:5", "Salmos 46:1", "Salmos 46:10",
    "Salmos 51:10", "Salmos 55:22", "Salmos 91:1", "Salmos 91:11",
    "Salmos 100:4", "Salmos 103:2", "Salmos 118:24", "Salmos 119:105",
    "Salmos 121:1", "Salmos 121:2", "Salmos 139:14", "Salmos 143:8",
    "Provérbios 3:5", "Provérbios 3:6", "Provérbios 16:3", "Provérbios 18:10",
    "Eclesiastes 3:1", "Isaías 40:31", "Isaías 41:10", "Isaías 43:2",
    "Isaías 26:3", "Jeremias 29:11", "Jeremias 33:3", "Lamentações 3:22",
    "Lamentações 3:23", "Miquéias 6:8", "Sofonias 3:17", "Habacuque 3:19",
    "Mateus 5:16", "Mateus 6:33", "Mateus 11:28", "Mateus 28:19",
    "Marcos 12:30", "Lucas 1:37", "Lucas 6:31", "João 1:1",
    "João 3:16", "João 8:12", "João 14:6", "João 14:27",
    "João 15:5", "João 16:33", "Atos 1:8", "Romanos 5:8",
    "Romanos 8:28", "Romanos 8:38", "Romanos 12:2", "Romanos 15:13",
    "1 Coríntios 13:4", "1 Coríntios 13:13", "1 Coríntios 16:14", "2 Coríntios 5:17",
    "2 Coríntios 12:9", "Gálatas 2:20", "Gálatas 5:22", "Efésios 2:8",
    "Efésios 6:10", "Filipenses 4:6", "Filipenses 4:7", "Filipenses 4:13",
    "Colossenses 3:23", "1 Tessalonicenses 5:16", "2 Timóteo 1:7", "Hebreus 11:1",
    "Hebreus 12:1", "Hebreus 13:8", "Tiago 1:5", "1 Pedro 5:7",
    "1 João 4:19", "Apocalipse 21:4",
]

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
    "conta",
    # Estas quatro ficaram fora do build por um tempo e congelaram com a
    # navegação antiga (sem Workspace, sem barra inferior no celular). Voltaram
    # a ser geradas — precisam ser limpas a cada build como as demais.
    "temas",
    "dicionario",
    "mapas",
    "offline",
)
