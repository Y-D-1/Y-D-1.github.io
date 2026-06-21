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
INTERRUPT_PATTERN = re.compile(r"\\(?:qs|Qs|ex)\*?\{|\\subsection\*?\{|\\section\*?\{")
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
    command: str = ""
    subsection: str = ""
    intro: str = ""
    subject: str = ""


@dataclass
class ImportState:
    macros: dict[str, str] = field(default_factory=dict)
    label_db: dict[str, str] = field(default_factory=dict)
    questions: list[dict[str, Any]] = field(default_factory=list)
    questions_by_file: dict[str, list[ParsedBlock]] = field(default_factory=dict)
    content_by_id: dict[str, str] = field(default_factory=dict)
    solution_by_id: dict[str, str] = field(default_factory=dict)


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
        if text.startswith("\\begin{", i):
            env_end = text.find("}", i + 7)
            if env_end < 0:
                raise ValueError("unbalanced braces")
            env_name = text[i + 7 : env_end]
            end_marker = f"\\end{{{env_name}}}"
            end_pos = text.find(end_marker, env_end + 1)
            if end_pos < 0:
                raise ValueError("unbalanced environment")
            i = end_pos + len(end_marker)
            continue
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


def collapse_inline_math_newlines(text: str) -> str:
    parts: list[str] = []
    cursor = 0
    while cursor < len(text):
        start = text.find(r"\(", cursor)
        if start < 0:
            parts.append(text[cursor:])
            break
        parts.append(text[cursor:start])
        end = start + 2
        depth = 1
        while end < len(text) and depth > 0:
            if text.startswith(r"\(", end):
                depth += 1
                end += 2
                continue
            if text.startswith(r"\)", end):
                depth -= 1
                end += 2
                continue
            end += 1
        block = text[start:end].replace("\n", " ")
        parts.append(block)
        cursor = end
    return "".join(parts)


def split_math_segments(text: str) -> list[tuple[bool, str]]:
    segments: list[tuple[bool, str]] = []
    cursor = 0
    while cursor < len(text):
        next_pos = -1
        token: tuple[str, str] | None = None
        if text.startswith(r"\(", cursor):
            next_pos = cursor
            token = (r"\(", r"\)")
        elif text.startswith(r"\[", cursor):
            next_pos = cursor
            token = (r"\[", r"\]")
        elif text.startswith("$$", cursor):
            next_pos = cursor
            token = ("$$", "$$")
        elif text[cursor] == "$":
            next_pos = cursor
            token = ("$", "$")

        if next_pos < 0 or token is None:
            segments.append((False, text[cursor:]))
            break

        if next_pos > cursor:
            segments.append((False, text[cursor:next_pos]))

        open_token, close_token = token
        end = next_pos + len(open_token)
        depth = 1
        while end < len(text) and depth > 0:
            if text.startswith(open_token, end):
                depth += 1
                end += len(open_token)
                continue
            if text.startswith(close_token, end):
                depth -= 1
                if depth == 0:
                    end += len(close_token)
                    break
                end += len(close_token)
                continue
            end += 1
        segments.append((True, text[next_pos:end]))
        cursor = end
    return segments


def apply_outside_math(text: str, transform) -> str:
    return "".join(
        segment if is_math else transform(segment)
        for is_math, segment in split_math_segments(text)
    )


def find_display_math_blocks(text: str) -> list[tuple[int, int]]:
    blocks: list[tuple[int, int]] = []
    cursor = 0
    while cursor < len(text):
        start = text.find(r"\[", cursor)
        if start < 0:
            break
        end = start + 2
        depth = 1
        while end < len(text) and depth > 0:
            if text.startswith(r"\[", end):
                depth += 1
                end += 2
                continue
            if text.startswith(r"\]", end):
                depth -= 1
                if depth == 0:
                    end += 2
                    break
                end += 2
                continue
            end += 1
        if depth == 0:
            blocks.append((start, end))
            cursor = end
        else:
            break
    return blocks


