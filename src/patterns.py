#!/usr/bin/env python3
"""Extract high-frequency German patterns from the Tatoeba corpus.

Selection criteria (METHODOLOGY.md D8 - no arbitrary thresholds):
  D8a t-score >= 2        collocation significance, Evert 2004 / Church et al. 1991
  D8b FUNCTION_WORDS      linguistically defined closed class, not a rank cutoff
  D8c NAME_BLOCKLIST      heuristic: tokens identified as corpus proper names by
                          manual review of top bundles (Tatoeba sentence factory)
  D8d exemplar window     interquartile range of corpus sentence lengths
  D8e frame floors        same t-score rule; O >= 10 for sparse-slot stability

Output: derived/patterns.csv, derived/pattern_stats.json
"""
import bz2, collections, csv, json, pathlib, re, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DERIVED = ROOT / "derived"
SRC = DATA / "deu_sentences_detailed.tsv.bz2"
TOKEN_RE = re.compile(r"[a-zA-Z\u00c4\u00d6\u00dc\u00e4\u00f6\u00fc\u00df']+")

TSCORE_MIN = 2.0
MIN_OBS_BUNDLE = 4
MIN_OBS_FRAME = 10
PRUNE_KEEP = 3
SAFETY_CAP = 5000
NGRAM_MAX = 5

FUNCTION_WORDS = set("""der die das ein eine einen einem einer eines des dem den
ich du er sie es wir ihr mich dich sich uns euch mir dir ihm ihnen mein meine
meinen meinem meiner dein deine deinen sein seine seinen seinem ihrer eure
habe hab hast hat habt bin bist sind seid war warst waren hatte hattest hatten
bin worden wurde wurden werden würde würdest würden soll sollte sollst muss
musst muß musste können könnt kann kannst darf darfst dürfte will willst
wollte wollt möchte möcht nicht ja nein doch mal halt eben wohl denn bitte
danke ja doch in an auf mit von zu bei nach aus vor um für über unter
zwischen gegen ohne bis seit während wegen trotz laut gegenüber entlang ab
und oder aber sondern weil dass ob wenn als bevor nachdem obwohl damit
deshalb deswegen trotzdem außerdem dennoch also dann jedoch hier dort jetzt
heute morgen gestern immer nie nie oft manchmal schon noch auch nur sehr ganz
so wie was wer wo wann warum wieviel man kein keine keinen manche viel viele
wenig wenigen etwas nichts alles alle aller allem allen andere anderen""".split())

NAME_BLOCKLIST = set("""tom maria mary john johannes ken bob alice mr mrs
svetlana tanin yuri ivan anna lisa peter paul heinz klaus""".split())

AUX = {"habe","hab","hast","hat","habt","bin","bist","ist","sind","seid",
       "war","warst","waren","hatte","hattest","hatten"}
MODALS = {"muss","musst","muß","kann","kannst","will","willst","möchte","möcht",
          "möchten","soll","sollst","sollt","darf","darfst","könnte","wollte",
          "musste","sollte","konnten","wollen","müssen","können","dürfen","sollen"}
SEP_PREFIX = {"an","auf","aus","ein","mit","vor","zu","ab","nach","zurück","los",
              "fest","weg","her","hin","zusammen","statt","fern","entgegen",
              "dran","rauf","runter","rein","raus"}
IRREG_PTCP = {"gegangen","gesehen","gesagt","gekommen","genommen","gegeben",
              "geschrieben","gelesen","getan","gefunden","gewusst","gewußt",
              "gebracht","gedacht","geworden","geblieben","gefahren","gelaufen",
              "gesessen","gestanden","gelegen","vergessen","verstanden","gewesen"}
NOT_PTCP = {"nicht","gut","aber","doch","mal","sehr","noch","schon","auch",
            "hier","dort","jetzt","heute","morgen","gestern","immer","wieder",
            "vielleicht","wirklich","leider","zusammen","fertig","wichtig",
            "lieber","genau","sicher","einfach","endlich","schlecht","recht",
            "ganz","bald","kaum","nur","halt","denn","bitte","danke","viel",
            "wenig","gerade","gleich","sonst","damit","deshalb","kurz","spät"}
DETS = {"eine","einen","einem","einer","ein","den","die","das","dem","der",
        "meine","mein","keine","kein","seine","ihre","deine"}
LIGHT_STEMS = ("treff","nehm","geb","mach","bring","stell","setz","führ",
               "zieh","druck","fall","halt","leist","teiln")
