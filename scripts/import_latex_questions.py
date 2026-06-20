#!/usr/bin/env python3
"""Import homework LaTeX files into practice questions.json."""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MACRO_PATH = Path(__file__).with_name("latex_macros.json")
PENDING_SOLUTION = "待补充解答"

SUBJECT_SOURCES: dict[str, list[Path]] = {
    "微分几何": [
        Path("/Users/yudongyi/Desktop/Latex/2025Autumn/Differential-Geometry/homework"),
        Path("/Users/yudongyi/Desktop/Latex/2025Spring/Manifold/mani_homework"),
    ],
    "泛函分析": [
        Path("/Users/yudongyi/Desktop/Latex/2025Autumn/Functional-Analysis/homework"),
    ],
}

SKIP_FILES = {
    "no.tex",
    "collection.tex",
    "all.tex",
    "manifold_homework_problems.tex",
    "1-1-problems-1-4.tex",
    "major-assignment.tex",
}

SKIP_SUFFIXES = ("o.tex",)

ENV_PATTERN = re.compile(
    r"\\begin\{(?P<name>figure|tikzpicture|algorithm|algorithm2e|comment)\*?\}.*?\\end\{(?P=name)\*?\}",
    re.DOTALL,
)
SECTION_PATTERN = re.compile(r"\\section\*?\{([^{}]*)\}")
SUBSECTION_PATTERN = re.compile(r"\\subsection\*?\{([^{}]*)\}")
LABEL_PATTERN = re.compile(r"\\label\{([^}]+)\}")
QUESTION_CMD_PATTERN = re.compile(r"\\(?:qs|Qs|ex)\*?\{")
PROP_PATTERN = re.compile(r"\\mprop\*?\{")
THEOREM_PATTERN = re.compile(r"\\thm\*?\{")
REF_PATTERN = re.compile(r"\\ref(?:eq)?\{([^}]+)\}")
DING_PATTERN = re.compile(r"\\ding\{(\d+)\}")
DING_MAP = {172: "①", 173: "②", 174: "③", 175: "④", 176: "⑤", 177: "⑥"}


@dataclass
class ParsedBlock:
    kind: str
    title: str
    body: str
    label: str | None = None
    source_file: str = ""
    number: str = ""
    solution: str = ""


@dataclass
class ImportState:
    macros: dict[str, str] = field(default_factory=dict)
    label_db: dict[str, str] = field(default_factory=dict)
    questions: list[dict[str, Any]] = field(default_factory=list)


def load_macros() -> dict[str, str]:
    with MACRO_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def strip_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("%"):
            continue
        lines.append(re.sub(r"(?<!\\)%.*$", "", line))
    return "\n".join(lines)


def extract_braced(text: str, start: int) -> tuple[str, int]:
    if start >= len(text) or text[start] != "{":
        raise ValueError("expected opening brace")
    depth = 0
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i], i + 1
        elif ch == "\\" and i + 1 < len(text):
            i += 1
        i += 1
    raise ValueError("unbalanced braces")


def remove_environments(text: str) -> str:
    previous = None
    current = text
    while previous != current:
        previous = current
        current = ENV_PATTERN.sub("[图示略]", current)
    return current


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\\\s*\n", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


