"""pronuncia-pt: texto em português europeu (pronúncia de Lisboa) para fonemas.

Regras e uma lista de excepções, sem dicionário de terceiros, sem modelos e sem
eSpeak: tudo sob Apache-2.0. Os símbolos são os do eSpeak NG para português,
que são também as etiquetas do reconhecedor de fonemas multilíngue usado no
alinhamento (facebook/wav2vec2-lv-60-espeak-cv-ft).

    >>> from pronuncia_pt import fonemas
    >>> fonemas("O pão quente.")
    'u ˈpɐ̃ʊ̃ ˈkẽtɨ .'

Lê as duas grafias: a de antes do Acordo de 1990 («acção», «óptimo»), com as
consoantes mudas caladas, e a de depois.
"""

import re
import unicodedata

from .numeros import por_extenso

VERSAO = "0.2.0"

CONSOANTES = ("p", "b", "t", "d", "k", "ɡ", "f", "v", "s", "z", "ʃ", "ʒ",
              "m", "n", "ɲ", "l", "ʎ", "ɾ", "ʁ", "j", "w")
VOGAIS = ("i", "e", "ɛ", "a", "ɐ", "ɔ", "o", "u", "ɨ", "ĩ", "ẽ", "ɐ̃", "õ", "ũ", "ɐ̃ʊ̃")
FONEMAS = CONSOANTES + VOGAIS
PONTUACAO = (",", ".", "?", "!", ";", ":", '"', "'", "(", ")", "—", "…")

_ACENTOS = {"á": ("a", "´"), "à": ("a", "`"), "â": ("a", "^"), "ã": ("a", "~"),
            "é": ("e", "´"), "ê": ("e", "^"), "í": ("i", "´"), "ó": ("o", "´"),
            "ô": ("o", "^"), "õ": ("o", "~"), "ú": ("u", "´"), "ü": ("u", "¨"), "è": ("e", "´"),
            "y": ("i", None)}
_VOZEADAS = set("bdɡvzʒmnɲlʎɾʁ")
_VOGAL_LETRA = set("aeiou")