def apply_outside_display_math(text: str, transform) -> str:
    blocks = find_display_math_blocks(text)
    if not blocks:
        return transform(text)
    parts: list[str] = []
    cursor = 0
    for start, end in blocks:
        if start > cursor:
            parts.append(transform(text[cursor:start]))
        parts.append(text[start:end])
        cursor = end
    if cursor < len(text):
        parts.append(transform(text[cursor:]))
    return "".join(parts)


MATRIX_ENVS = ("pmatrix", "bmatrix", "vmatrix", "matrix", "cases", "aligned", "gathered", "align")


def fix_matrix_row_breaks(text: str) -> str:
    for env in MATRIX_ENVS:
        pattern = re.compile(
            rf"\\begin\{{(?P<env>{env})\*?\}}(?P<body>.*?)\\end\{{(?P=env)\*?\}}",
            re.DOTALL,
        )

        def repl(match: re.Match[str]) -> str:
            env_name = match.group("env")
            body = match.group("body")
            lines = [line.strip() for line in body.split("\n") if line.strip()]
            if len(lines) <= 1:
                return match.group(0)
            fixed_body = r" \\ ".join(lines)
            return rf"\begin{{{env_name}}}{fixed_body}\end{{{env_name}}}"

        text = pattern.sub(repl, text)
    return text


def merge_continued_display_math(text: str) -> str:
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"\\\]\s*\\\[\s*(?=[=+\-])", " ", text)
    return text


def fix_spacing_artifacts(text: str) -> str:
    text = re.sub(r"\\g\\left", r"g\\left", text)
    text = re.sub(r"\[1\.5ex\]", "", text)
    return text


def separate_prose_after_display_math(text: str) -> str:
    text = re.sub(r"\\\]\s*([\u4e00-\u9fff(（])", r"\\]\n\n\1", text)
    text = re.sub(r"请通过\s*\\\[", "请通过\n\n\\[", text)
    return text


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n")

    def compact(chunk: str) -> str:
        chunk = re.sub(r"\\\s*\n", " ", chunk)
        chunk = re.sub(r"\n{3,}", "\n\n", chunk)
        chunk = re.sub(r"[ \t]+\n", "\n", chunk)
        chunk = re.sub(r"\n{2,}", "\n\n", chunk)
        return chunk

    text = apply_outside_math(text, compact)
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
    itemize_pattern = re.compile(
        r"\\begin\{(?P<env>itemize\*?)(?:\[[^\]]*\])?\}(?P<body>.*?)\\end\{(?P=env)\}",
        re.DOTALL,
    )
    enumerate_pattern = re.compile(
        r"\\begin\{(?P<env>enumerate\*?)(?:\[[^\]]*\])?\}(?P<body>.*?)\\end\{(?P=env)\}",
        re.DOTALL,
    )

    def convert_itemize_block(match: re.Match[str]) -> str:
        body = match.group("body")
        items: list[str] = []
        for item_match in re.finditer(
            r"\\item(?:\[([^\]]*)\])?\s*(.*?)(?=\\item\b|$)",
            body,
            re.DOTALL,
        ):
            label = (item_match.group(1) or "").strip()
            content = item_match.group(2).strip()
            content = re.sub(r"\\end\{(?:enumerate|itemize)\*?\}\s*$", "", content).strip()
            if not content:
                continue
            if label:
                prefix = label if label.startswith("(") else f"({label})"
                items.append(f"{prefix} {content}")
            else:
                items.append(f"- {content}")
        return "\n".join(items)

    def convert_enumerate_block(match: re.Match[str]) -> str:
        body = match.group("body")
        body = itemize_pattern.sub(convert_itemize_block, body)
        segments = re.split(r"\\item(?:\[[^\]]*\])?", body)
        preamble = segments[0].strip() if segments else ""
        items = [segment.strip() for segment in segments[1:] if segment.strip()]
        if items:
            items[-1] = re.sub(r"\\end\{(?:enumerate|itemize)\*?\}\s*$", "", items[-1]).strip()
        lines: list[str] = []
        if preamble:
            lines.append(preamble)
        for index, item in enumerate(items, start=1):
            nested = itemize_pattern.sub(convert_itemize_block, item)
            lines.append(f"{index}. {nested}")
        return "\n".join(lines)

    previous = None
    current = text
    while previous != current:
        previous = current
        current = itemize_pattern.sub(convert_itemize_block, current)
        current = enumerate_pattern.sub(convert_enumerate_block, current)
    return current


