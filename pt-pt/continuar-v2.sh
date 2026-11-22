#!/bin/bash
# Continua o afinamento v2 (21 Nov 2026): a primeira volta parou ao fim de uma hora, porque o afinar-v2.sh não
# passava --max-seconds e o predefinido é 3600. Retoma o mesmo run do last.pt, até ao passo 120 000.
cd ~/Projects/tiny-voca-ptpt
export TINY_VOCA_FRONTEND=pt
nice -n 10 .venv/bin/python -m tiny_voca.train --train dados/v1/anotacoes-v2/train.jsonl --validation dados/v1/anotacoes-v2/validation.jsonl \
  --output dados/v1/afinar-v2 --config config-v1.json --device mps --resume dados/v1/afinar-v2/last.pt \
  --steps 120000 --gan-start 8000 --gan-ratio 0.7 --max-seconds 400000 --save-every 1000 --keep-every 4000 --log-every 50 >> dados/afinar-v2.log 2>&1
echo "== treinado $(date)" >> dados/afinar-v2.log
