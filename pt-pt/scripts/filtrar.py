"""Frases do Common Voice (CC0) que um português de Portugal diria: fora as do Brasil.

Sinais do Brasil: o gerúndio depois de estar/ficar/continuar, «em um», «você» como
tratamento corrente, ê/ô onde Portugal tem é/ó (econômico), palavras só de lá.
Ficam frases completas: maiúscula, ponto final, cinco a vinte palavras.
"""
import re, sys, collections
entrada, saida = sys.argv[1:3]
BR_PALAVRAS = set("""você vocês cotidiano ônibus trem time fato fatos registro registros banheiro geladeira
celular moça moço garoto garota xícara grama café-da-manhã aluguel tela usuário usuários
equipe planejamento esporte esportes goleiro gol academia açougue pedágio carona camisinha
caminhão sorvete suco bonde favela legal cara gente nossa tô tá pra pro pros pras né
mídia trânsito síndico prefeito prefeitura estado-membro abacaxi mandioca aipim jeito""".split())
BR_RE = [
    re.compile(r"\b(?:est|fic|continu|and|vi)\w*\s+(?:\w+\s+)?\w+(?:ando|endo|indo)\b", re.I),
    re.compile(r"\bem (?:um|uma|uns|umas)\b", re.I),
    re.compile(r"\w*(?:ômic|êmic|ônic|ênic|ôm|ên)\w*", re.I),
    re.compile(r"\b\w+(?:ção|são)\b.*\bseu\b", re.I) if False else re.compile(r"^$"),
    re.compile(r"\b(?:me|se|te|lhe) (?:\w+)\b(?<![.,])$", re.I) if False else re.compile(r"^$"),
]
GENERUNDIO_SOLTO = re.compile(r"\b\w{3,}(?:ando|endo|indo)\b", re.I)
fora, motivos = [], collections.Counter()
vistas = set()
for linha in open(entrada, encoding="utf-8"):
    f = linha.strip()
    if not f or f in vistas:
        continue
    vistas.add(f)
    palavras = re.findall(r"[\wÀ-ÿ-]+", f)
    if not (5 <= len(palavras) <= 20) or not f[0].isupper() or f[-1] not in ".!?":
        motivos["incompleta"] += 1; continue
    if re.search(r"[0-9@#/&*_<>]|[A-Z]{3,}", f):
        motivos["números e siglas"] += 1; continue
    if {p.lower() for p in palavras} & BR_PALAVRAS:
        motivos["palavra do Brasil"] += 1; continue
    if any(r.search(f) for r in BR_RE[:3]) or GENERUNDIO_SOLTO.search(f):
        motivos["construção do Brasil"] += 1; continue
    fora.append(f)
open(saida, "w", encoding="utf-8").write("\n".join(fora) + "\n")
print(len(fora), "frases;", dict(motivos))
