#!/bin/sh
# The daily ritual, two commands.
#
#   ./daily.sh publish 001
#   ./daily.sh reveal  001 AI
#
# Reveal reads the salt from the private seal file and lets the Worker
# re-verify the hash before anything becomes public.

API="${HUMANOR_API:-https://humanor-api.workers.dev}"
KEY="${HUMANOR_KEY:?export HUMANOR_KEY first}"

case "$1" in
  publish)
    curl -sS -X POST "$API/api/admin/publish" \
      -H "x-humanor-key: $KEY" -H 'content-type: application/json' \
      -d "{\"no\":$2}"; echo ;;
  reveal)
    SALT=$(python3 -c "import json;print(json.load(open('../proof/revealed.json'))['$2']['salt'])")
    SRC="${4:-}"
    curl -sS -X POST "$API/api/admin/reveal" \
      -H "x-humanor-key: $KEY" -H 'content-type: application/json' \
      -d "{\"no\":$2,\"label\":\"$3\",\"salt\":\"$SALT\",\"source\":\"$SRC\"}"; echo ;;
  *) echo "usage: daily.sh publish <no> | daily.sh reveal <no> <LABEL> [source]" ;;
esac
