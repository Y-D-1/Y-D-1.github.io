#!/usr/bin/env python3
"""Rebuild fa.json from Functional Analysis homework *o.tex files."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_TEX_DIR = Path.home() / "Desktop/Latex/2025Autumn/Functional-Analysis/homework"
OUT = REPO / "Problem/banks/fa.json"

# --- parser (from math-bank/app/latex_parser.py) ---


def _extract_braced(text: str, start: int) -> tuple[str, int] | None:
    if start >= len(text) or text[start] != "{":
        return None
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i], i + 1
    return None


def _find_one_arg(text: str, macro: str, pos: int = 0) -> tuple[str, int] | None:
    needle = f"\\{macro}{{"
    idx = text.find(needle, pos)
    if idx == -1:
        return None
    cursor = idx + len(needle) - 1
    extracted = _extract_braced(text, cursor)
    if extracted is None:
        return None
    return extracted[0].strip(), extracted[1]


def _find_two_arg(text: str, macro: str, pos: int = 0) -> tuple[str, str, int] | None:
    needle = f"\\{macro}{{"
    idx = text.find(needle, pos)
    if idx == -1:
        return None
    cursor = idx + len(needle) - 1
    first = _extract_braced(text, cursor)
    if first is None:
        return None
    arg1, cursor = first
    second = _extract_braced(text, cursor)
    if second is None:
        return None
    arg2, cursor = second
    return arg1.strip(), arg2.strip(), cursor


def parse_o_tex(content: str) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    chapter = ""
    pos = 0

    while pos < len(content):
        sec_idx = content.find("\\sectionn{", pos)
        ex_idx = content.find("\\ex{", pos)
        if sec_idx == -1 and ex_idx == -1:
            break
        if sec_idx != -1 and (ex_idx == -1 or sec_idx < ex_idx):
            found = _find_one_arg(content, "sectionn", sec_idx)
            if found is None:
                break
            chapter, pos = found
            continue
        found = _find_two_arg(content, "ex", ex_idx)
        if found is None:
            break
        _title, stem, pos = found
        items.append((chapter, stem))
    return items


# --- LaTeX normalization for MathJax ---

MACRO_REPLACEMENTS = [
    (r"\\rd\b", r"\\mathrm{d}"),
    (r"\\mcB\b", r"\\mathcal{B}"),
    (r"\\mcL\b", r"\\mathcal{L}"),
    (r"\\bbK\b", r"\\mathbb{K}"),
    (r"\\bbR\b", r"\\mathbb{R}"),
    (r"\\bbN\b", r"\\mathbb{N}"),
    (r"\\mathcal\s+B\b", r"\\mathcal{B}"),
    (r"\\mathcal\s+L\b", r"\\mathcal{L}"),
    (r"\\mathbf1\b", r"\\mathbf{1}"),
    (r"\\id_E\b", r"I_E"),
    (r"\\id\b", r"\\mathrm{id}"),
    (r"\\Ker\b", r"\\ker"),
    (r"\\mathrm\s+\\mathrm\s+e\b", r"\\mathrm{e}"),
    (r"\\mathrm\s+e\b", r"\\mathrm{e}"),
    (r"\\overset\{\\delta\}\{\\to\}", r"\\xrightarrow{\\delta}"),
    (r"\\mathrm\s*\{\s*e\s*\}\s*\^\*", r"E^*"),
    (r"\\mathrm\s*\{\s*e\s*\}\s*\\\^\\perp", r"E^\\perp"),
    (r"\\mathrm\s*\{\s*e\s*\}\s*\^\\perp", r"E^\\perp"),
    (r"\\spn\b", r"\\operatorname{span}"),
    (r"\\innerp\{([^}]*)\}\{([^}]*)\}", r"\\langle \\1, \\2 \\rangle"),
]

REF_PHRASES = [
    r"并利用题中函数列证明二者不等价\.?",
    r"题中函数列",
    r"如上(?:所述|构造)?",
    r"同上",
    r"上一题",
    r"见上(?:一)?题",
    r"如前(?:所述|证明)?",
]


def normalize_tex(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"\\\[", "$$", text)
    text = re.sub(r"\\\]", "$$", text)
    text = re.sub(r"\\\((.+?)\\\)", r"$\1$", text, flags=re.DOTALL)
    text = re.sub(r"\$\s*\n\s*\$", " ", text)
    for pat, repl in MACRO_REPLACEMENTS:
        text = re.sub(pat, repl, text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_ref_phrases(text: str) -> str:
    for pat in REF_PHRASES:
        text = re.sub(pat, "", text)
    return re.sub(r"\s+", " ", text).strip(" ，,;；.")


def parse_list_env(body: str, env: str) -> list[str]:
    begin = rf"\\begin\{{{env}\}}(?:\[[^\]]*\])?"
    end = rf"\\end\{{{env}\}}"
    m = re.search(begin + r"(.*?)" + end, body, flags=re.DOTALL)
    if not m:
        return []
    content = m.group(1)
    parts = re.split(r"\\item(?:\[[^\]]*\])?\s*", content)
    items = [normalize_tex(p) for p in parts if p.strip()]
    return [strip_ref_phrases(i) for i in items if strip_ref_phrases(i)]


def split_stem(stem: str) -> tuple[str, list[str], str]:
    stem = normalize_tex(stem)
    for env in ("enumerate", "itemize"):
        begin = rf"\\begin\{{{env}\}}"
        m = re.search(begin, stem)
        if not m:
            continue
        head = normalize_tex(stem[: m.start()])
        tail = normalize_tex(stem[m.end() + len(env) + len("\\end{}") :])
        # fix tail extraction
        end_tag = f"\\end{{{env}}}"
        end_idx = stem.find(end_tag, m.start())
        if end_idx == -1:
            continue
        body = stem[m.end() : end_idx]
        tail = normalize_tex(stem[end_idx + len(end_tag) :])
        items = parse_list_env(f"\\begin{{{env}}}{body}\\end{{{env}}}", env)
        return strip_ref_phrases(head), items, strip_ref_phrases(tail)
    return strip_ref_phrases(stem), [], ""


def difficulty_from_file(stem_name: str) -> int:
    m = re.match(r"(\d+)o", stem_name)
    if not m:
        return 3
    n = int(m.group(1))
    if n <= 1:
        return 1
    if n <= 3:
        return 2
    if n <= 6:
        return 3
    if n <= 9:
        return 4
    return 5


def build_problem(set_id: str, index: int, stem_raw: str) -> dict:
    question, subquestions, tail = split_stem(stem_raw)
    if tail:
        if subquestions:
            subquestions[-1] = strip_ref_phrases(subquestions[-1] + " " + tail)
        else:
            question = strip_ref_phrases(question + " " + tail)

    # Manual expansions for self-contained statements
    if "N_1" in question and "N_2" in question and subquestions:
        for i, sq in enumerate(subquestions):
            if "函数列" in sq or "不等价" in sq and "f_n" not in sq:
                subquestions[i] = (
                    "考虑函数列 $f_n(x)=1-nx$（$x\\in[0,n^{-1}]$）且 $f_n(x)=0$（$x\\in[n^{-1},1]$），"
                    "证明 $N_1$ 与 $N_2$ 不等价."
                )

    prob: dict = {
        "id": f"fa-all-{set_id}-{index:02d}",
        "difficulty": difficulty_from_file(set_id),
        "question": question or "（请阅读各小问）",
    }
    if subquestions:
        prob["subquestions"] = subquestions
    return prob


def main() -> None:
    tex_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TEX_DIR
    if not tex_dir.is_dir():
        print(f"Tex directory not found: {tex_dir}", file=sys.stderr)
        sys.exit(1)

    problems: list[dict] = []
    for tex_path in sorted(tex_dir.glob("*o.tex")):
        set_id = tex_path.stem.replace("o", "")
        parsed = parse_o_tex(tex_path.read_text(encoding="utf-8"))
        for idx, (_chapter, stem) in enumerate(parsed, start=1):
            problems.append(build_problem(set_id, idx, stem))

    OUT.write_text(
        json.dumps({"problems": problems}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(problems)} problems to {OUT}")


if __name__ == "__main__":
    main()
