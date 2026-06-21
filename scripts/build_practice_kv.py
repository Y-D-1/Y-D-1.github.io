#!/usr/bin/env python3
"""Build Cloudflare KV bulk upload file from suncoastmath questions.json."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def subject_name(question: dict[str, Any]) -> str:
    subject = question.get("subject")
    if isinstance(subject, dict):
        return str(subject.get("name") or "未分类").strip() or "未分类"
    return str(subject or "未分类").strip() or "未分类"


def public_question(question: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": question["id"],
        "subject": subject_name(question),
        "content": question.get("content") or "",
    }


def build_entries(questions: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    indexes: dict[str, list[str]] = defaultdict(list)
    counts: dict[str, int] = defaultdict(int)
    subjects: set[str] = set()
    entries: list[dict[str, str]] = []

    for question in questions.values():
        question_id = question.get("id")
        if not question_id:
            continue

        subject = subject_name(question)
        subjects.add(subject)
        indexes[f"idx:{subject}:all"].append(question_id)
        counts[subject] += 1

        entries.append(
            {
                "key": f"q:{question_id}",
                "value": json.dumps(public_question(question), ensure_ascii=False, separators=(",", ":")),
            }
        )

        solution = question.get("solution")
        if solution is not None:
            entries.append(
                {
                    "key": f"sol:{question_id}",
                    "value": json.dumps(
                        {"id": question_id, "solution": solution},
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                }
            )

    for key, ids in indexes.items():
        entries.append(
            {
                "key": key,
                "value": json.dumps(ids, ensure_ascii=False, separators=(",", ":")),
            }
        )

    meta = {
        "subjects": sorted(subjects),
        "counts": dict(sorted(counts.items())),
        "total": sum(counts.values()),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    entries.append({"key": "meta", "value": json.dumps(meta, ensure_ascii=False, separators=(",", ":"))})
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Path to questions.json")
    parser.add_argument("--output", type=Path, required=True, help="Path to KV bulk JSON output")
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 1

    with args.input.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    questions = payload.get("questions")
    if not isinstance(questions, dict):
        print("Invalid questions.json: missing 'questions' object", file=sys.stderr)
        return 1

    entries = build_entries(questions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(entries, handle, ensure_ascii=False, separators=(",", ":"))

    meta_entry = next(entry for entry in entries if entry["key"] == "meta")
    meta = json.loads(meta_entry["value"])
    print(f"Built {len(entries)} KV entries for {meta['total']} questions")
    print(f"Subjects: {', '.join(meta['subjects'])}")
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