def fix_display_math_nesting(text: str) -> str:
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"\\\[\s*\\\[", r"\\[", text)
        text = re.sub(r"\\\]\s*\\\]", r"\\]", text)
    text = re.sub(
        r"\\\[\s*\\begin\{(cases|matrix|pmatrix|bmatrix|vmatrix|aligned|gathered)\}",
        lambda match: f"\\[\\begin{{{match.group(1)}}}",
        text,
    )
    text = re.sub(
        r"\\end\{(cases|matrix|pmatrix|bmatrix|vmatrix|aligned|gathered)\}\s*\\\]\s*\\\]",
        r"\\end{\1}\\]",
        text,
    )
    text = re.sub(r"\\\[\s*\\\]", "", text)
    return text


def convert_math_environments(text: str) -> str:
    text = re.sub(
        r"\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}",
        lambda match: f"\n\\[{match.group(1).strip()}\\]\n",
        text,
        flags=re.DOTALL,
    )
    for env in ("align", "alignat", "gather"):
        pattern = re.compile(rf"\\begin\{{{env}\*?\}}(.*?)\\end\{{{env}\*?\}}", re.DOTALL)
        text = pattern.sub(
            lambda match: (
                f"\n\\[\n\\begin{{aligned}}{match.group(1).strip()}\\end{{aligned}}\n\\]\n"
            ),
            text,
        )
    text = fix_display_math_nesting(text)
    return text


def strip_spacing_commands(text: str) -> str:
    spacing = r"\\\\\[[0-9]+(?:\.[0-9]+)?(?:ex|pt|em)\]"
    text = re.sub(spacing, r" \\\\ ", text)
    text = re.sub(
        r"\\\[[0-9]+(?:\.[0-9]+)?(?:ex|pt|em)\]",
        r" \\\\ ",
        text,
    )
    text = re.sub(r"\\vspace\*?\{[^{}]*\}", "", text)
    text = re.sub(r"\\hspace\*?\{[^{}]*\}", "", text)
    text = re.sub(r"\\(small|med|big)skip\b", "", text)
    text = re.sub(r"\\setcounter\{[^}]*\}\{[^}]*\}", "", text)
    text = re.sub(r"\\quad\b", " ", text)
    text = re.sub(r"\\qquad\b", "  ", text)
    return text


def strip_stray_markup(text: str) -> str:
    text = re.sub(r"\[[^\]]*label=[^\]]*\]", "", text)
    text = re.sub(r"\[leftmargin=[^\]]*\]", "", text)
    text = re.sub(r"\\begin\{(?:enumerate|itemize)\*?\}(?:\[[^\]]*\])?", "", text)
    text = re.sub(r"\\end\{(?:enumerate|itemize)\*?\}", "", text)
    text = re.sub(r"\\(sub)*section\*?\{[^{}]*\}", "", text)
    text = re.sub(r"\\pagenumbering\{[^{}]*\}", "", text)
    text = re.sub(r"\\nt\{[^{}]*\}\{", "", text)
    text = re.sub(r"\\color\{[^{}]*\}", "", text)
    text = re.sub(r"\\vocab\{([^{}]*)\}", r"**\1**", text)
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

    def outside_markup(chunk: str) -> str:
        chunk = re.sub(r"\\hfill", " ", chunk)
        chunk = re.sub(r"\\newline\b", "\n", chunk)
        chunk = re.sub(r"\\\\\s*", "\n", chunk)
        return chunk

    return apply_outside_math(text, outside_markup)


def parse_reference_key(raw_key: str) -> tuple[str, str | None]:
    key = normalize_reference_key(raw_key.strip())
    match = re.match(r"^(ex|prop|thm|eq):([\d.]+)(?:\(([^)]*)\))?$", key)
    if match:
        base_key = f"{match.group(1)}:{match.group(2)}"
        part = (match.group(3) or "").strip() or None
        return base_key, part
    return key.rstrip("()"), None


