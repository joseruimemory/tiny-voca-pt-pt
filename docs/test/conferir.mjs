// Confere o pronuncia.js com o Python (os vectores de vectores.py): os fonemas e as fichas do modelo, iguais.
//   node docs/test/conferir.mjs [vectores.json]
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const P = require("../pronuncia.js");
P.definirAbertas(readFileSync(new URL("../assets/abertas.txt", import.meta.url), "utf8"));
const vectores = JSON.parse(readFileSync(process.argv[2] || new URL("vectores.json", import.meta.url), "utf8"));
let erros = 0;
for (const v of vectores) {
  const f = P.fonemas(v.texto), r = P.fichas(v.texto);
  const ids = r ? r.ids : null, acento = r ? r.acento : null;
  const ok = f === v.fonemas && JSON.stringify(ids) === JSON.stringify(v.ids) && (!v.ids || JSON.stringify(acento) === JSON.stringify(v.acento));
  if (!ok && erros++ < 15) console.log("DIFERE:", JSON.stringify(v.texto), "\n  py:", v.fonemas, "\n  js:", f);
}
console.log(`${vectores.length - erros} de ${vectores.length} iguais`);
process.exit(erros ? 1 : 0);