def apply_macros(text: str, macros: dict[str, str]) -> str:
    for command, replacement in sorted(macros.items(), key=lambda item: len(item[0]), reverse=True):
        pattern = re.compile(re.escape(command) + r"(?![A-Za-z])")
        text = pattern.sub(lambda _match, repl=replacement: repl, text)
    text = re.sub(
        r"\\pp\{([^{}]+)\}\{([^{}]+)\}",
        lambda m: rf"\frac{{\partial {m.group(1)}}}{{\partial {m.group(2)}}}",
        text,
    )
    text = re.sub(
        r"\\dpp\{([^{}]+)\}\{([^{}]+)\}",
        lambda m: rf"\dfrac{{\partial {m.group(1)}}}{{\partial {m.group(2)}}}",
        text,
    )
    text = re.sub(
        r"\\ddd\{([^{}]+)\}\{([^{}]+)\}",
        lambda m: rf"\frac{{\mathrm{{d}} {m.group(1)}}}{{\mathrm{{d}} {m.group(2)}}}",
        text,
    )
    text = re.sub(r"\\rdd\{([^{}]+)\}", lambda m: rf"\dfrac{{\mathrm{{d}}}}{{\mathrm{{d}} {m.group(1)}}}", text)
    text = re.sub(r"\\mc([A-Z])\b", r"\\mathcal{\1}", text)
    text = re.sub(r"\\s([A-Z])\b", r"\\mathscr{\1}", text)
    text = re.sub(r"\\bb([A-Z])\b", r"\\mathbb{\1}", text)
    text = re.sub(r"\\RR\b", r"\\mathbb{R}", text)
    text = re.sub(r"\\NN\b", r"\\mathbb{N}", text)
    text = re.sub(r"\\ZZ\b", r"\\mathbb{Z}", text)
    text = re.sub(r"\\QQ\b", r"\\mathbb{Q}", text)
    text = re.sub(r"\\CC\b", r"\\mathbb{C}", text)
    text = re.sub(r"\\mathbbm\{1\}", r"\\mathbb{1}", text)
    text = re.sub(r"\\overset\{([^}]*)\}\{\\to\}", r"\\xrightarrow{\1}", text)
    text = re.sub(r"\\overset\{([^}]*)\}\{\\rightarrow\}", r"\\xrightarrow{\1}", text)
    return text


def convert_lists(text: str) -> str:
    def convert_block(match: re.Match[str]) -> str:
        env = match.group("env")
        body = match.group("body")
        ordered = env.startswith("enumerate")
        items = re.split(r"\\item(?:\[[^\]]*\])?", body)
        items = [item.strip() for item in items if item.strip()]
        lines: list[str] = []
        for index, item in enumerate(items, start=1):
            prefix = f"{index}. " if ordered else "- "
            lines.append(prefix + item)
        return "\n".join(lines)

    list_pattern = re.compile(
        r"\\begin\{(?P<env>enumerate\*?|itemize\*?)(?:\[[^\]]*\])?\}(?P<body>.*?)\\end\{(?P=env)\}",
        re.DOTALL,
    )
    previous = None
    current = text
    while previous != current:
        previous = current
        current = list_pattern.sub(convert_block, current)
    return current


def convert_math_environments(text: str) -> str:
    replacements = [
        ("equation*", "equation"),
        ("align*", "aligned"),
        ("alignat*", "aligned"),
        ("gather*", "gathered"),
        ("cases", "cases"),
        ("matrix", "matrix"),
        ("pmatrix", "pmatrix"),
        ("bmatrix", "bmatrix"),
        ("vmatrix", "vmatrix"),
    ]
    for env, inner in replacements:
        pattern = re.compile(rf"\\begin\{{{env}\*?\}}(.*?)\\end\{{{env}\*?\}}", re.DOTALL)
        if env in {"equation", "equation*"}:
            text = pattern.sub(lambda m: f"\n\\[{m.group(1).strip()}\\]\n", text)
        elif env.endswith("matrix") or env == "cases":
            text = pattern.sub(lambda m, inner=inner: f"\n\\[\n\\begin{{{inner}}}{m.group(1).strip()}\\end{{{inner}}}\n\\]\n", text)
        else:
            text = pattern.sub(lambda m, inner=inner: f"\n\\[\n\\begin{{{inner}}}{m.group(1).strip()}\\end{{{inner}}}\n\\]\n", text)
    return text


