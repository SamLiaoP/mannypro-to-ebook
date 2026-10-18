#!/bin/bash
# Print the slug of every article already exported to <articles_dir>, one per line.
# Compare against list_all_titles output to find which articles still need exporting.
dir="${1:?usage: list_slugs.sh <articles_dir>}"
grep -h '^- 原文：' "$dir"/*.md 2>/dev/null | sed -E 's#.*/posts/##' | sort -u
