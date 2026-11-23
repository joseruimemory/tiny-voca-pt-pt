# tiny-voca PT-PT

A small European Portuguese text-to-speech model, built on
[tiny-voca](https://github.com/n4ze3m/tiny-voca) by Muhammed Nazeem. Two
invented voices, F3 (female) and M1 (male), 4.5M parameters including the
waveform generator, 18 MB, 24 kHz. It runs about 150 times faster than real
time on four CPU threads (Apple M4 Pro).

[Weights and samples on Hugging Face](https://huggingface.co/joserui/tiny-voca-pt-pt) · [Leia-me em português](LEIA-ME.md)

## What is different from tiny-voca

- **Portuguese front end.** `pronuncia-pt/` turns European Portuguese text
  into phonemes with rules and an exception list, without eSpeak or a
  dictionary: the Lisbon pronunciation, reduced unstressed vowels,
  /ʃ/ for final *s*, liaison before vowels, numbers read out.
  It writes the eSpeak NG symbol set, which is also what the multilingual
  phoneme recogniser used for alignment emits.
- **Alignment.** Each Portuguese phoneme accepts the recogniser's labels for
  it, so forced alignment works on Portuguese audio.
- **Open and closed stressed vowels measured.** The stressed *e* and *o* of
  514 words were classified as open or closed from their first formant in
  the training audio (`pt-pt/scripts/medir_vogais.py`), and the front end
  learned them (version 0.2.0).

The model architecture, losses and training code are tiny-voca's, unchanged
except for the phoneme inventory.

## Install and run

```bash
git clone https://github.com/joseruimemory/tiny-voca-pt-pt.git
cd tiny-voca-pt-pt
pip install -e . -e ./pronuncia-pt
hf download joserui/tiny-voca-pt-pt --local-dir weights
export TINY_VOCA_FRONTEND=pt          # before Python starts: the inventory is fixed at import
python -m tiny_voca.infer --checkpoint weights/tiny-voca-pt-pt.pt \
  --voice F3 --text "Bom dia. Hoje vamos ao jardim." --output bom-dia.wav
```

Voices: `F3`, `M1`. Options as in tiny-voca: `--speed`, `--pitch-shift`,
`--pitch-range`, `--text-file`.

## Data

| | |
|---|---|
| Sentences | 13,582, from Common Voice Portuguese (CC0), filtered to European usage (`pt-pt/scripts/filtrar.py`, from 41,139) |
| Voices | F3 and M1, designed from text descriptions in Qwen3-TTS VoiceDesign: not the voice of any real person |
| Speech | Every sentence spoken by both voices with Sopro (`samuel-vitorino/sopro-v2-turbo`), which gives them the Portuguese accent |
| Size | 27,163 clips, 22.8 h, 24 kHz; split by sentence: 26,643 train, 236 validation, 284 test |

The speech is synthetic. The model learns the accent of the system that made
the data, and its mistakes.

## Training

On one Mac mini M4 Pro (64 GB), PyTorch MPS, tiny-voca's recipe:

| Stage | Steps | Time |
|---|---:|---:|
| v1, from scratch (adversarial from step 8,000) | 104,000 | 52.6 h |
| v2, fine-tuned with the corrected vowels | +16,000 | 8.1 h |
| Total | 120,000 | 60.7 h |

The scripts are in `pt-pt/`: `scripts/gerar.py` (data), `treinar-v1.sh`,
`afinar-v2.sh`, `continuar-v2.sh`, `config-v1.json`.

## Credits and licence

- tiny-voca, by Muhammed Nazeem: the model, training code and recipe
  (Apache-2.0). Its original README is kept as `README.tiny-voca.md`.
- Sopro, by Samuel Vitorino (Apache-2.0): the Portuguese speech of the data.
- Qwen3-TTS VoiceDesign, by the Qwen team (Apache-2.0): the two voices.
- Common Voice, Mozilla (CC0): the sentences.
- `facebook/wav2vec2-lv-60-espeak-cv-ft`: phoneme recognition for alignment
  (training only).

Apache-2.0, as tiny-voca. See `LICENSE` and `NOTICE`.

```bibtex
@software{nazeem2026tinyvoca,
  author = {Nazeem, Muhammed},
  title  = {tiny-voca: a 4.5M-parameter two-voice English text-to-speech model},
  year   = {2026},
  url    = {https://huggingface.co/n4ze3m/tiny-voca}
}
```

Please do not use the voices to pass as a real person.