def convert_text_markup(text: str) -> str:
    text = re.sub(r"\\textbf\{([^{}]*)\}", r"**\1**", text)
    text = re.sub(r"\\textit\{([^{}]*)\}", r"*\1*", text)
    text = re.sub(r"\\emph\{([^{}]*)\}", r"*\1*", text)
    text = re.sub(r"\\text\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\mathrm\{([^{}]*)\}", r"\\mathrm{\1}", text)
    text = re.sub(r"\\operatorname\{([^{}]*)\}", r"\\operatorname{\1}", text)
    text = DING_PATTERN.sub(lambda m: DING_MAP.get(int(m.group(1)), "•"), text)
    text = text.replace("\\noindent", "")
    text = text.replace("\\quad", " ")
    text = text.replace("\\qquad", "  ")
    text = re.sub(r"\\hfill", " ", text)
    text = re.sub(r"\\newline\b", "\n", text)
    text = re.sub(r"\\\\\s*", "\n", text)
    text = re.sub(r"\\sectionn?\*?\{[^{}]*\}", "", text)
    text = re.sub(r"\\subsection\*?\{[^{}]*\}", "", text)
    text = re.sub(r"\\(sub)*section\*?\{[^{}]*\}", "", text)
    text = re.sub(r"\\pagenumbering\{[^{}]*\}", "", text)
    text = re.sub(r"\\(vspace|hspace)\*?\{[^{}]*\}", "", text)
    text = re.sub(r"\\nt\{[^{}]*\}\{", "", text)
    return text


