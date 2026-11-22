"""As vogais tónicas e e o, abertas ou fechadas, medidas no áudio do Sopro (20 Nov 2026).

O conversor pronuncia-pt dá fechado o e e o tónicos sem acento escrito, salvo nas excepções; o Sopro diz
muitos abertos («escola», «chove»), e o modelo aprendeu um «e» que às vezes abre (no passo 79 700 dizia
«já léste» em vez de «já lêste»). Aqui mede-se, em cada frase dos dados,
a primeira ressonância (F1) da vogal tónica de cada palavra com e ou o: a aberta tem o F1 mais alto. A
fronteira de cada voz tira-se das palavras com acento escrito (é, ó abertas; ê, ô fechadas), que o conversor
acerta sempre. Sai um léxico por palavra (mediana das medidas), e a lista das que o conversor erra.

Uso: python scripts/medir_vogais.py   (escreve dados/v1/vogais/)
"""
import json, re, sys, unicodedata
from collections import defaultdict
from pathlib import Path
import numpy as np, soundfile as sf, librosa
sys.path.insert(0, "pronuncia-pt")
import pronuncia_pt as pp

HOP, SR = 256, 24000
SAI = Path("dados/v1/vogais"); SAI.mkdir(parents=True, exist_ok=True)
audio_de = {}
for f in ("manifest.jsonl",):
    for l in open("dados/v1/" + f):
        d = json.loads(l); audio_de[d["id"]] = "dados/v1/" + d["audio"]

def palavras_orto(texto):
    """As palavras escritas, pela mesma ordem que o pecas() as dá."""
    fora = []
    for parte in re.split(r"([,.?!;:\"\x27()—…])", pp._normalizar(texto)):
        if not parte.strip() or parte in pp.PONTUACAO: continue
        fora += [re.sub(r"[^a-zà-üç]", "", w) for w in re.split(r"[\s\-]+", parte.lower()) if re.search(r"[a-zà-ü]", w)]
    return fora

def formantes(x):
    """F1 e F2 de um troço de vogal: LPC a 10 kHz, ordem 12, raízes com banda estreita."""
    if len(x) < 400: return None
    y = librosa.resample(x.astype(np.float32), orig_sr=SR, target_sr=10000)
    y = np.append(y[0], y[1:] - 0.63 * y[:-1]) * np.hamming(len(y))
    try: a = librosa.lpc(y, order=12)
    except Exception: return None
    r = [z for z in np.roots(a) if np.imag(z) > 0]
    f = sorted((np.angle(z) * 10000 / (2 * np.pi), -0.5 * 10000 / np.pi * np.log(abs(z))) for z in r)
    f = [fr for fr, bw in f if 180 < fr < 4500 and bw < 500]
    return (f[0], f[1]) if len(f) >= 2 else None

medidas = []   # (voz, palavra, vogal escrita tónica, fonema do conversor, F1, F2)
for nome in ("train", "validation", "test"):
    for linha in open(f"dados/v1/anotacoes/{nome}.jsonl"):
        d = json.loads(linha)
        if d["id"] not in audio_de: continue
        sims, durs, acc = d["symbols"].split(), d["durations"], d["stress"]
        ini = np.concatenate([[0], np.cumsum(durs)])
        # as palavras nos símbolos: grupos entre <bos>/<sp>/pontuação/<eos>
        grupos, atual = [], []
        for k, s in enumerate(sims):
            if s in ("<bos>", "<eos>", "<sp>") or s in pp.PONTUACAO:
                if atual: grupos.append(atual); atual = []
            else: atual.append(k)
        if atual: grupos.append(atual)
        orto = palavras_orto(d["text"])
        conv = [w for pont, v in pp.pecas(d["text"]) if not pont for w in v]
        if len(orto) != len(grupos) or len(conv) != len(grupos): continue
        wav = None
        for w, g, cw in zip(orto, grupos, conv):
            t = [k for k in g if acc[k] == 1]
            if len(t) != 1: continue
            k = t[0]
            if sims[k] not in ("e", "ɛ", "o", "ɔ") or len(w) < 2: continue
            if durs[k] < 5: continue
            if wav is None: wav, _ = sf.read(audio_de[d["id"]], dtype="float32")
            a, b = ini[k] * HOP, ini[k + 1] * HOP
            m = (b - a) // 4
            fm = formantes(wav[a + m:b - m])
            if fm: medidas.append((d["speaker"], w, sims[k], fm[0], fm[1]))
json.dump(medidas, open(SAI / "medidas.json", "w"), ensure_ascii=False)
print(len(medidas), "medidas")

# a fronteira de cada voz e vogal, pelas palavras de acento escrito
def acento(w, base):
    if base == "e": return "aberta" if "é" in w else "fechada" if "ê" in w else None
    return "aberta" if "ó" in w else "fechada" if "ô" in w else None
limiar = {}
for voz in ("F3", "M1"):
    for base in ("e", "o"):
        ab = [f1 for v, w, s, f1, f2 in medidas if v == voz and s.replace("ɛ", "e").replace("ɔ", "o") == base and acento(w, base) == "aberta"]
        fe = [f1 for v, w, s, f1, f2 in medidas if v == voz and s.replace("ɛ", "e").replace("ɔ", "o") == base and acento(w, base) == "fechada"]
        if len(ab) > 20 and len(fe) > 20:
            limiar[(voz, base)] = (np.median(ab) + np.median(fe)) / 2
            print(voz, base, "aberta", round(np.median(ab)), len(ab), "fechada", round(np.median(fe)), len(fe), "limiar", round(limiar[(voz, base)]))
# cada palavra: a fracção das medidas acima do limiar, nas duas vozes
por = defaultdict(list)
for v, w, s, f1, f2 in medidas:
    base = "e" if s in ("e", "ɛ") else "o"
    if (v, base) in limiar: por[(w, base, s)].append(f1 > limiar[(v, base)])
lex = []
for (w, base, s), vs in por.items():
    if acento(w, base) or len(vs) < 3: continue
    frac = sum(vs) / len(vs)
    ouvido = "aberta" if frac >= 0.7 else "fechada" if frac <= 0.3 else "dúvida"
    conv = "aberta" if s in ("ɛ", "ɔ") else "fechada"
    lex.append({"palavra": w, "vogal": base, "conversor": conv, "ouvido": ouvido, "aberta": round(frac, 2), "n": len(vs)})
lex.sort(key=lambda x: -x["n"])
json.dump(lex, open(SAI / "lexico.json", "w"), ensure_ascii=False, indent=1)
erradas = [x for x in lex if x["ouvido"] != "dúvida" and x["ouvido"] != x["conversor"]]
print(len(lex), "palavras medidas;", len(erradas), "que o conversor erra;", sum(x["ouvido"] == "dúvida" for x in lex), "em dúvida")
print("as mais frequentes que erra:", ", ".join(f"{x[chr(112)+chr(97)+chr(108)+chr(97)+chr(118)+chr(114)+chr(97)]}({x[chr(110)]})" for x in erradas[:40]))
