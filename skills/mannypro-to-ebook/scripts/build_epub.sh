#!/bin/bash
# Build the two ebook files (standard EPUB + Kobo KEPUB) from an articles folder.
# usage: build_epub.sh <articles_dir> <out_dir> [--from YYYYMMDD] [--to YYYYMMDD] [--name 曼報Pro合輯]
# Steps: shrink_images.py (downscale copy of assets) -> md2epub.py twice.
# Output names: "<name> <first>-<last>.epub" and "<name> <first>-<last> for kobo.kepub.epub",
# where first/last are the earliest/latest article dates actually included.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ART="${1:?articles_dir}"; OUT="${2:?out_dir}"; shift 2
FROM=00000000; TO=99999999; NAME="曼報Pro合輯"
while [ $# -gt 0 ]; do case "$1" in
  --from) FROM="$2"; shift 2;; --to) TO="$2"; shift 2;; --name) NAME="$2"; shift 2;;
  *) echo "unknown arg $1"; exit 1;; esac; done

FIRST=""; LAST=""
for f in "$ART"/[0-9]*.md; do d="$(basename "$f" | cut -c1-8)"
  [ "$d" \< "$FROM" ] && continue; [ "$d" \> "$TO" ] && continue
  [ -z "$FIRST" ] || [ "$d" \< "$FIRST" ] && FIRST="$d"; [ -z "$LAST" ] || [ "$d" \> "$LAST" ] && LAST="$d"; done
[ -n "$FIRST" ] || { echo "no articles in range"; exit 1; }

IMG="${TMPDIR:-/tmp}/manbao-images-$$"
rm -rf "$IMG"
python3 -I "$HERE/shrink_images.py" "$ART/assets" "$IMG"

mkdir -p "$OUT"
python3 -I "$HERE/md2epub.py" "$ART" "$IMG" "$OUT/$NAME $FIRST-$LAST.epub" --from "$FROM" --to "$TO"
python3 -I "$HERE/md2epub.py" "$ART" "$IMG" "$OUT/$NAME $FIRST-$LAST for kobo.kepub.epub" --kepub --from "$FROM" --to "$TO"
rm -rf "$IMG"
