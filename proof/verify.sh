#!/bin/sh
# Public verification — anyone, anywhere, no trust required.
# Usage: ./verify.sh HUMAN 004 <salt>
# The output must equal the sha256 published BEFORE the votes.
printf '%s|round-%s|%s' "$1" "$2" "$3" | sha256sum | cut -d' ' -f1
