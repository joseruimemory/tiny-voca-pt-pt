// A pronúncia (pronuncia.js, o pronuncia-pt em JavaScript) e o modelo (ONNX Runtime Web) fora da linha principal
// (23 Nov 2026), como o web/public/worker.js do tiny-voca original, mas sem Python no navegador.
// Mensagens que chegam: {type: "load"} e {type: "speak", id, text, voice, speed}. Mensagens que saem: status,
// ready, sentence (com o áudio, logo que é feito), done (o clipe inteiro), error.

const ORT = "https://cdn.jsdelivr.net/npm/onnxruntime-web@1.20.1/dist/";
importScripts("pronuncia.js", ORT + "ort.wasm.min.js");

let session, config;
const status = (text, progress) => postMessage({ type: "status", text, progress });

// Muda quando os ficheiros de assets/ mudarem, para o navegador os ir buscar de novo.
const VERSION = "1";
const MODELO = "https://huggingface.co/joserui/tiny-voca-pt-pt/resolve/main/onnx/model.onnx";

// O que se descarrega fica na cache do navegador: a segunda visita começa sem rede.
async function download(url, label) {
  const key = `${url}?v=${VERSION}`;
  let store = null;
  try {
    store = await caches.open("tiny-voca-pt-pt-" + VERSION);
    const hit = await store.match(key);
    if (hit) return new Uint8Array(await hit.arrayBuffer());
  } catch (error) { store = null; }
  const response = await fetch(key);
  if (!response.ok) throw new Error(`${url}: ${response.status}`);
  const total = Number(response.headers.get("content-length")) || 0;
  let bytes;
  if (!response.body || !total) bytes = new Uint8Array(await response.arrayBuffer());
  else {
    const reader = response.body.getReader(), chunks = [];
    let received = 0;
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value); received += value.length;
      status(label, received / total);
    }
    bytes = new Uint8Array(received);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
  }
  if (store) store.put(key, new Response(bytes)).catch(() => {});
  return bytes;
}

async function load() {
  config = await (await fetch("assets/config.json?v=" + VERSION)).json();
  // os símbolos do modelo têm de ser, pela mesma ordem, os da pronúncia: senão as fichas não querem dizer nada
  if (JSON.stringify(config.symbols) !== JSON.stringify(PronunciaPT.SIMBOLOS)) throw new Error("the phonemizer and the model disagree on the symbols");
  PronunciaPT.definirAbertas(await (await fetch("assets/abertas.txt?v=" + VERSION)).text());
  // o modelo vem do Hugging Face (21 MB): o .gitignore do original deixa os .onnx fora do git, e assim o repositório
  // não carrega com ele
  const bytes = await download(MODELO, "Loading the model");
  status("Starting the model");
  ort.env.wasm.wasmPaths = ORT;
  ort.env.wasm.numThreads = 1;
  session = await ort.InferenceSession.create(bytes, { executionProviders: ["wasm"] });
}

