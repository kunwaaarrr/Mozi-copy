#!/usr/bin/env python3
"""Split the two raw transcript files into per-transcript markdown files under
mozi-copy/sources/, collapsing whisper hallucination loops (consecutive
repeated sentences) and marking probable content gaps."""
import re
import os
import unicodedata

RAW_GL = "/root/.claude/uploads/088171ad-d166-5ba6-85f4-a69050c87ecb/d95b8ff2-ALLTRANSCRIPTS.txt"
RAW_YT = "/root/.claude/uploads/088171ad-d166-5ba6-85f4-a69050c87ecb/73b21c83-youtubetranscripts.txt"
OUT = "/home/user/Mozi-copy/mozi-copy/sources"

GAP = "\n> **[TRANSCRIPTION GAP — a transcription-error loop was collapsed here; some original speech was lost and must not be invented.]**\n"

SENT_SPLIT = re.compile(r'(?<=[.!?])\s+')

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower()
    return re.sub(r'[^a-z0-9 ]', '', s).strip()

def collapse_clauses(sent: str):
    """Collapse comma-joined repeated clauses inside one sentence."""
    clauses = sent.split(", ")
    if len(clauses) < 3:
        return sent, 0
    out, i, collapsed = [], 0, 0
    while i < len(clauses):
        j = i
        key = norm(clauses[i])
        while j + 1 < len(clauses) and norm(clauses[j + 1]) == key and key:
            j += 1
        run = j - i + 1
        out.append(clauses[i])
        if run >= 2:
            collapsed += 1
            if run >= 5:
                out.append("[[GAPMARK]]")
        i = j + 1
    return ", ".join(out), collapsed

def collapse_loops(text: str):
    """Collapse runs of >=3 identical consecutive sentences. Insert GAP when run >=5."""
    sents = SENT_SPLIT.split(text)
    new_sents, intra = [], 0
    for s in sents:
        s2, c = collapse_clauses(s)
        intra += c
        new_sents.append(s2)
    sents = new_sents
    out = []
    i = 0
    n_collapsed = 0
    while i < len(sents):
        j = i
        key = norm(sents[i])
        while j + 1 < len(sents) and norm(sents[j + 1]) == key and key:
            j += 1
        run = j - i + 1
        out.append(sents[i])
        if run >= 3:
            n_collapsed += 1
            if run >= 5:
                out.append("\n" + GAP.strip() + "\n")
        elif run == 2:
            out.append(sents[i + 1])
        i = j + 1
    joined = " ".join(out)
    joined = joined.replace(", [[GAPMARK]],", ".\n" + GAP.strip() + "\n").replace("[[GAPMARK]]", "\n" + GAP.strip() + "\n")
    return joined, n_collapsed + intra

def clean_paragraphs(body: str):
    # join transcript lines into paragraphs (raw files have one long line per chunk)
    lines = [l.strip() for l in body.split("\n") if l.strip()]
    text = " ".join(lines)
    text, n = collapse_loops(text)
    # re-wrap into readable paragraphs of ~5 sentences
    sents = SENT_SPLIT.split(text)
    paras, cur = [], []
    for s in sents:
        if s.strip().startswith("> **[TRANSCRIPTION GAP"):
            if cur:
                paras.append(" ".join(cur)); cur = []
            paras.append(s.strip())
            continue
        cur.append(s)
        if len(cur) >= 5:
            paras.append(" ".join(cur)); cur = []
    if cur:
        paras.append(" ".join(cur))
    return "\n\n".join(paras), n

FIXES = [
    (re.compile(r'\bJim ?Lodge\b', re.I), "Gym Launch"),
    (re.compile(r'\bJim ?lunch\b', re.I), "Gym Launch"),
    (re.compile(r'\bJim Winters\b'), "Gym Launchers"),
    (re.compile(r'\bJim Warner is\b'), "Gym Launchers,"),
    (re.compile(r'\boverhomes\b', re.I), "overcomes"),
    (re.compile(r'\bstall clothes\b', re.I), "stall closes"),
    (re.compile(r'\bmoney clothes\b', re.I), "money closes"),
    (re.compile(r'\bunicorn clothes\b', re.I), "unicorn close"),
    (re.compile(r'\bspouse clothes\b', re.I), "spouse closes"),
    (re.compile(r'\bthe clothes\b(?= only work| that| are just| on top)'), "the closes"),
    (re.compile(r'\bOxramozy\b', re.I), "Alex Hormozi"),
]

def apply_fixes(text: str) -> str:
    for pat, rep in FIXES:
        text = pat.sub(rep, text)
    return text

def slug(s: str) -> str:
    s = re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-').lower()
    return re.sub(r'-+', '-', s)[:60]

def split_gym_launch():
    raw = open(RAW_GL).read()
    blocks = re.findall(
        r'===== TRANSCRIPT (\d+)/30 =====\n(.*?)\n===== END TRANSCRIPT \1 =====',
        raw, re.S)
    os.makedirs(f"{OUT}/gym-launch", exist_ok=True)
    report = []
    for num, block in blocks:
        meta, body = block.split("-----", 1)
        fields = dict(re.findall(r'^(Section|Module|Title): (.+)$', meta, re.M))
        body_clean, ngaps = clean_paragraphs(body)
        body_clean = apply_fixes(body_clean)
        fname = f"{int(num):02d}-{slug(fields['Title'])}.md"
        with open(f"{OUT}/gym-launch/{fname}", "w") as f:
            f.write(f"# {fields['Title']}\n\n")
            f.write(f"- **Source:** Gym Launch 2.0 course, transcript {num}/30\n")
            f.write(f"- **Section:** {fields['Section']}\n")
            f.write(f"- **Module:** {fields['Module']}\n")
            f.write(f"- **Cleaning:** whisper small.en transcript; loop artifacts collapsed: {ngaps}\n\n---\n\n")
            f.write(body_clean + "\n")
        report.append((f"gym-launch/{fname}", ngaps))
    return report

def split_youtube():
    raw = open(RAW_YT).read()
    parts = re.split(r'={60}\nVIDEO (\d+): (.+)\nURL: (.+)\n={60}\n', raw)
    # parts: [preamble, num, title, url, body, num, title, url, body, ...]
    os.makedirs(f"{OUT}/youtube", exist_ok=True)
    report = []
    for i in range(1, len(parts), 4):
        num, title, url, body = parts[i], parts[i+1], parts[i+2], parts[i+3]
        body_clean, ngaps = clean_paragraphs(body)
        body_clean = apply_fixes(body_clean)
        fname = f"{int(num):02d}-{slug(title)}.md"
        with open(f"{OUT}/youtube/{fname}", "w") as f:
            f.write(f"# {title}\n\n")
            f.write(f"- **Source:** YouTube video {num}/6 — {url}\n")
            f.write(f"- **Cleaning:** whisper large-v3-turbo transcript; loop artifacts collapsed: {ngaps}\n\n---\n\n")
            f.write(body_clean + "\n")
        report.append((f"youtube/{fname}", ngaps))
    return report

if __name__ == "__main__":
    r1 = split_gym_launch()
    r2 = split_youtube()
    for name, n in r1 + r2:
        print(f"{n:4d} loops collapsed  {name}")
