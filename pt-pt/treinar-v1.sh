#!/bin/bash
# O tiny-voca-pt-pt v1 de ponta a ponta (18 Nov 2026), com as vozes F3 e M1
# (config-v1.json; a primeira volta parou porque a configuração ainda dizia F1):
# espera que a geração acabe, prepara, alinha e treina a receita do original (104 000 passos).
set -euo pipefail
cd ~/Projects/tiny-voca-ptpt
export TINY_VOCA_FRONTEND=pt PYTORCH_ENABLE_MPS_FALLBACK=1 HF_HUB_OFFLINE=1
D=dados/v1
while pgrep -f "scripts/gerar.py" > /dev/null; do sleep 60; done
echo "== geração: $(tail -1 dados/v1.log)"
python3 - <<PY
import json
linhas = [json.loads(l) for l in open("$D/manifest.jsonl")]
# a validação de gerar.py divide-se em duas pela frase: metade validação, metade teste
def parte(r):
    if r["split"] == "train": return "train"
    return "test" if int(r["text_id"][2:], 16) % 2 else "validation"
for s in ("train", "validation", "test"):
    # o campo split tem de dizer a divisão em que a frase fica (o prepare recusa o resto)
    open(f"$D/manifest-{s}.jsonl", "w").write("".join(json.dumps(dict(r, split=s), ensure_ascii=False) + "\n" for r in linhas if parte(r) == s))
print({s: sum(parte(r) == s for r in linhas) for s in ("train", "validation", "test")})
PY
for s in train validation test; do
  nice -n 10 .venv/bin/python -m tiny_voca.prepare --inputs $D/manifest-$s.jsonl --split $s --output $D/features --config config-v1.json --resume
done
echo "== preparado $(date)"
.venv/bin/python -m tiny_voca.annotate --features $D/features --output $D/anotacoes --dataset-revision v1-20261118 --config config-v1.json --device mps
echo "== alinhado $(date)"
.venv/bin/python -m tiny_voca.train --train $D/anotacoes/train.jsonl --validation $D/anotacoes/validation.jsonl --output $D/treino \
  --config config-v1.json --device mps --steps 104000 --gan-start 8000 --gan-ratio 0.7 --max-seconds 400000 \
  --save-every 1000 --keep-every 10000 --log-every 50
echo "== treinado $(date)"