# Palavras que as regras não acertam, ou átonas (sem acento de palavra). A sílaba
# tónica vem marcada com ˈ antes da vogal.
EXCECOES = {
    "quero": "k ˈɛ ɾ u", "quer": "k ˈɛ ɾ",
    # átonas
    "o": "u", "a": "ɐ", "os": "u S", "as": "ɐ S", "e": "i", "é": "ˈɛ", "de": "d ɨ",
    "do": "d u", "da": "d ɐ", "dos": "d u S", "das": "d ɐ S", "que": "k ɨ", "se": "s ɨ",
    "me": "m ɨ", "te": "t ɨ", "lhe": "ʎ ɨ", "lhes": "ʎ ɨ S", "nos": "n u S", "vos": "v u S",
    "no": "n u", "na": "n ɐ", "nas": "n ɐ S", "ao": "a w", "aos": "a w S", "à": "a", "às": "a S",
    "em": "ɐ̃ j", "com": "k õ", "por": "p u ɾ", "para": "p ɐ ɾ ɐ", "pelo": "p ɨ l u",
    "pela": "p ɨ l ɐ", "pelos": "p ɨ l u S", "pelas": "p ɨ l ɐ S", "mas": "m ɐ S",
    "nem": "n ɐ̃ j", "sem": "s ɐ̃ j", "um": "ˈũ", "uns": "ˈũ S", "num": "n ũ", "numa": "n ˈu m ɐ",
    "ou": "ˈo", "lo": "l u", "la": "l ɐ", "los": "l u S", "las": "l ɐ S", "no-lo": "n u l u",
    # tónicas que as regras erram
    "muito": "m ˈũ j t u", "muita": "m ˈũ j t ɐ", "muitos": "m ˈũ j t u S", "muitas": "m ˈũ j t ɐ S",
    "ele": "ˈe l ɨ", "eles": "ˈe l ɨ S", "ela": "ˈɛ l ɐ", "elas": "ˈɛ l ɐ S",
    "este": "ˈe ʃ t ɨ", "esta": "ˈɛ ʃ t ɐ", "estes": "ˈe ʃ t ɨ S", "estas": "ˈɛ ʃ t ɐ S",
    "esse": "ˈe s ɨ", "essa": "ˈɛ s ɐ", "isto": "ˈi ʃ t u", "isso": "ˈi s u",
    "aquele": "ɐ k ˈe l ɨ", "aquela": "ɐ k ˈɛ l ɐ", "aquilo": "ɐ k ˈi l u",
    "hoje": "ˈo ʒ ɨ", "sete": "s ˈɛ t ɨ", "nove": "n ˈɔ v ɨ", "novo": "n ˈo v u", "nova": "n ˈɔ v ɐ",
    "novos": "n ˈɔ v u S", "novas": "n ˈɔ v ɐ S", "porta": "p ˈɔ ɾ t ɐ", "pedra": "p ˈɛ d ɾ ɐ",
    "festa": "f ˈɛ ʃ t ɐ", "certo": "s ˈɛ ɾ t u", "certa": "s ˈɛ ɾ t ɐ", "terra": "t ˈɛ ʁ ɐ",
    "guerra": "ɡ ˈɛ ʁ ɐ", "velho": "v ˈɐ ʎ u", "velha": "v ˈɐ ʎ ɐ", "mesmo": "m ˈe ʒ m u",
    "mesma": "m ˈe ʒ m ɐ", "fora": "f ˈɔ ɾ ɐ", "agora": "ɐ ɡ ˈɔ ɾ ɐ", "hora": "ˈɔ ɾ ɐ",
    "horas": "ˈɔ ɾ ɐ S", "cedo": "s ˈe d u", "perto": "p ˈɛ ɾ t u", "pé": "p ˈɛ", "café": "k ɐ f ˈɛ",
    "sexta": "s ˈɐ j ʃ t ɐ", "seis": "s ˈɐ j S", "dez": "d ˈɛ S", "três": "t ɾ ˈe S",
    "dois": "d ˈo j S", "doze": "d ˈo z ɨ", "treze": "t ɾ ˈe z ɨ", "dezasseis": "d ɨ z ɐ s ˈɐ j S",
    "táxi": "t ˈa k s i", "fixo": "f ˈi k s u", "fixa": "f ˈi k s ɐ", "sexo": "s ˈɛ k s u",
    "complexo": "k õ p l ˈɛ k s u", "reflexo": "ʁ ɨ f l ˈɛ k s u", "fluxo": "f l ˈu k s u",
    "tóxico": "t ˈɔ k s i k u", "próximo": "p ɾ ˈɔ s i m u", "próxima": "p ɾ ˈɔ s i m ɐ",
    "máximo": "m ˈa s i m u", "auxílio": "a w s ˈi l j u", "trouxe": "t ɾ ˈo s ɨ",
    "exame": "i z ˈɐ m ɨ", "exemplo": "i z ˈẽ p l u", "existe": "i z ˈi ʃ t ɨ",
    "existir": "i z i ʃ t ˈi ɾ", "êxito": "ˈɐ j z i t u", "exacto": "i z ˈa t u", "exacta": "i z ˈa t ɐ",
    "nunca": "n ˈũ k ɐ", "bom": "b ˈõ", "boa": "b ˈo ɐ", "boas": "b ˈo ɐ S", "bons": "b ˈõ S",
    "rio": "ʁ ˈi u", "dia": "d ˈi ɐ", "dias": "d ˈi ɐ S", "tia": "t ˈi ɐ", "tio": "t ˈi u",
    "rua": "ʁ ˈu ɐ", "lua": "l ˈu ɐ", "sua": "s ˈu ɐ", "suas": "s ˈu ɐ S", "tua": "t ˈu ɐ",
    "voo": "v ˈo u", "coelho": "k u ˈɐ ʎ u", "olho": "ˈo ʎ u", "olhos": "ˈɔ ʎ u S",
    "obra": "ˈɔ b ɾ ɐ", "onde": "ˈõ d ɨ", "homem": "ˈɔ m ɐ̃ j", "homens": "ˈɔ m ɐ̃ j S",
    "mulher": "m u ʎ ˈɛ ɾ", "flor": "f l ˈo ɾ", "flores": "f l ˈo ɾ ɨ S", "melhor": "m ɨ ʎ ˈɔ ɾ",
    "pior": "p j ˈɔ ɾ", "maior": "m ɐ j ˈɔ ɾ", "menor": "m ɨ n ˈɔ ɾ", "sol": "s ˈɔ l",
    "avó": "ɐ v ˈɔ", "avô": "ɐ v ˈo", "só": "s ˈɔ", "nós": "n ˈɔ S", "vós": "v ˈɔ S",
    "sobre": "s ˈo b ɾ ɨ", "depois": "d ɨ p ˈo j S", "também": "t ɐ̃ b ˈɐ̃ j",
    "porque": "p u ɾ k ˈe", "porquê": "p u ɾ k ˈe", "quando": "k w ˈɐ̃ d u",
}

