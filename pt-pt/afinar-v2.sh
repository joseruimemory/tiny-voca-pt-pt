#!/bin/bash
# O afinamento com as vogais certas (20 Nov 2026): parte do modelo final do treino v1 e treina com as anotações
# corrigidas (pronuncia-pt 0.2.0, as 514 tónicas abertas medidas no áudio do Sopro).
# Espera que o treino v1 acabe; o contador de passos continua (o --init-from traz o do v1): mais 16 000, até ao 120 000, todos na fase adversária (umas 9 h).
cd ~/Projects/tiny-voca-ptpt
while pgrep -f "tiny_voca.train --train dados/v1/anotacoes/" >/dev/null; do sleep 120; done
export TINY_VOCA_FRONTEND=pt
nice -n 10 .venv/bin/python -m tiny_voca.train --train dados/v1/anotacoes-v2/train.jsonl --validation dados/v1/anotacoes-v2/validation.jsonl \
  --output dados/v1/afinar-v2 --config config-v1.json --device mps --init-from dados/v1/treino/last.pt --new-data \
  --steps 120000 --gan-start 8000 --gan-ratio 0.7 --save-every 1000 --keep-every 4000 --log-every 50 >> dados/afinar-v2.log 2>&1
