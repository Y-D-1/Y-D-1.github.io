#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_text_markdown(text: str) -> str:
    lines = text.replace("\r\n", "\n").split("\n")
    html_parts: list[str] = []
    list_type = None
    list_items: list[str] = []

    def flush_list() -> None:
        nonlocal list_type, list_items
        if not list_type:
            return
        html_parts.append(f"<{list_type}>")
        for item in list_items:
            html_parts.append(f"<li>{escape_html(item)}</li>")
        html_parts.append(f"</{list_type}>")
        list_type = None
        list_items = []

    for line in lines:
        ordered = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
        bullet = re.match(r"^\s*-\s+(.*)$", line)
        if ordered:
            if list_type != "ol":
                flush_list()
                list_type = "ol"
            list_items.append(ordered.group(2))
            continue
        if bullet:
            if list_type != "ul":
                flush_list()
                list_type = "ul"
            list_items.append(bullet.group(1))
            continue
        flush_list()
        if line.strip():
            html_parts.append(f"<p>{escape_html(line)}</p>")
    flush_list()
    return "".join(html_parts)


def find_delim_end(text: str, start: int, open_token: str, close_token: str) -> int:
    pos = start + len(open_token)
    depth = 1
    while pos < len(text) and depth > 0:
        if text.startswith(open_token, pos):
            depth += 1
            pos += len(open_token)
            continue
        if text.startswith(close_token, pos):
            depth -= 1
            if depth == 0:
                return pos + len(close_token)
            pos += len(close_token)
            continue
        pos += 1
    return -1


def render_markdown(text: str) -> str:
    html_parts: list[str] = []
    cursor = 0
    while cursor < len(text):
        display_start = text.find(r"\[", cursor)
        if display_start < 0:
            html_parts.append(render_text_markdown(text[cursor:]))
            break
        if display_start > cursor:
            html_parts.append(render_text_markdown(text[cursor:display_start]))
        display_end = find_delim_end(text, display_start, r"\[", r"\]")
        if display_end < 0:
            html_parts.append(render_text_markdown(text[display_start:]))
            break
        html_parts.append(text[display_start:display_end])
        cursor = display_end
    return "".join(html_parts)


def main() -> None:
    qid = sys.argv[1] if len(sys.argv) > 1 else "微分几何-6-4-第二题"
    questions = json.load(open("/Users/yudongyi/suncoastmath-data/questions.json"))["questions"]
    content = questions[qid]["content"]
    rendered = render_markdown(content)
    out = Path(__file__).resolve().parents[1] / "tmp-math-test.html"
    out.write_text(
        f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script>
window.MathJax = {{
  tex: {{
    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
    processEscapes: true,
    macros: {{ mn: '\\\\mathbf{{n}}', rd: '\\\\mathrm{{d}}' }}
  }},
  startup: {{
    pageReady: () => MathJax.startup.defaultPageReady().then(() => {{
      let inline = 0, display = 0;
      document.querySelectorAll('mjx-container').forEach((node) => {{
        if (node.getAttribute('display') === 'true') display += 1;
        else inline += 1;
      }});
      document.getElementById('stats').textContent = 'inline=' + inline + ' display=' + display;
    }})
  }}
}};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>
body {{ font-family: serif; max-width: 800px; margin: 2rem; }}
p {{ border: 1px solid #ddd; padding: 8px; }}
mjx-container[display="true"] {{ background: #fdd; }}
mjx-container[display="false"] {{ background: #dfd; }}
</style></head><body>
<h1>{qid}</h1>
<p id="stats">loading...</p>
<div id="q">{rendered}</div>
</body></html>
""",
        encoding="utf-8",
    )
    print(out)


if __name__ == "__main__":
    main()