# Antes do Acordo, o c e o p antes de ç, c e t calavam-se quase sempre («acção»,
# «óptimo»); nestas palavras ouvem-se, e escrevem-se igual depois do Acordo.
_PRONUNCIADAS = re.compile(r"^(?:facto|pacto|compact|contact|intact|tact|impact|ficç|convicç|fricç|"
                           r"egípc|rapt|apt|inapt|adept|erupç|núpc|opç|opcion|eucalipt|cépt|"
                           r"conceptu|ruptur|corrupt|abrupt|bact|caract|dicç|seccion)")


def _mudas(p):
    if _PRONUNCIADAS.match(p):
        return p
    # e abre a vogal antes dela: «director» diɾɛˈtoɾ, «acção» aˈsɐ̃ʊ̃ (marca: maiúscula)
    return re.sub(r"([aeo])[cp](?=[cçt])", lambda m: m[1].upper(), re.sub(r"(?<=[iuáéíóúâêô])[cp](?=[cçt])", "", p))


def _unidades(p):
    """A palavra em unidades: vogais (base, acento) e consoantes (dígrafos juntos)."""
    u, i = [], 0
    while i < len(p):
        c, d = p[i], p[i:i+2]
        if d in ("ch", "lh", "nh", "rr", "ss"):
            u.append(("C", d)); i += 2; continue
        if d in ("qu", "gu", "qü", "gü") and i + 2 < len(p):
            seguinte = _ACENTOS.get(p[i+2], (p[i+2], None))[0]
            if seguinte in "ei" and d[1] == "u":
                u.append(("C", "k" if c == "q" else "ɡ")); i += 2; continue
            if seguinte in "aoei":
                u.append(("C", "k" if c == "q" else "ɡ")); u.append(("C", "w")); i += 2; continue
        if c in "AEO":
            u.append(("V", c.lower(), "aberta")); i += 1; continue
        if c in _VOGAL_LETRA or c in _ACENTOS:
            base, acento = _ACENTOS.get(c, (c, None))
            u.append(("V", base, acento)); i += 1; continue
        if c == "h":
            i += 1; continue
        u.append(("C", c)); i += 1
    return u


def _nucleos(u):
    """Os índices das vogais que são núcleo de sílaba; as outras são semivogais."""
    nuc = []
    for k, x in enumerate(u):
        if x[0] != "V":
            continue
        ant = u[k-1] if k else None
        if ant and ant[0] == "V" and x[2] in (None, "¨"):
            # ão, ãe, õe: a segunda é semivogal
            if ant[2] == "~" and x[1] in "oe":
                continue
            if x[1] in "iu":
                seg = u[k+1:k+3]
                hiato = seg and (seg[0] == ("C", "nh") or (seg[0][0] == "C" and seg[0][1] in "lmnrz"
                                 and (len(seg) == 1 or seg[1][0] == "C")))
                if not hiato:
                    continue
        nuc.append(k)
    return nuc


def _tonica(p, u, nuc):
    if not nuc:
        return None
    for k in nuc:
        if u[k][2] in ("´", "^"):
            return k
    for k in reversed(nuc):
        if u[k][2] == "~":
            return k
    if len(nuc) == 1:
        return nuc[0]
    if re.search(r"(?:[aeoAEO]s?|am|em|ens)$", p):
        return nuc[-2]
    return nuc[-1]


# As abertas medidas no áudio (0.2.0): a tónica e/o destas palavras é ɛ/ɔ, não e/o.
ABERTAS = {l.strip() for l in open(__import__("os").path.join(__import__("os").path.dirname(__file__), "abertas.txt"), encoding="utf-8") if l.strip() and not l.startswith("#")}


def _palavra(p):
    fora = _palavra_regras(p)
    if p in ABERTAS:
        fora = [({"e": "ɛ", "o": "ɔ"}.get(f, f), a) if a else (f, a) for f, a in fora]
    return fora