def cleanup_content(text: str) -> str:
    text = re.sub(r"\\label\{[^}]*\}", "", text)
    text = re.sub(r"\\begin\{myproof\}", "", text)
    text = re.sub(r"\\end\{myproof\}", "", text)
    text = re.sub(r"\\begin\{proof\}", "", text)
    text = re.sub(r"\\end\{proof\}", "", text)
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


def join_broken_prose_lines(text: str) -> str:
    lines = text.split("\n")
    merged: list[str] = []
    for line in lines:
        stripped = line.strip()
        if (
            merged
            and stripped
            and re.match(r"[\u4e00-\u9fff(]", stripped)
            and merged[-1].rstrip().endswith(r"\)")
        ):
            merged[-1] = merged[-1].rstrip() + " " + stripped
            continue
        merged.append(line)
    return "\n".join(merged)


def join_orphan_inline_math_lines(text: str) -> str:
    previous = None
    while previous != text:
        previous = text
        text = re.sub(
            r"([^\n])\n(\s*\\\((?:\\.|[^\\])*\\\))\s*\n(?=[\u4e00-\u9fffA-Za-z(])",
            r"\1 \2\n",
            text,
        )
    return text


def demote_display_math_in_prose(text: str) -> str:
    """Turn sentence-embedded \\[...\\] into \\(...\\) in stems."""

    def should_demote(before: str, body: str, after: str) -> bool:
        body_stripped = body.strip()
        if not body_stripped or r"\begin{" in body:
            return False
        lines = [line.strip() for line in body_stripped.split("\n") if line.strip()]
        if len(lines) > 1:
            return False
        if before.endswith("\n\n"):
            return False
        if re.match(r"^\s*\n\s*\(\d+\)", after):
            return False
        if re.match(r"^\s*\n\s*\d+\.\s", after):
            return False
        if re.match(r"^\s*\n\s*\\\[", after):
            return False
        if re.match(r"^\s*[\u4e00-\u9fffA-Za-z0-9(\\]", after):
            return True
        if re.match(r"^\s*\n(?!\n)", after):
            return True
        return False

    def repl(match: re.Match[str]) -> str:
        before = text[: match.start()]
        after = text[match.end() :]
        body = match.group(1)
        if should_demote(before, body, after):
            return rf"\({body.strip()}\)"
        return match.group(0)

    return re.sub(r"\\\[([\s\S]*?)\\\]", repl, text)


def normalize_dollar_math(text: str) -> str:
    parts: list[str] = []
    cursor = 0
    while cursor < len(text):
        if text.startswith(r"\$", cursor):
            parts.append("$")
            cursor += 2
            continue
        if text[cursor] != "$":
            parts.append(text[cursor])
            cursor += 1
            continue
        if cursor + 1 < len(text) and text[cursor + 1] == "$":
            parts.append("$$")
            cursor += 2
            continue
        end = cursor + 1
        while end < len(text):
            if text.startswith(r"\$", end):
                end += 2
                continue
            if text[end] == "$":
                if end + 1 < len(text) and text[end + 1] == "$":
                    break
                inner = text[cursor + 1 : end]
                parts.append(rf"\({inner}\)")
                cursor = end + 1
                break
            end += 1
        else:
            parts.append("$")
            cursor += 1
    return "".join(parts)


def latex_to_content(text: str, macros: dict[str, str]) -> str:
    text = strip_comments(text)
    text = remove_environments(text)
    text = convert_footnotes(text)
    text = re.sub(r"\\begin\{myproof\}[\s\S]*?\\end\{myproof\}", "", text)
    text = re.sub(r"\\begin\{proof\}[\s\S]*?\\end\{proof\}", "", text)
    text = re.sub(r"\\sol\b[\s\S]*?(?=\\(?:qs|Qs|ex|mprop|thm)\*?\{|$)", "", text)
    text = strip_spacing_commands(text)
    text = convert_math_environments(text)
    text = convert_lists(text)
    text = apply_macros(text, macros)
    text = normalize_dollar_math(text)
    text = convert_text_markup(text)
    text = strip_stray_markup(text)
    text = cleanup_content(text)
    text = collapse_inline_math_newlines(text)
    text = fix_display_math_nesting(text)
    text = fix_matrix_row_breaks(text)
    text = merge_continued_display_math(text)
    text = separate_prose_after_display_math(text)
    text = fix_spacing_artifacts(text)
    text = normalize_whitespace(text)
    return text


