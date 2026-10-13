#!/usr/bin/env bash
# Mirror /workspace/News/<cat>/*.md -> docs/<cat>/ (adds, updates, deletions), commit, push via gh-authenticated git.
set -euo pipefail
SRC=/workspace/News; REPO=/workspace/news-site
cd "$REPO"
git pull -q --rebase origin main
for c in Daily Chinese-Topics English-Topics High-Traffic; do
  mkdir -p "$SRC/$c" "docs/$c"
  for f in "$SRC/$c"/*.md; do [ -e "$f" ] || continue; n=$(basename "$f"); [ "$n" = index.md ] && continue
    cmp -s "$f" "docs/$c/$n" || cp "$f" "docs/$c/$n"; done
  for f in "docs/$c"/*.md; do [ -e "$f" ] || continue; n=$(basename "$f"); [ "$n" = index.md ] && continue
    [ -e "$SRC/$c/$n" ] || git rm -q "$f"; done
done
git add -A docs
if git diff --cached --quiet; then echo "no changes"; exit 0; fi
git commit -q -m "sync reports $(date '+%Y-%m-%d %H:%M')"
git push -q origin main
echo "pushed; watch: gh run list -R robbin/x-news"
