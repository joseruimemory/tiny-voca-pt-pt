"""Som a som: com que probabilidade o alinhador encontra cada fonema do conversor,
e o que ouve em vez dele quando hesita. Sobre o lote de teste (18 Nov 2026)."""
import json, collections, sys
import numpy as np, soundfile as sf
from tiny_voca.align import PhoneRecognizer, token_spans
from tiny_voca.text import phonemize, PHONE_SET
rec = PhoneRecognizer("mps"); inv = {v: k for k, v in rec.vocabulary.items()}
linhas = [json.loads(l) for l in open("dados/teste/manifest.jsonl")][:int(sys.argv[1])]
prob, ouve = collections.defaultdict(list), collections.defaultdict(collections.Counter)
for r in linhas:
    w, sr = sf.read("dados/teste/" + r["audio"], dtype="float32")
    sims = [s for s in phonemize(r["text"]).symbols if s in PHONE_SET]
    labels = [rec.label(s) for s in sims]
    lp = rec.log_probs(w, sr)
    for s, lab, (a, b) in zip(sims, labels, token_spans(lp, labels, rec.blank)):
        p = float(np.exp(lp[a:b+1, lab]).mean()); prob[s].append(p)
        if p < 0.5:
            seg = lp[a:b+1].copy(); seg[:, rec.blank] = -1e9
            ouve[s][inv[int(seg.mean(0).argmax())]] += 1
print("fonema  n     média  fracos  ouve em vez")
for s in sorted(prob, key=lambda k: np.mean(prob[k])):
    v = prob[s]; print(f"{s:6} {len(v):5} {np.mean(v):6.2f} {np.mean(np.array(v) < 0.5):6.0%}   {ouve[s].most_common(4)}")
