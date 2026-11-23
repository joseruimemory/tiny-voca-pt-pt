"""Os vectores de teste do pronuncia.js (23 Nov 2026): o que o Python dá (pronuncia-pt e tiny_voca.text com o front
end pt) para as frases dos dados e para casos difíceis. O teste (node docs/test/conferir.mjs) exige que o JavaScript
dê exactamente o mesmo, fonema a fonema.

    TINY_VOCA_FRONTEND=pt PYTHONPATH=src:pronuncia-pt python docs/test/vectores.py [--todas] > docs/test/vectores.json
"""
import json, random, sys
from pathlib import Path
import pronuncia_pt
from tiny_voca.text import phonemize, NothingToPronounce

DIFICEIS = [
    "Bom dia. Hoje vamos ao jardim ver as roseiras e podar as macieiras, antes que chegue o Inverno.",
    "Quanto custa? São 3,50 € por quilo, às 10h30.", "Custa 1,01 € e 21,00 €.", "Chego às 9h e saio às 17h05.",
    "Em 1942 havia 1.250 sócios; em 2024, 123456789012345.", "Taxa de 7 % e 100%.", "Pi é 3,14159; meio é 0,5.",
    "A acção do director foi óptima, de facto.", "O exacto objecto da adopção.", "Já leste o livro? O vento vem de leste, a leste do rio.",
    "Ele disse: «Não!» — e foi-se embora… (sem mais).", "Dá-mo, no-lo disse.", "O ÑANDÚ e o pinguim.", "Ação, ótimo, diretor, fato.",
    "Hífen-com-hífen e ex-aluno.", "Quê? Porquê! Porque sim.", "Os ossos, as asas e os olhos.", "Seis homens e dez mulheres.",
    "Extra texto exame êxito.", "Queijo, guerra, aguenta, quando, linguiça, frequente.", "Rainha, moinho, saúde, país, juiz.",
    "Mãe, pães, põe, mão, irmãos, falam, falaram.", "Também tem bens e homens.", "Rio, rua, carro, honra, Israel.",
    "...", "!!!", "123", "Olá   mundo\n\ttabs", "“Aspas” ‘simples’ – travessão ― outro [parênteses].",
    "Café com açúcar à tarde.", "Sexta, próximo, máximo, táxi, fixo.", "Choveu muito na quinta-feira.",
]

frases = [l for l in Path("pt-pt/frases-pt-pt.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
if "--todas" not in sys.argv:
    random.seed(23); frases = random.sample(frases, 600)
fora = []
for t in DIFICEIS + frases:
    try:
        p = phonemize(t); r = {"texto": t, "fonemas": pronuncia_pt.fonemas(t), "ids": list(p.ids), "acento": list(p.stress)}
    except NothingToPronounce:
        r = {"texto": t, "fonemas": pronuncia_pt.fonemas(t), "ids": None}
    except Exception as e:          # o Python não dá conta do texto: o JavaScript não tem de dar o mesmo
        print(f"saltada ({type(e).__name__}): {t!r}", file=sys.stderr); continue
    fora.append(r)
json.dump(fora, sys.stdout, ensure_ascii=False, indent=0)
