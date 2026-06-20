#!/usr/bin/env bash
# Copy local question bank into a new private-repo folder (does not push to GitHub).
set -euo pipefail

SOURCE="${1:-$HOME/Documents/suncoastmath_data/questions.json}"
TARGET_DIR="${2:-$HOME/suncoastmath-data}"

if [[ ! -f "$SOURCE" ]]; then
  echo "Source not found: $SOURCE" >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"
cp "$SOURCE" "$TARGET_DIR/questions.json"

if [[ ! -d "$TARGET_DIR/.git" ]]; then
  git -C "$TARGET_DIR" init
  git -C "$TARGET_DIR" branch -M main
fi

git -C "$TARGET_DIR" add questions.json
git -C "$TARGET_DIR" diff --cached --quiet && echo "No changes to commit." && exit 0
git -C "$TARGET_DIR" commit -m "Update practice question bank"

cat <<EOF

Prepared private data repo at: $TARGET_DIR

Next steps:
1. Create a private GitHub repo (e.g. Y-D-1/analysis-algebra)
2. git -C "$TARGET_DIR" remote add origin git@github.com:Y-D-1/analysis-algebra.git
3. git -C "$TARGET_DIR" push -u origin main
4. Configure GitHub Actions secrets (see worker/README.md)
EOF