def cleanup_content(text: str) -> str:
    text = re.sub(r"\\begin\{myproof\}", "", text)
    text = re.sub(r"\\end\{myproof\}", "", text)
    text = re.sub(r"\\begin\{proof\}", "", text)
    text = re.sub(r"\\end\{proof\}", "", text)
    text = re.sub(r"\\item\b", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def convert_footnotes(text: str) -> str:
    cursor = 0
    while True:
        marker = text.find("\\footnote{", cursor)
        if marker < 0:
            break
        body, end = extract_braced(text, marker + len("\\footnote"))
        note = body.strip()
        replacement = f"（{note}）" if note else ""
        text = text[:marker] + replacement + text[end:]
        cursor = marker + len(replacement)
    return text


def latex_to_content(text: str, macros: dict[str, str]) -> str:
    text = strip_comments(text)
    text = remove_environments(text)
    text = convert_footnotes(text)
    text = re.sub(r"\\begin\{myproof\}[\s\S]*?\\end\{myproof\}", "", text)
    text = re.sub(r"\\begin\{proof\}[\s\S]*?\\end\{proof\}", "", text)
    text = re.sub(r"\\sol\b[\s\S]*?(?=\\(?:qs|Qs|ex|mprop|thm)\*?\{|$)", "", text)
    text = convert_math_environments(text)
    text = convert_lists(text)
    text = apply_macros(text, macros)
    text = convert_text_markup(text)
    text = cleanup_content(text)
    text = normalize_whitespace(text)
    return text


def expand_references(text: str, label_db: dict[str, str], depth: int = 0) -> str:
    if depth > 3:
        return text

    def repl(match: re.Match[str]) -> str:
        key = match.group(1).strip().rstrip("()")
        content = label_db.get(key)
        if not content:
            return f"（见 {key}）"
        expanded = latex_to_content(content, load_macros())
        return expanded

    return REF_PATTERN.sub(repl, text)


def enrich_stem_with_solution_context(stem: str, solution: str) -> str:
    if not solution or solution == PENDING_SOLUTION:
        return stem
    if "曳物线" in stem and "x = a \\sin t" not in stem and "x = a \\sin t" in solution:
        pass
    context_patterns = [
        (r"x = a \\sin t", r"设在\s*\$?xz\$?\s*平面"),
        (r"f\(u\) = \\frac\{1\}\{c\} e\^\{-cu\}", r"伪球面"),
    ]
    for snippet, trigger in context_patterns:
        if re.search(trigger, stem) and snippet not in stem and snippet in solution:
            block = re.search(rf".{{0,220}}{re.escape(snippet)}.{{0,220}}", solution)
            if block:
                stem = stem.strip() + "\n\n" + block.group(0).strip()
    return stem


def parse_command_at(text: str, pos: int) -> tuple[str, str, str, int] | None:
    for command in ("\\qs", "\\Qs", "\\ex", "\\mprop", "\\thm"):
        if text.startswith(command, pos):
            cursor = pos + len(command)
            if cursor < len(text) and text[cursor] == "*":
                cursor += 1
            if command == "\\Qs":
                body, cursor = extract_braced(text, cursor)
                return "question", "", body.strip(), cursor
            title, cursor = extract_braced(text, cursor)
            body, cursor = extract_braced(text, cursor)
            kind = {
                "\\qs": "question",
                "\\ex": "question",
                "\\mprop": "proposition",
                "\\thm": "theorem",
            }[command]
            return kind, title.strip(), body.strip(), cursor
    return None


def extract_solution_after(text: str, start: int) -> tuple[str, int]:
    cursor = start
    while cursor < len(text):
        match = re.search(
            r"\\begin\{myproof\}|\\begin\{proof\}|\\sol\b|\\pf\{",
            text[cursor:],
        )
        if not match:
            return "", len(text)
        absolute = cursor + match.start()
        if QUESTION_CMD_PATTERN.search(text, start, absolute):
            return "", absolute
        token = match.group(0)
        if token.startswith("\\begin{myproof}") or token.startswith("\\begin{proof}"):
            env = "myproof" if "myproof" in token else "proof"
            end = re.search(rf"\\end\{{{env}\}}", text[absolute:])
            if not end:
                return "", len(text)
            body = text[absolute + len(token) : absolute + end.start()]
            return body.strip(), absolute + end.end()
        if token == "\\sol":
            cursor = absolute + len(token)
            next_break = QUESTION_CMD_PATTERN.search(text, cursor)
            end = next_break.start() + cursor if next_break else len(text)
            return text[cursor:end].strip(), end
        if token == "\\pf{":
            cursor = absolute + len(token)
            title, cursor = extract_braced(text, absolute + 3)
            body, cursor = extract_braced(text, cursor)
            return body.strip(), cursor
    return "", len(text)


def find_next_marker(text: str, start: int) -> int | None:
    markers = [QUESTION_CMD_PATTERN, PROP_PATTERN, THEOREM_PATTERN]
    positions = []
    for pattern in markers:
        match = pattern.search(text, start)
        if match:
            positions.append(match.start())
    return min(positions) if positions else None


def parse_tex_file(path: Path, subject: str, macros: dict[str, str]) -> list[ParsedBlock]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = strip_comments(raw)
    file_stem = path.stem
    blocks: list[ParsedBlock] = []
    section_title = ""
    subsection_title = ""
    pending_context = ""
    index = 0

    pos = 0
    while pos < len(raw):
        section_match = SECTION_PATTERN.search(raw, pos)
        subsection_match = SUBSECTION_PATTERN.search(raw, pos)
        next_cmd = find_next_marker(raw, pos)
        candidates = [m.start() for m in (section_match, subsection_match) if m]
        if next_cmd is not None:
            candidates.append(next_cmd)
        if not candidates:
            break
        next_pos = min(candidates)

        if section_match and section_match.start() == next_pos:
            section_title = section_match.group(1).strip()
            pos = section_match.end()
            continue
        if subsection_match and subsection_match.start() == next_pos:
            subsection_title = subsection_match.group(1).strip()
            pos = subsection_match.end()
            continue

        parsed = parse_command_at(raw, next_pos)
        if not parsed:
            pos = next_pos + 1
            continue
        kind, title, body, cursor = parsed
        label_match = LABEL_PATTERN.search(raw, cursor, cursor + 120)
        label = label_match.group(1) if label_match else None

        if kind in {"proposition", "theorem"}:
            content = body if not title else f"{title}\n\n{body}"
            auto_label = label or f"{kind[:4]}:{file_stem}:{len([b for b in blocks if b.kind == kind]) + 1}"
            blocks.append(
                ParsedBlock(
                    kind=kind,
                    title=title,
                    body=content,
                    label=auto_label,
                    source_file=path.name,
                )
            )
            pending_context = content
            pos = cursor
            continue

        index += 1
        number_parts = [part for part in (file_stem, subsection_title, str(index)) if part]
        number = "-".join(number_parts)
        if title and title not in body[:40]:
            stem = f"**{title}**\n\n{body}" if title else body
        else:
            stem = body
        if pending_context and re.search(r"命题|定理|练习", body) and not re.search(r"\\ref(?:eq)?\{", body):
            stem = f"{pending_context}\n\n{stem}"
            pending_context = ""

        intro_start = max(0, next_pos - 1200)
        intro_chunk = raw[intro_start:next_pos]
        intro_chunk = re.sub(r"\\begin\{myproof\}[\s\S]*", "", intro_chunk)
        intro_match = re.search(r"\\noindent([\s\S]*?)$", intro_chunk)
        if intro_match and raw.startswith("\\Qs", next_pos):
            intro = latex_to_content(intro_match.group(1), macros)
            if intro and intro not in stem:
                stem = f"{intro}\n\n{stem}"
        if section_title and section_title.lower().startswith("week"):
            number = f"{section_title.replace(' ', '')}-{index}"

        solution, solution_end = extract_solution_after(raw, cursor)
        pos = solution_end if solution_end > cursor else cursor

        blocks.append(
            ParsedBlock(
                kind="question",
                title=title,
                body=stem,
                label=label or f"ex:{file_stem}:{index}",
                source_file=path.name,
                number=number,
                solution=solution,
            )
        )

    return blocks


def collect_tex_files() -> list[tuple[str, Path]]:
    files: list[tuple[str, Path]] = []
    for subject, directories in SUBJECT_SOURCES.items():
        for directory in directories:
            if not directory.is_dir():
                print(f"warning: missing directory {directory}", file=sys.stderr)
                continue
            for path in sorted(directory.glob("*.tex")):
                if path.name in SKIP_FILES or path.name.endswith(SKIP_SUFFIXES):
                    continue
                files.append((subject, path))
    return files


def file_section_key(file_stem: str) -> str:
    parts = file_stem.split("-")
    if len(parts) == 2 and all(part.isdigit() for part in parts):
        return f"{parts[0]}.{parts[1]}"
    return file_stem


def register_label_aliases(state: ImportState, raw_blocks: list[tuple[str, ParsedBlock]]) -> None:
    props_by_file: dict[str, list[ParsedBlock]] = {}
    questions_by_file: dict[str, list[ParsedBlock]] = {}

    for _subject, block in raw_blocks:
        if block.kind == "proposition":
            props_by_file.setdefault(block.source_file, []).append(block)
        elif block.kind == "question":
            questions_by_file.setdefault(block.source_file, []).append(block)
        if block.label:
            state.label_db[block.label] = block.body

    for filename, props in props_by_file.items():
        section = file_section_key(Path(filename).stem)
        for index, block in enumerate(props, start=1):
            state.label_db[f"prop:{section}.{index}"] = block.body

    for filename, questions in questions_by_file.items():
        section = file_section_key(Path(filename).stem)
        for index, block in enumerate(questions, start=1):
            state.label_db[f"ex:{section}.{index}"] = block.body


def build_questions(macros: dict[str, str]) -> ImportState:
    state = ImportState(macros=macros)
    raw_blocks: list[tuple[str, ParsedBlock]] = []

    for subject, path in collect_tex_files():
        for block in parse_tex_file(path, subject, macros):
            raw_blocks.append((subject, block))

    register_label_aliases(state, raw_blocks)

    for subject, block in raw_blocks:
        if block.kind != "question":
            continue
        stem = latex_to_content(block.body, macros)
        stem = expand_references(stem, state.label_db)
        solution_raw = block.solution
        solution = latex_to_content(solution_raw, macros) if solution_raw.strip() else PENDING_SOLUTION
        stem = enrich_stem_with_solution_context(stem, solution)
        stem = expand_references(stem, state.label_db)
        if solution != PENDING_SOLUTION:
            solution = expand_references(solution, state.label_db)

        question_id = f"{subject}-{block.number}".replace(" ", "")
        state.questions.append(
            {
                "id": question_id,
                "number": block.number,
                "subject": subject,
                "content": stem,
                "solution": solution,
                "source": block.source_file,
            }
        )
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/Users/yudongyi/suncoastmath-data/questions.json"),
        help="Output questions.json path",
    )
    args = parser.parse_args()

    macros = load_macros()
    state = build_questions(macros)
    payload = {
        "source": "latex-homework-import",
        "questions": {item["id"]: item for item in state.questions},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)

    subjects: dict[str, int] = {}
    for item in state.questions:
        subjects[item["subject"]] = subjects.get(item["subject"], 0) + 1
    print(f"Imported {len(state.questions)} questions")
    for subject, count in sorted(subjects.items()):
        print(f"  - {subject}: {count}")
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