def _palavra_regras(p):
    """Uma palavra em fonemas: lista de (fonema, acento), com «S» para a sibilante
    final, que depende da palavra seguinte."""
    if p in EXCECOES:
        fora = []
        for f in EXCECOES[p].split():
            fora.append((f[1:], 1) if f.startswith("ˈ") else (f, 0))
        return fora
    p = _mudas(p)
    u = _unidades(p)
    nuc = _nucleos(u)
    ton = _tonica(p, u, nuc)
    fora, salta, n = [], set(), len(u)

    def vogal_seg(k):
        return k + 1 < n and u[k+1][0] == "V"

    for k, x in enumerate(u):
        if k in salta:
            continue
        ant = u[k-1] if k else None
        seg = u[k+1] if k + 1 < n else None
        seg2 = u[k+2] if k + 2 < n else None
        fim = k == n - 1
        if x[0] == "V":
            base, acento = x[1], x[2]
            tonica = k == ton
            if k not in nuc:
                # semivogal: ou → o; ão → ɐ̃ʊ̃ (tratado na vogal); ei → ɐj (tratado na vogal)
                if base == "u" and ant and ant[1] == "o" and ant[2] in (None, "^"):
                    continue
                fora.append(("j" if base in "ie" else "w", 0))
                continue
            # nasal: til, ou m/n antes de consoante ou no fim
            nasal_mn = seg and seg[0] == "C" and seg[1] in ("m", "n") and (seg2 is None or seg2[0] == "C")
            if nasal_mn:
                salta.add(k + 1)
            nasal = acento == "~" or nasal_mn
            # -em, -ens, -ém no fim: ɐ̃j
            if base == "e" and nasal_mn and (seg2 is None or (seg2 == ("C", "s") and k + 3 == n)):
                fora += [("ɐ̃", int(tonica)), ("j", 0)]
                continue
            # -am átono no fim: ɐ̃ʊ̃ (falam)
            if base == "a" and nasal_mn and seg2 is None and not tonica:
                fora.append(("ɐ̃ʊ̃", 0)); continue
            if base == "a" and acento == "~" and seg and seg[0] == "V" and seg[1] == "o":
                fora.append(("ɐ̃ʊ̃", int(tonica))); salta.add(k + 1); continue
            if nasal:
                fora.append(({"a": "ɐ̃", "e": "ẽ", "i": "ĩ", "o": "õ", "u": "ũ"}[base], int(tonica)))
                if acento == "~" and seg and seg[0] == "V" and seg[1] == "e":
                    fora.append(("j", 0)); salta.add(k + 1)
                continue
            # e antes de x e consoante: ɐjʃ («extra», «texto»)
            if base == "e" and seg == ("C", "x") and seg2 and seg2[0] == "C" and acento is None:
                fora += [("ɐ", int(tonica)), ("j", 0), ("ʃ", 0)]; salta.add(k + 1); continue
            # ditongo ei: ɐj (é: ɛj)
            if base == "e" and seg and seg[0] == "V" and seg[1] == "i" and (k + 1) not in nuc:
                fora.append(("ɛ" if acento == "´" else "ɐ", int(tonica))); continue
            if tonica:
                if base == "a":
                    v = "a" if acento == "´" else "ɐ" if acento == "^" else (
                        "ɐ" if seg and seg[0] == "C" and seg[1] in ("m", "n", "nh") and seg2 and seg2[0] == "V" else "a")
                elif base == "e":
                    v = "ɛ" if acento in ("´", "aberta") else "e" if acento == "^" else (
                        "ɐ" if seg and seg[0] == "C" and seg[1] in ("lh", "nh", "ch", "j") else "e")
                elif base == "o":
                    v = "ɔ" if acento in ("´", "aberta") else "o"
                else:
                    v = base
                fora.append((v, 1)); continue
            # átona
            if base == "o" and seg and seg[0] == "V" and seg[1] == "u" and (k + 1) not in nuc:
                fora.append(("o", 0)); continue
            if base in "eiou" and vogal_seg(k) and (k + 1) in nuc and acento is None:
                fora.append(("j" if base in "ei" else "w", 0)); continue
            if acento in ("`", "aberta"):
                fora.append(({"a": "a", "e": "ɛ", "o": "ɔ"}[base], 0)); continue
            if base == "e" and k == 0 and seg and seg == ("C", "x"):
                if seg2 and seg2[0] == "V":
                    fora += [("i", 0), ("z", 0)]
                else:
                    fora += [("ɐ", 0), ("j", 0), ("ʃ", 0)]
                salta.add(k + 1); continue
            fora.append(({"a": "ɐ", "e": "ɨ", "i": "i", "o": "u", "u": "u"}[base], 0)); continue
        # consoantes
        c = x[1]
        prox_v = seg and seg[0] == "V"
        frente = prox_v and seg[1] in "ei"
        if c in ("s", "z"):
            if c == "s" and k == 0:
                fora.append(("s", 0))
            elif prox_v and ant and (ant[0] == "V"):
                fora.append(("z", 0))
            elif prox_v:
                fora.append(("s" if c == "s" else "z", 0))
            elif fim:
                fora.append(("S", 0))
            else:
                fora.append(("ʒ" if _primeiro_som(u[k+1]) in _VOZEADAS else "ʃ", 0))
            continue
        if c == "x":
            if fim:
                fora += [("k", 0), ("s", 0)]
            else:
                fora.append(("ʃ", 0))
            continue
        if c == "r":
            fora.append(("ʁ" if k == 0 or (ant and ant[0] == "C" and ant[1] in ("n", "l", "s")) else "ɾ", 0))
            continue
        mapa = {"c": "s" if frente else "k", "g": "ʒ" if frente else "ɡ", "ç": "s", "ch": "ʃ", "lh": "ʎ",
                "nh": "ɲ", "rr": "ʁ", "ss": "s", "j": "ʒ", "q": "k", "k": "k", "w": "w", "ɡ": "ɡ"}
        fora.append((mapa.get(c, c), 0))
    return fora