def normalize_reference_key(key: str) -> str:
    key = key.strip().rstrip("()")
    if key.startswith("th:"):
        return f"thm:{key[3:]}"
    if key.startswith("rmk:"):
        return key
    return key


def format_missing_reference(key: str, part: str | None = None) -> str:
    key = normalize_reference_key(key)
    match = re.match(r"^(ex|prop|thm|rmk|eq):(.+)$", key)
    if match:
        kind_labels = {
            "ex": "习题",
            "prop": "命题",
            "thm": "定理",
            "rmk": "注记",
            "eq": "公式",
        }
        label = f"{kind_labels[match.group(1)]} {match.group(2)}"
    else:
        label = key.replace(":", " ")
    suffix = f" 第 {part} 小问" if part else ""
    return f"{label}{suffix}"


def lookup_reference(key: str, state: ImportState) -> str | None:
    key = normalize_reference_key(key)
    if key in state.label_db:
        return state.label_db[key]

    parsed = parse_ex_key(key)
    if parsed:
        chapter, section, number = parsed
        block = resolve_exercise_block(state, chapter, section, number)
        if block:
            qid = question_id_for_block(block.subject, block)
            return state.content_by_id.get(qid, block.body)

    match = re.match(r"^(ex|prop|thm|eq):([\d.]+)(?:\(([^)]*)\))?$", key)
    if not match:
        return None
    base = f"{match.group(1)}:{match.group(2)}"
    suffix = match.group(3)
    content = state.label_db.get(base)
    if not content:
        return None
    if suffix:
        part = extract_numbered_part(content, suffix)
        return part or f"{content}（第 {suffix} 小问）"
    return content


def question_id_for_block(subject: str, block: ParsedBlock) -> str:
    return f"{subject}-{block.number}".replace(" ", "")


def parse_ex_key(key: str) -> tuple[int, int, int] | None:
    key = normalize_reference_key(key)
    match = re.match(r"^ex:(\d+)\.(\d+)\.(\d+)$", key.strip())
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def resolve_exercise_block(state: ImportState, chapter: int, section: int, number: int) -> ParsedBlock | None:
    for filename, questions in state.questions_by_file.items():
        stem = Path(filename).stem
        candidates = (
            stem == str(section),
            stem == f"{chapter}-{section}",
            stem.replace("-", ".") == f"{chapter}.{section}",
        )
        if any(candidates) and 1 <= number <= len(questions):
            return questions[number - 1]
    return None