PARTICLES = {"ja","doch","mal","halt","eben","wohl","denn","schon","noch"}
CONNECTORS = {"weil","dass","obwohl","deshalb","deswegen","trotzdem","außerdem",
              "dennoch","aber","also","dann","damit","wenn","als","denn"}
MAL_NOUN_PREV = {"erste","ersten","erster","erstes","letzte","letzten","letztes",
                 "jede","jeden","jedes","manche","manchen","einmal","zweite"}
ROUTINES = ["es tut mir leid","wie geht es dir","mir geht es gut","vielen dank",
            "danke schön","bis bald","bis später","bis morgen","bis dann",
            "keine ahnung","ich muss los","ich weiß es nicht","ich weiß nicht",
            "was ist los","mir ist kalt","mir ist heiß","ich habe hunger",
            "ich habe durst","nicht wahr","meiner meinung nach","gute besserung",
            "viel glück","viel spaß","alles gute","herzlichen glückwunsch",
            "in ordnung","stimmt genau","ach so","na ja","gute nacht",
            "guten morgen","guten tag","guten abend","auf wiedersehen",
            "entschuldigung","bitte schön","gern geschehen","kein problem",
            "machs gut","pass auf dich auf","was ist mit dir","wie bitte",
            "ich habe keine zeit","später vielleicht","natürlich nicht",
            "ich bin müde"]


def toks_raw(text):
    return TOKEN_RE.findall(text)


def toks(text):
    out = []
    for m in toks_raw(text):
        w = m.lower().strip("'")
        if w:
            out.append(w)
    return out