def _primeiro_som(x):
    if x[0] == "V":
        return "a"
    return {"c": "k", "g": "ɡ", "ç": "s", "ch": "ʃ", "lh": "ʎ", "nh": "ɲ", "rr": "ʁ", "ss": "s",
            "j": "ʒ", "q": "k", "r": "ɾ"}.get(x[1], x[1])


def _normalizar(texto):
    texto = unicodedata.normalize("NFC", texto)
    texto = texto.translate(str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "«": '"', "»": '"',
                                           "–": "—", "―": "—", "[": "(", "]": ")"}))
    texto = re.sub(r"\.{3,}", "…", texto)
    texto = por_extenso(texto)
    return re.sub(r"\s+", " ", texto).strip()


def pecas(texto):
    """O texto em peças, como o front end do tiny-voca as pede: (True, pontuação) ou
    (False, [palavra, ...]), cada palavra uma lista de (fonema, acento 0/1)."""
    pedacos = []
    for parte in re.split(r"([,.?!;:\"'()—…])", _normalizar(texto)):
        if not parte.strip():
            continue
        if parte in PONTUACAO:
            pedacos.append((True, parte)); continue
        palavras = [w for w in re.split(r"[\s\-]+", parte.lower()) if re.search(r"[a-zà-ü]", w)]
        pedacos.append((False, [_palavra(re.sub(r"[^a-zà-üç]", "", w)) for w in palavras]))
    # «leste»: o verbo («já leste») é fechado; o ponto cardeal, depois de «a», «de», «do», «ao», «no», «para»,
    # «pelo», é aberto (20 Nov 2026: o modelo dizia «já léste» em vez de «já lêste»)
    _orto = [w for parte in re.split(r"([,.?!;:\"\x27()—…])", _normalizar(texto)) if parte.strip() and parte not in PONTUACAO
             for w in [re.sub(r"[^a-zà-üç]", "", x) for x in re.split(r"[\s\-]+", parte.lower()) if re.search(r"[a-zà-ü]", x)]]
    _seq = [(i, j) for i, (pont, v) in enumerate(pedacos) if not pont for j in range(len(v))]
    for n, (i, j) in enumerate(_seq):
        if n < len(_orto) and _orto[n] == "leste" and n > 0 and _orto[n - 1] in ("a", "de", "do", "ao", "no", "para", "pelo", "o"):
            pedacos[i][1][j] = [("ɛ", a) if (f == "e" and a) else (f, a) for f, a in pedacos[i][1][j]]
    # a sibilante final: z antes de vogal, ʒ antes de consoante vozeada, ʃ no resto
    sequencia = [(i, j) for i, (pont, v) in enumerate(pedacos) if not pont for j in range(len(v))]
    for n, (i, j) in enumerate(sequencia):
        palavra = pedacos[i][1][j]
        if not palavra or palavra[-1][0] != "S":
            continue
        seguinte = None
        if n + 1 < len(sequencia) and sequencia[n+1][0] == i:
            seguinte = pedacos[i][1][sequencia[n+1][1]][0][0] if pedacos[i][1][sequencia[n+1][1]] else None
        if seguinte is None:
            som = "ʃ"
        elif seguinte in VOGAIS or seguinte in ("j", "w"):
            som = "z"
        else:
            som = "ʒ" if seguinte in _VOZEADAS else "ʃ"
        palavra[-1] = (som, 0)
    return pedacos


def fonemas(texto):
    """O texto em fonemas, legível: palavras separadas por espaço, a tónica com ˈ."""
    fora = []
    for pont, v in pecas(texto):
        if pont:
            fora.append(v); continue
        for palavra in v:
            fora.append("".join(("ˈ" if a else "") + f for f, a in palavra))
    return " ".join(fora)
