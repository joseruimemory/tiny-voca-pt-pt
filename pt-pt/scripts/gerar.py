"""Os dados do tiny-voca PT-PT: cada frase dita pelas duas vozes, pelo Sopro.

As vozes são inventadas (desenhadas no Qwen3-TTS VoiceDesign) e o Sopro, que
clona a voz a partir de uma gravação, dá-lhes a pronúncia de Portugal. Cada frase
fica nas duas vozes, e a divisão treino/validação faz-se por frase.

Retoma onde parou: um áudio que já existe não se refaz. Saída: <raiz>/audio/<id>.flac
e <raiz>/manifest.jsonl, na forma que o tiny_voca.prepare lê.
"""
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np, soundfile as sf

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--frases", type=Path, required=True)
ap.add_argument("--raiz", type=Path, required=True)
ap.add_argument("--referencias", type=Path, required=True, help="Pasta com <voz>.wav")
ap.add_argument("--vozes", nargs="+", default=["F1", "M1"])
ap.add_argument("--limite", type=int)
ap.add_argument("--validacao", type=float, default=0.02)
ap.add_argument("--device", default="cpu")
a = ap.parse_args()

from sopro import SoproTTS
tts = SoproTTS.from_pretrained("samuel-vitorino/sopro-v2-turbo", device=a.device)
taxa = int(tts.sample_rate)
refs = {v: tts.prepare_reference(ref_audio_path=str(a.referencias / f"{v}.wav"), seconds=15) for v in a.vozes}
frases = [f for f in a.frases.read_text(encoding="utf-8").splitlines() if f.strip()][:a.limite]
(a.raiz / "audio").mkdir(parents=True, exist_ok=True)
manifesto = a.raiz / "manifest.jsonl"
feitos = {}
if manifesto.exists():
    for l in manifesto.read_text(encoding="utf-8").splitlines():
        r = json.loads(l); feitos[r["id"]] = r
inicio, falados, rejeitados = time.time(), 0.0, []
with manifesto.open("a", encoding="utf-8") as m:
    for n, frase in enumerate(frases):
        tid = "cv" + hashlib.sha1(frase.encode()).hexdigest()[:10]
        split = "validation" if int(tid[2:], 16) % 1000 < a.validacao * 1000 else "train"
        for voz in a.vozes:
            ident = f"{tid}_{voz}"
            if ident in feitos:
                continue
            # Uma frase leva 0,04 a 0,16 s por letra; fora disso o Sopro tropeçou: outra vez.
            for tentativa in range(3):
                w = np.asarray(tts.synthesize(frase, ref=refs[voz], lang="pt"), dtype=np.float32).reshape(-1)
                dur = len(w) / taxa
                if 0.04 * len(frase) <= dur <= 0.16 * len(frase) + 1:
                    break
            else:
                rejeitados.append(ident); continue
            pico = float(np.max(np.abs(w))) or 1.0
            sf.write(a.raiz / "audio" / f"{ident}.flac", w * (0.95 / pico), taxa, subtype="PCM_16")
            falados += dur
            m.write(json.dumps({"id": ident, "text_id": tid, "voice_id": voz, "text": frase, "split": split,
                                "audio": f"audio/{ident}.flac", "duration_seconds": round(dur, 3),
                                "origin": "common-voice-pt", "source_license": "CC0-1.0",
                                "teacher_model": "samuel-vitorino/sopro-v2-turbo", "reference_audio": f"{voz}.wav"},
                               ensure_ascii=False) + "\n")
            m.flush()
        if n % 25 == 0:
            gasto = time.time() - inicio
            print(json.dumps({"frase": n, "audio_h": round(falados / 3600, 3), "tempo_real": round(gasto / max(falados, 1e-9), 3),
                              "rejeitados": len(rejeitados)}), flush=True)
print(json.dumps({"fim": True, "audio_h": round(falados / 3600, 3), "rejeitados": rejeitados}), flush=True)
