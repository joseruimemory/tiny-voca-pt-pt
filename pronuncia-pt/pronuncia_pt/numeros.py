"""Números por extenso, em português europeu: cardinais, decimais e horas."""

import re

_UNIDADES = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove",
             "dez", "onze", "doze", "treze", "catorze", "quinze", "dezasseis", "dezassete",
             "dezoito", "dezanove"]
_DEZENAS = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta",
            "oitenta", "noventa"]
_CENTENAS = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos",
             "setecentos", "oitocentos", "novecentos"]


def _ate_mil(n):
    if n < 20:
        return _UNIDADES[n]
    if n < 100:
        d, u = divmod(n, 10)
        return _DEZENAS[d] + ("" if u == 0 else " e " + _UNIDADES[u])
    if n == 100:
        return "cem"
    c, r = divmod(n, 100)
    return _CENTENAS[c] + ("" if r == 0 else " e " + _ate_mil(r))


def cardinal(n):
    """Um inteiro por extenso, até aos biliões (10^12, escala longa)."""
    if n < 0:
        return "menos " + cardinal(-n)
    if n < 1000:
        return _ate_mil(n)
    grupos = []
    for nome_um, nome_varios, base in (("bilião", "biliões", 10**12), ("milhão", "milhões", 10**6)):
        q, n = divmod(n, base)
        if q:
            grupos.append(cardinal(q) + " " + (nome_um if q == 1 else nome_varios))
    q, n = divmod(n, 1000)
    if q:
        grupos.append("mil" if q == 1 else cardinal(q) + " mil")
    if n:
        grupos.append(_ate_mil(n))
    # «mil e cem», «dois mil e trinta»; «mil cento e vinte»
    if len(grupos) > 1 and (n < 100 or n % 100 == 0):
        return ", ".join(grupos[:-1]).replace(", ", " ") + " e " + grupos[-1]
    return " ".join(grupos)


def por_extenso(texto):
    """Os números de um texto por extenso: «3,5» três vírgula cinco; «10h30» dez e
    trinta; «1.250» mil duzentos e cinquenta (ponto de milhares)."""
    texto = re.sub(r"\b(\d{1,2})h(\d{2})\b", lambda m: cardinal(int(m[1])) + " e " + cardinal(int(m[2])), texto)
    texto = re.sub(r"\b(\d{1,2})h\b", lambda m: cardinal(int(m[1])) + " horas", texto)
    texto = re.sub(r"\b\d{1,3}(?:\.\d{3})+\b", lambda m: m[0].replace(".", ""), texto)
    texto = re.sub(r"\b(\d+),(\d{2})\s*€", lambda m: cardinal(int(m[1])) + (" euro" if m[1] == "1" else " euros")
                   + ("" if m[2] == "00" else " e " + cardinal(int(m[2])) + (" cêntimo" if m[2] == "01" else " cêntimos")), texto)
    texto = re.sub(r"\b(\d+),(\d+)\b", lambda m: cardinal(int(m[1])) + " vírgula " + " ".join(
        cardinal(int(c)) for c in m[2]) if len(m[2]) > 2 else cardinal(int(m[1])) + " vírgula " + cardinal(int(m[2])), texto)
    texto = re.sub(r"(\d+)\s*%", lambda m: cardinal(int(m[1])) + " por cento", texto)
    texto = re.sub(r"(\d+)\s*€", lambda m: cardinal(int(m[1])) + (" euro" if m[1] == "1" else " euros"), texto)
    return re.sub(r"\d+", lambda m: cardinal(int(m[0])), texto)