// As frases, sem cortar depois de um título, de uma inicial ou dentro de um número.
const ABREVIATURAS = /(?:(?<![\p{L}])(?:sr|sra|srs|dr|dra|drs|prof|profa|eng|arq|exmo|exma|etc|pág|págs|vol|av|n\.º|cf|ex)|(?<![\p{L}])\p{Lu})\.$/iu;
function sentences(text) {
  const parts = [];
  let current = "";
  for (const piece of text.replace(/\s+/g, " ").trim().split(/(?<=[.!?…]["')\]»]?)\s+(?=["'(\[«]?[\p{Lu}\p{N}])/u)) {
    current = current ? current + " " + piece : piece;
    if (!ABREVIATURAS.test(current)) { parts.push(current); current = ""; }
  }
  if (current) parts.push(current);
  return parts.filter((part) => /[\p{L}\p{N}]/u.test(part));
}

// Um ponto final quando o texto acaba sem sinal: antes do sinal a voz alonga a última sílaba e deixa cair o som;
// sem ele, o áudio corta-se. Como tiny_voca.infer.finished.
function finished(text) {
  const body = text.replace(/\s+$/, "");
  if (!body) return text;
  const last = body.split(/\s+/).pop();
  const marked = /[\p{L}\p{N}]/u.test(last) ? /[.!?…,;:]["'”’)\]»]*$/.test(last) : /[.!?…]/.test(last) || /^[,;:]$/.test(last);
  return marked ? text : body + ".";
}

// Uma elocução leva no máximo max_tokens fichas; uma frase mais comprida corta-se nas vírgulas, depois nas palavras.
function fit(sentence) {
  const result = PronunciaPT.fichas(sentence);
  if (!result) return [];
  if (result.ids.length <= config.max_tokens - 12) return [result];
  const pieces = sentence.split(/(?<=[,;:—])\s+/);
  if (pieces.length > 1) return pieces.flatMap(fit);
  const words = sentence.split(" ");
  if (words.length < 2) return [];
  const half = Math.ceil(words.length / 2);
  return [...fit(words.slice(0, half).join(" ")), ...fit(words.slice(half).join(" "))];
}

async function synthesize(phones, voice, speed) {
  const count = phones.ids.length;
  const integers = (values) => new ort.Tensor("int64", BigInt64Array.from(values.map(BigInt)), [1, count]);
  const scalar = (value) => new ort.Tensor("float32", Float32Array.from([value]), [1]);
  const output = await session.run({
    tokens: integers(phones.ids), stress: integers(phones.acento),
    voice: new ort.Tensor("int64", BigInt64Array.from([BigInt(voice)]), [1]),
    speed: scalar(speed), pitch_shift: scalar(0), pitch_range: scalar(1),
  });
  return output.audio.data;
}

// O modelo passa às vezes de 1,0, o que cortaria no ficheiro de 16 bits: o clipe inteiro baixa então.
const PEAK = 0.99;
function limitPeak(samples) {
  let loudest = 0;
  for (let i = 0; i < samples.length; i++) loudest = Math.max(loudest, Math.abs(samples[i]));
  if (loudest > PEAK) for (let i = 0; i < samples.length; i++) samples[i] *= PEAK / loudest;
}

async function speak({ id, text, voice, speed }) {
  const started = performance.now();
  const list = sentences(finished(text));
  const chunks = [];
  let phonemeTime = 0, modelTime = 0;
  for (let index = 0; index < list.length; index++) {
    let mark = performance.now();
    const utterances = fit(list[index]);
    const spoken = PronunciaPT.fonemas(list[index]);
    phonemeTime += performance.now() - mark;
    for (const phones of utterances) {
      mark = performance.now();
      const audio = await synthesize(phones, voice, speed);
      modelTime += performance.now() - mark;
      chunks.push(audio);
      const heard = audio.slice();
      limitPeak(heard);
      postMessage({ type: "sentence", id, index, total: list.length, phonemes: spoken, audio: heard,
                    sampleRate: config.sample_rate }, [heard.buffer]);
    }
  }
  if (!chunks.length) {
    postMessage({ type: "error", id, message: "Nothing to read: type some Portuguese text.", plain: true });
    return;
  }
  const length = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const audio = new Float32Array(length);
  let offset = 0;
  for (const chunk of chunks) { audio.set(chunk, offset); offset += chunk.length; }
  limitPeak(audio);
  postMessage({ type: "done", id, audio, sampleRate: config.sample_rate, phonemeTime, modelTime,
                totalTime: performance.now() - started }, [audio.buffer]);
}

onmessage = async ({ data }) => {
  try {
    if (data.type === "load") {
      await load();
      postMessage({ type: "ready", voices: config.voices, sampleRate: config.sample_rate });
    } else if (data.type === "speak") {
      await speak(data);
    }
  } catch (error) {
    postMessage({ type: "error", id: data.id, message: String(error && error.message || error) });
  }
};
