#!/usr/bin/env bash
# Verify that every relative Markdown link under a Book root resolves to an
# existing path. External (http/https/mailto) links and same-page anchors are
# out of scope. Fenced code blocks and inline code spans are ignored, so link
# syntax quoted as an example is not treated as a link.
# Usage: check-links.sh [<book-root>]   (default: docs)
# Exit: 0 when every link resolves; 1 and one "BROKEN <file>: <target>" line
# per unresolved link otherwise.
set -uo pipefail

ROOT="${1:-docs}"
[ -d "$ROOT" ] || { echo "check-links: no such directory $ROOT" >&2; exit 2; }

broken=0
checked=0
while IFS= read -r -d '' file; do
  dir=$(dirname "$file")
  while IFS= read -r target; do
    [ -n "$target" ] || continue
    case "$target" in
      http://*|https://*|mailto:*|'#'*) continue ;;
    esac
    path=${target%%#*}
    checked=$((checked + 1))
    if [ ! -e "$dir/$path" ]; then
      echo "BROKEN $file: $target"
      broken=$((broken + 1))
    fi
  done < <(awk '
    /^[[:space:]]*(```|~~~)/ { fence = !fence; next }
    fence { next }
    {
      line = $0
      gsub(/`[^`]*`/, "", line)
      while (match(line, /\]\([^) ]+\)/)) {
        print substr(line, RSTART + 2, RLENGTH - 3)
        line = substr(line, RSTART + RLENGTH)
      }
    }
  ' "$file")
done < <(find "$ROOT" -type f -name '*.md' -print0)

echo "check-links: $checked relative links checked, $broken broken"
[ "$broken" -eq 0 ]
