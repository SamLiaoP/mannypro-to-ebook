#!/bin/bash
# Rename "YYYY-MM-DD 標題.md" -> "YYYYMMDD 標題.md" inside <articles_dir>. Safe to rerun.
dir="${1:?usage: rename_dates.sh <articles_dir>}"
n=0
for f in "$dir"/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]\ *.md; do
  [ -e "$f" ] || continue
  base="$(basename "$f")"
  new="$(echo "$base" | sed -E 's/^([0-9]{4})-([0-9]{2})-([0-9]{2}) /\1\2\3 /')"
  mv "$f" "$dir/$new" && n=$((n+1))
done
echo "renamed $n file(s); total articles: $(ls "$dir"/[0-9]*.md 2>/dev/null | wc -l | tr -d ' ')"