def main():
    t0 = time.time()

    # ---------------- pass 1: unigrams, n-grams, capitalization, lengths ----
    uni = collections.Counter()
    grams = {n: collections.Counter() for n in range(2, NGRAM_MAX + 1)}
    cap_mid = collections.Counter()   # mid-sentence capitalized occurrences
    lengths = []
    n_sent = 0
    with bz2.open(SRC, "rt", encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3 or parts[1] != "deu":
                continue
            raw = toks_raw(parts[2])
            tk = [m.lower().strip("'") for m in raw]
            tk = [w for w in tk if w]
            if not tk:
                continue
            n_sent += 1
            lengths.append(len(tk))
            for i, m in enumerate(raw):
                w = m.lower().strip("'")
                if not w:
                    continue
                uni[w] += 1
                if i > 0 and m[:1].isupper():
                    cap_mid[w] += 1
            for n in range(2, NGRAM_MAX + 1):
                c = grams[n]
                for i in range(len(tk) - n + 1):
                    c[tuple(tk[i:i + n])] += 1
            if n_sent % 150_000 == 0:
                for n in range(3, NGRAM_MAX + 1):
                    g = grams[n]
                    for k in [k for k, v in g.items() if v < PRUNE_KEEP]:
                        del g[k]
    total = sum(uni.values())
    lengths.sort()
    q1 = lengths[len(lengths) // 4]
    q3 = lengths[(3 * len(lengths)) // 4]
    print(f"pass1: {n_sent} sents, {total} tokens, IQR length [{q1},{q3}], "
          f"{int(time.time()-t0)}s", flush=True)

    def proper_noun(w):
        return cap_mid[w] >= 50 and cap_mid[w] / uni[w] > 0.8

    def tscore(obs, expected):
        return (obs - expected) / (obs ** 0.5)

    # ---------------- bundle candidates: t-score criterion (D8a) ------------
    rows = []
    per_n_stats = {}
    for n in range(2, NGRAM_MAX + 1):
        passed = 0
        scored = []
        for k, obs in grams[n].items():
            if obs < MIN_OBS_BUNDLE:
                continue
            if any(w in NAME_BLOCKLIST for w in k):
                continue
            if all(w in FUNCTION_WORDS for w in k):
                continue
            exp = 1.0
            for w in k:
                exp *= uni[w] / total
            exp *= total
            if obs <= exp:
                continue
            if tscore(obs, exp) < TSCORE_MIN:
                continue
            scored.append((tscore(obs, exp), obs, k))
            passed += 1
        scored.sort(reverse=True)
        scored = scored[:SAFETY_CAP]
        per_n_stats[n] = {"passed_tscore": passed, "kept_after_cap": len(scored)}
        for tsc, obs, k in scored:
            rows.append((tsc, obs, n, k))
        grams[n] = None
        print(f"  n={n}: {passed} pass t-score, kept {len(scored)}", flush=True)

    # ---------------- subsumption: structural, longest-first ----------------
    rows.sort(key=lambda x: (-len(x[3]), -x[1]))
    kept = []
    kept_strs = []
    for tsc, obs, n, k in rows:
        s = " ".join(k)
        if any(s in ks for ks in kept_strs):
            continue
        kept.append((tsc, obs, k))
        kept_strs.append(s)
    print(f"bundles after subsumption: {len(kept)}", int(time.time()-t0), "s", flush=True)

    # ---------------- pass 2: exemplars + frame mining ----------------------
    big_index = collections.defaultdict(list)
    for idx, (tsc, obs, k) in enumerate(kept):
        big_index[k[0], k[1]].append(idx)
    for r in ROUTINES:
        tk = toks(r)
        if len(tk) >= 2:
            big_index[tk[0], tk[1]].append(("R", r))

    frame_counts = collections.Counter()
    frame_ex = collections.defaultdict(list)
    fv_counts = collections.Counter()
    fv_ex = collections.defaultdict(list)
    bundle_ex = collections.defaultdict(list)
    routine_counts = collections.Counter()
    routine_ex = collections.defaultdict(list)

    def participle_like(t):
        if t in NOT_PTCP or t in AUX or t in MODALS or t in FUNCTION_WORDS:
            return False
        return (t.startswith("ge") and len(t) >= 6) or t in IRREG_PTCP or \
               (t.endswith("t") and len(t) >= 5)

    n_sent = 0
    with bz2.open(SRC, "rt", encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3 or parts[1] != "deu":
                continue
            sid, text = parts[0], parts[2]
            tk = toks(text)
            n_sent += 1
            if not (q1 <= len(tk) <= q3):          # D8d exemplar window
                continue
            joined = " " + " ".join(tk) + " "
            for i in range(len(tk) - 1):
                for entry in big_index.get((tk[i], tk[i + 1]), ()):
                    if isinstance(entry, tuple):
                        r = entry[1]
                        if " " + r + " " in joined:
                            routine_counts[r] += 1
                            if len(routine_ex[r]) < 4:
                                routine_ex[r].append((len(tk), sid))
                    else:
                        idx = entry
                        s = " ".join(kept[idx][2])
                        if " " + s + " " in joined and len(bundle_ex[idx]) < 4:
                            bundle_ex[idx].append((len(tk), sid))
            # Perfekt frames
            for i, t in enumerate(tk):
                if t in AUX:
                    for j in range(i + 1, min(i + 7, len(tk))):
                        if participle_like(tk[j]):
                            key = t + " \u2026 " + tk[j]
                            frame_counts[key] += 1
                            if len(frame_ex[key]) < 3:
                                frame_ex[key].append((len(tk), sid))
                            break
                    break
            # separable-verb frames
            if len(tk) >= 3 and tk[-1] in SEP_PREFIX:
                for t in tk[:3]:
                    if t not in FUNCTION_WORDS and t not in AUX and \
                       (t.endswith("e") or t.endswith("st") or t.endswith("t")
                        or t.endswith("en")) and uni[t] >= 50:
                        key = t + " \u2026 " + tk[-1]
                        frame_counts[key] += 1
                        if len(frame_ex[key]) < 3:
                            frame_ex[key].append((len(tk), sid))
                        break
            # modal + infinitive-final frames
            for i, t in enumerate(tk):
                if t in MODALS:
                    last = tk[-1]
                    if last.endswith("en") and len(last) >= 6 and \
                       last not in FUNCTION_WORDS and last not in AUX and last not in MODALS:
                        key = t + " \u2026 " + last
                        frame_counts[key] += 1
                        if len(frame_ex[key]) < 3:
                            frame_ex[key].append((len(tk), sid))
                    break
            # Funktionsverbgefüge: det (adj) noun + light verb, mined in situ
            for i in range(len(tk) - 2):
                if tk[i] in DETS and tk[i + 2].startswith(LIGHT_STEMS) and \
                   tk[i + 2] not in FUNCTION_WORDS and 5 <= len(tk[i + 2]) <= 9 and \
                   not tk[i + 2].startswith("ge") and \
                   tk[i + 1] not in FUNCTION_WORDS and len(tk[i + 1]) >= 4:
                    key = " ".join(tk[i:i + 3])
                    fv_counts[key] += 1
                    if len(fv_ex[key]) < 3:
                        fv_ex[key].append((len(tk), sid))
                if i + 3 < len(tk) and tk[i] in DETS and \
                   tk[i + 3].startswith(LIGHT_STEMS) and tk[i + 3] not in FUNCTION_WORDS and \
                   not tk[i + 3].startswith("ge") and len(tk[i + 3]) <= 9 and \
                   tk[i + 1] not in FUNCTION_WORDS and tk[i + 2] not in FUNCTION_WORDS:
                    key = " ".join(tk[i:i + 4])
                    fv_counts[key] += 1
                    if len(fv_ex[key]) < 3:
                        fv_ex[key].append((len(tk), sid))
            if n_sent % 200_000 == 0:
                print("  pass2", n_sent, int(time.time()-t0), "s", flush=True)
    print("pass2 done", int(time.time()-t0), "s", flush=True)

    # ---------------- frame significance (D8e) ------------------------------
    def frame_passes(obs, words):
        exp = 1.0
        for w in words:
            exp *= uni[w] / total
        exp *= n_sent
        return obs >= MIN_OBS_FRAME and obs > exp and tscore(obs, exp) >= TSCORE_MIN

    # ---------------- assemble ----------------------------------------------
    def classify(k):
        for i, w in enumerate(k):
            if w == "mal" and i > 0 and k[i - 1] in MAL_NOUN_PREV:
                return "lexical_bundle"
        if any(w in PARTICLES for w in k) and len(k) >= 3:
            return "particle_frame"
        if any(w in CONNECTORS for w in k):
            return "connector_bundle"
        return "lexical_bundle"

    out_rows = []
    for idx, (tsc, obs, k) in enumerate(kept):
        ex = sorted(bundle_ex.get(idx, []))
        out_rows.append({"class": classify(k), "pattern": " ".join(k),
                         "count": obs, "tscore": round(tsc, 2), "kind": "bundle",
                         "n": len(k),
                         "examples": ";".join(sid for _, sid in ex[:3])})
    for key, obs in frame_counts.items():
        if " \u2026 " not in key:
            continue
        a, b = key.split(" \u2026 ")
        if not frame_passes(obs, [a, b]):
            continue
        cls = ("perfekt_frame" if a in AUX else
               "modal_frame" if a in MODALS else "separable_frame")
        ex = sorted(frame_ex.get(key, []))
        exp = uni[a] * uni[b] / total
        out_rows.append({"class": cls, "pattern": key, "count": obs,
                         "tscore": round((obs - exp) / obs ** 0.5, 2),
                         "kind": "frame", "n": 0,
                         "examples": ";".join(sid for _, sid in ex[:3])})
    for key, obs in fv_counts.items():
        k = key.split()
        if not frame_passes(obs, k):
            continue
        ex = sorted(fv_ex.get(key, []))
        out_rows.append({"class": "funkverbgefüge", "pattern": key, "count": obs,
                         "tscore": 0.0, "kind": "frame", "n": 0,
                         "examples": ";".join(sid for _, sid in ex[:3])})
    for r in ROUTINES:
        ex = sorted(routine_ex.get(r, []))
        out_rows.append({"class": "routine", "pattern": r,
                         "count": routine_counts.get(r, 0), "tscore": 0.0,
                         "kind": "routine", "n": 0,
                         "examples": ";".join(sid for _, sid in ex[:3])})

    DERIVED.mkdir(exist_ok=True)
    order = {"routine": 0, "perfekt_frame": 1, "separable_frame": 2,
             "modal_frame": 3, "funkverbgefüge": 4, "particle_frame": 5,
             "connector_bundle": 6, "lexical_bundle": 7}
    out_rows.sort(key=lambda r: (order.get(r["class"], 9), -r["count"]))
    with open(DERIVED / "patterns.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["class", "pattern", "count", "tscore",
                                           "kind", "n", "examples"])
        w.writeheader()
        w.writerows(out_rows)

    stats = {
        "sentences": n_sent, "tokens": total, "length_iqr": [q1, q3],
        "criteria": {"tscore_min": TSCORE_MIN, "min_obs_bundle": MIN_OBS_BUNDLE,
                     "min_obs_frame": MIN_OBS_FRAME,
                     "function_words": len(FUNCTION_WORDS),
                     "name_blocklist": sorted(NAME_BLOCKLIST)},
        "per_n": per_n_stats,
        "totals": dict(collections.Counter(r["class"] for r in out_rows)),
        "top_by_class": {c: [r["pattern"] for r in out_rows if r["class"] == c][:8]
                         for c in order},
    }
    (DERIVED / "pattern_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2))
    print(json.dumps(stats["totals"], ensure_ascii=False))
    print("done", int(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    main()
