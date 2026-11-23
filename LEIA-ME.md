# tiny-voca PT-PT

Um modelo pequeno de texto para voz em português europeu, feito sobre o
[tiny-voca](https://github.com/n4ze3m/tiny-voca) de Muhammed Nazeem. Duas vozes
inventadas, F3 (feminina) e M1 (masculina), 4,5 milhões de parâmetros com o
gerador de onda incluído, 18 MB, 24 kHz. Fala cerca de 150 vezes mais depressa
do que o tempo real em quatro núcleos de CPU (Apple M4 Pro).

[Experimentar no navegador](https://joseruimemory.github.io/tiny-voca-pt-pt/) · [Pesos e amostras no Hugging Face](https://huggingface.co/joserui/tiny-voca-pt-pt) · [README in English](README.md)

## O que muda em relação ao tiny-voca

- **A pronúncia.** `pronuncia-pt/` passa o texto a fonemas com regras e uma
  lista de excepções, sem eSpeak e sem dicionário: a pronúncia de Lisboa, as
  vogais átonas reduzidas, o *s* final chiado, a ligação antes de vogal, os
  números por extenso. Escreve os símbolos do eSpeak NG, os mesmos que o
  reconhecedor de fonemas usado no alinhamento.
- **O alinhamento.** Cada fonema português aceita as etiquetas que o
  reconhecedor lhe dá.
- **As tónicas abertas e fechadas, medidas.** O *e* e o *o* tónicos de 514
  palavras foram classificados pela primeira ressonância no áudio do treino
  (`pt-pt/scripts/medir_vogais.py`), e a pronúncia aprendeu-os (versão 0.2.0).

A arquitectura, as perdas e o código de treino são os do tiny-voca, sem
alterações além do inventário de fonemas.

## Instalar e usar

```bash
git clone https://github.com/joseruimemory/tiny-voca-pt-pt.git
cd tiny-voca-pt-pt
pip install -e . -e ./pronuncia-pt
hf download joserui/tiny-voca-pt-pt --local-dir weights
export TINY_VOCA_FRONTEND=pt          # antes de o Python arrancar
python -m tiny_voca.infer --checkpoint weights/tiny-voca-pt-pt.pt \
  --voice F3 --text "Bom dia. Hoje vamos ao jardim." --output bom-dia.wav
```

## Os dados

13 582 frases do Common Voice em português (CC0), filtradas para as de
Portugal (de 41 139); as duas vozes desenhadas por descrição no Qwen3-TTS
VoiceDesign, que não são de ninguém; cada frase dita pelas duas no Sopro, que
lhes dá a pronúncia de Portugal. São 27 163 gravações, 22,8 horas. A fala é
sintética: o modelo aprende a pronúncia de quem fez os dados, e os erros.

## O treino

Num Mac mini M4 Pro de 64 GB, com a receita do tiny-voca: 104 000 passos de
raiz (52,6 h) e mais 16 000 de afinação com as vogais corrigidas (8,1 h),
60,7 horas ao todo. Os scripts estão em `pt-pt/`.

## Créditos e licença

O tiny-voca, de Muhammed Nazeem (Apache-2.0); o Sopro, de Samuel Vitorino
(Apache-2.0); o Qwen3-TTS VoiceDesign, da equipa Qwen (Apache-2.0); o Common
Voice, da Mozilla (CC0); o `facebook/wav2vec2-lv-60-espeak-cv-ft`, no
alinhamento. Licença Apache-2.0, como o original: ver `LICENSE` e `NOTICE`.

Não usem as vozes para se fazerem passar por uma pessoa real.

## No navegador

[`docs/`](docs/) é a página de demonstração, servida pelo GitHub Pages: o modelo
em ONNX (`docs/assets/model.onnx`, corrido pelo ONNX Runtime Web) e o
pronuncia-pt reescrito em JavaScript (`docs/pronuncia.js`). O JavaScript dá
exactamente os fonemas e as fichas do pacote Python: `docs/test/vectores.py`
escreve os vectores de teste com o Python e `node docs/test/conferir.mjs`
confere-os (as 13 582 frases do treino e 32 casos difíceis batem certo).