def extract_numbered_part(text: str, part: str) -> str | None:
    part = str(part).strip().rstrip(".")
    patterns = [
        rf"\({part}\)\s*(.*?)(?=\n\(\d+\)\s|\n\d+\.\s|\Z)",
        rf"(?:^|\n){part}\.\s*(.*?)(?=\n\d+\.\s|\n\(\d+\)\s|\Z)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match and match.group(1).strip():
            return match.group(1).strip()
    return None


def payload_for_reference(
    state: ImportState,
    key: str,
    part: str | None,
    *,
    use_solution: bool,
) -> str:
    macros = state.macros
    key = normalize_reference_key(key)
    parsed = parse_ex_key(key)
    if parsed:
        chapter, section, number = parsed
        block = resolve_exercise_block(state, chapter, section, number)
        if block:
            qid = question_id_for_block(block.subject, block)
            store = state.solution_by_id if use_solution else state.content_by_id
            payload = store.get(qid, "")
            if not payload and use_solution:
                payload = state.content_by_id.get(qid, block.body)
            if part and payload:
                extracted = extract_numbered_part(payload, part)
                if extracted:
                    return extracted
            if payload:
                return payload

    raw = state.label_db.get(key)
    if not raw:
        return f"（{key}）"
    processed = latex_to_content(raw, macros)
    if part:
        extracted = extract_numbered_part(processed, part)
        if extracted:
            return extracted
    return processed


def cleanup_reference_citations(text: str) -> str:
    text = re.sub(r"\bProp\s+", "", text)
    text = re.sub(r"\bThm\s+", "", text)
    text = re.sub(r"（\s*（([^）]+)）\s*）", r"（\1）", text)
    text = re.sub(r"习题\s+习题", "习题", text)
    text = re.sub(r"定理\s+定理", "定理", text)
    text = re.sub(r"命题\s+命题", "命题", text)
    text = re.sub(r"Rmk\\?\s+", "", text)
    return text


def expand_references(text: str, state: ImportState, depth: int = 0) -> str:
    if depth > 3:
        return text

    def repl(match: re.Match[str]) -> str:
        base_key, part = parse_reference_key(match.group(1))
        if base_key.startswith(("ex:", "prop:", "thm:", "rmk:")) and not part:
            return format_missing_reference(base_key)
        content = lookup_reference(base_key, state)
        if not content:
            return format_missing_reference(base_key, part)
        if content in state.content_by_id.values() or content in state.solution_by_id.values():
            if part:
                extracted = extract_numbered_part(content, part)
                return extracted or content
            return format_missing_reference(base_key)
        expanded = latex_to_content(content, state.macros)
        if part:
            extracted = extract_numbered_part(expanded, part)
            return extracted or expanded
        return expanded

    return cleanup_reference_citations(REF_PATTERN.sub(repl, text))


def expand_prose_references(
    text: str,
    state: ImportState,
    source_file: str,
    question_index: int,
) -> str:
    questions = state.questions_by_file.get(source_file, [])
    if question_index > 1 and "同上题" in text:
        prev = questions[question_index - 2]
        qid = question_id_for_block(prev.subject, prev)
        replacement = state.solution_by_id.get(qid) or state.content_by_id.get(qid, "")
        if replacement:
            text = text.replace("同上题", replacement)

    text = re.sub(
        r"同习题\s*\\ref\{([^}]+)\}(?:\(([^)]*)\))?(?:\.)?",
        lambda match: payload_for_reference(
            state, match.group(1).strip(), match.group(2), use_solution=True
        ),
        text,
    )
    text = re.sub(
        r"由习题\s*\\ref(?:eq)?\{([^}]+)\}(?:\(([^)]*)\))?(?:的)?结论",
        lambda match: payload_for_reference(
            state, match.group(1).strip(), match.group(2), use_solution=False
        ),
        text,
    )
    text = re.sub(
        r"(?:见|参见)习题\s*\\ref(?:eq)?\{([^}]+)\}(?:\(([^)]*)\))?",
        lambda match: payload_for_reference(
            state, match.group(1).strip(), match.group(2), use_solution=False
        ),
        text,
    )
    text = re.sub(
        r"（习题\s*[\d.]+\s*(?:第\s*[\d.]+\s*题)?）(?:\(([^)]*)\))?",
        "",
        text,
    )
    return text


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


def parse_command_at(text: str, pos: int) -> tuple[str, str, str, str, int] | None:
    for command in ("\\qs", "\\Qs", "\\ex", "\\mprop", "\\thm"):
        if text.startswith(command, pos):
            cursor = pos + len(command)
            if cursor < len(text) and text[cursor] == "*":
                cursor += 1
            if command == "\\Qs":
                body, cursor = extract_braced(text, cursor)
                return "question", "", body.strip(), "Qs", cursor
            title, cursor = extract_braced(text, cursor)
            body, cursor = extract_braced(text, cursor)
            kind = {
                "\\qs": "question",
                "\\ex": "question",
                "\\mprop": "proposition",
                "\\thm": "theorem",
            }[command]
            cmd_name = command.lstrip("\\")
            return kind, title.strip(), body.strip(), cmd_name, cursor
    return None


def extract_subsection_intro(raw: str, start: int, end: int) -> str:
    chunk = raw[start:end]
    chunk = re.sub(r"\\begin\{myproof\}[\s\S]*?\\end\{myproof\}", "", chunk)
    chunk = re.sub(r"\\sol\b[\s\S]*?(?=\\Qs|\\qs|\\ex|$)", "", chunk)
    chunk = re.sub(r"\\subsection\*?\{[^{}]*\}", "", chunk)
    chunk = re.sub(r"\\section\*?\{[^{}]*\}", "", chunk)
    chunk = re.sub(r"\\setcounter\{[^}]*\}\{[^}]*\}", "", chunk)
    chunk = re.sub(r"\\(?:qs|Qs|ex|mprop|thm)\*?\{[\s\S]*$", "", chunk)
    chunk = chunk.strip()
    if not chunk:
        return ""
    return chunk


def merge_qs_blocks(blocks: list[ParsedBlock], file_stem: str) -> list[ParsedBlock]:
    merged: list[ParsedBlock] = []
    index = 0
    cursor = 0
    while cursor < len(blocks):
        block = blocks[cursor]
        if block.kind != "question" or block.command != "Qs":
            if block.kind == "question":
                index += 1
                block.number = build_standalone_number(file_stem, block, index)
            merged.append(block)
            cursor += 1
            continue

        group = [block]
        next_cursor = cursor + 1
        while next_cursor < len(blocks):
            candidate = blocks[next_cursor]
            if (
                candidate.kind == "question"
                and candidate.command == "Qs"
                and candidate.subsection == block.subsection
                and candidate.source_file == block.source_file
            ):
                group.append(candidate)
                next_cursor += 1
            else:
                break

        merged.append(merge_qs_group(group, file_stem))
        cursor = next_cursor
    return merged


def build_standalone_number(file_stem: str, block: ParsedBlock, index: int) -> str:
    if block.subsection:
        return f"{file_stem}-{block.subsection}"
    if block.title and block.title.lower().startswith("week"):
        return f"{block.title.replace(' ', '')}-{index}"
    return f"{file_stem}-{index}"


def merge_qs_group(group: list[ParsedBlock], file_stem: str) -> ParsedBlock:
    intro = group[0].intro
    number_parts = [file_stem, group[0].subsection]
    number = "-".join(part for part in number_parts if part)

    if len(group) == 1:
        body = group[0].body
        if intro and intro not in body:
            body = f"{intro}\n\n{body}"
        solution = group[0].solution
    else:
        stem_parts: list[str] = []
        if intro:
            stem_parts.append(intro)
        for part_index, item in enumerate(group, start=1):
            stem_parts.append(f"({part_index}) {item.body}")
        body = "\n\n".join(stem_parts)

        solution_parts: list[str] = []
        for part_index, item in enumerate(group, start=1):
            if item.solution.strip():
                solution_parts.append(f"({part_index}) {item.solution}")
            else:
                solution_parts.append(f"({part_index}) {PENDING_SOLUTION}")
        solution = "\n\n".join(solution_parts)
        if all(not item.solution.strip() for item in group):
            solution = PENDING_SOLUTION

    return ParsedBlock(
        kind="question",
        title="",
        body=body,
        label=group[0].label,
        source_file=group[0].source_file,
        number=number,
        solution=solution,
        command="Qs",
        subsection=group[0].subsection,
        intro=intro,
    )


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
        if INTERRUPT_PATTERN.search(text, start, absolute):
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
            next_break = INTERRUPT_PATTERN.search(text, cursor)
            end = next_break.start() if next_break else len(text)
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
    subsection_start = 0
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
            subsection_start = subsection_match.end()
            pos = subsection_match.end()
            continue

        parsed = parse_command_at(raw, next_pos)
        if not parsed:
            pos = next_pos + 1
            continue
        kind, title, body, command, cursor = parsed
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
        intro = ""
        if command == "Qs":
            intro = extract_subsection_intro(raw, subsection_start, next_pos)

        stem = body
        if pending_context and re.search(r"命题|定理|练习", body) and not re.search(r"\\ref(?:eq)?\{", body):
            stem = f"{pending_context}\n\n{stem}"
            pending_context = ""

        solution, solution_end = extract_solution_after(raw, cursor)
        pos = solution_end if solution_end > cursor else cursor

        if section_title and section_title.lower().startswith("week"):
            number = f"{section_title.replace(' ', '')}-{index}"
        elif command == "Qs":
            number = "-".join(part for part in (file_stem, subsection_title) if part)
        else:
            number = "-".join(part for part in (file_stem, subsection_title, str(index)) if part)

        blocks.append(
            ParsedBlock(
                kind="question",
                title=title,
                body=stem,
                label=label or f"ex:{file_stem}:{index}",
                source_file=path.name,
                number=number,
                solution=solution,
                command=command,
                subsection=subsection_title,
                intro=intro,
                subject=subject,
            )
        )

    return merge_qs_blocks(blocks, file_stem)


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

    for subject, block in raw_blocks:
        if block.kind == "proposition":
            props_by_file.setdefault(block.source_file, []).append(block)
        elif block.kind == "question":
            questions_by_file.setdefault(block.source_file, []).append(block)
            block.subject = subject
        if block.label:
            state.label_db[block.label] = block.body

    state.questions_by_file = questions_by_file

    for filename, props in props_by_file.items():
        section = file_section_key(Path(filename).stem)
        for index, block in enumerate(props, start=1):
            state.label_db[f"prop:{section}.{index}"] = block.body

    for filename, questions in questions_by_file.items():
        section = file_section_key(Path(filename).stem)
        stem = Path(filename).stem
        for index, block in enumerate(questions, start=1):
            state.label_db[f"ex:{section}.{index}"] = block.body
            if stem.isdigit():
                state.label_db[f"ex:7.{stem}.{index}"] = block.body
            parts = stem.split("-")
            if len(parts) == 2 and all(part.isdigit() for part in parts):
                state.label_db[f"ex:{parts[0]}.{parts[1]}.{index}"] = block.body


def build_questions(macros: dict[str, str]) -> ImportState:
    state = ImportState(macros=macros)
    raw_blocks: list[tuple[str, ParsedBlock]] = []

    for subject, path in collect_tex_files():
        for block in parse_tex_file(path, subject, macros):
            raw_blocks.append((subject, block))

    register_label_aliases(state, raw_blocks)

    prepared: list[tuple[str, ParsedBlock, str, str, int]] = []
    for subject, block in raw_blocks:
        if block.kind != "question":
            continue
        stem = latex_to_content(block.body, macros)
        solution_raw = block.solution
        solution = latex_to_content(solution_raw, macros) if solution_raw.strip() else PENDING_SOLUTION
        stem = enrich_stem_with_solution_context(stem, solution)
        question_index = state.questions_by_file.get(block.source_file, []).index(block) + 1
        prepared.append((subject, block, stem, solution, question_index))

    for subject, block, stem, solution, _question_index in prepared:
        qid = question_id_for_block(subject, block)
        state.content_by_id[qid] = stem
        if solution != PENDING_SOLUTION:
            state.solution_by_id[qid] = solution

    for subject, block, stem, solution, question_index in prepared:
        stem = expand_prose_references(stem, state, block.source_file, question_index)
        stem = expand_references(stem, state)
        stem = demote_display_math_in_prose(stem)
        stem = merge_continued_display_math(stem)
        stem = separate_prose_after_display_math(stem)
        stem = fix_matrix_row_breaks(stem)
        stem = join_orphan_inline_math_lines(stem)
        stem = join_broken_prose_lines(stem)
        if solution != PENDING_SOLUTION:
            solution = expand_prose_references(solution, state, block.source_file, question_index)
            solution = expand_references(solution, state)

        question_id = question_id_for_block(subject, block)
        state.content_by_id[question_id] = stem
        if solution != PENDING_SOLUTION:
            state.solution_by_id[question_id] = solution

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
