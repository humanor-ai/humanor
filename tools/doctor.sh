#!/bin/sh
# Identity hygiene check — run before EVERY push. Blocks the classic leaks.
FAIL=0
EMAIL=$(git config user.email)
NAME=$(git config user.name)

case "$EMAIL" in
  *users.noreply.github.com) echo "OK   email is GitHub noreply ($EMAIL)";;
  *) echo "LEAK user.email is '$EMAIL' — use the project's GitHub noreply address"; FAIL=1;;
esac

[ "$NAME" = "humanor" ] && echo "OK   user.name is 'humanor'" \
  || { echo "LEAK user.name is '$NAME' — must be 'humanor'"; FAIL=1; }

[ "$(git config commit.gpgsign)" = "true" ] && echo "OK   commits are GPG-signed" \
  || { echo "WARN commit.gpgsign is off — sign with the project key"; FAIL=1; }

git log --format='%ae %an' 2>/dev/null | sort -u | grep -vi 'noreply\|humanor' \
  && { echo "LEAK personal identity found in git history above"; FAIL=1; } \
  || echo "OK   no personal identity in git history"

git remote -v | grep -qi 'flom95' \
  && { echo "LEAK remote URL mentions personal account"; FAIL=1; } \
  || echo "OK   remotes are clean"

echo "TIP  commit with UTC timezone: git config alias.c 'commit --date=format:%cI'; export TZ=UTC"
[ $FAIL -eq 0 ] && echo "DOCTOR: CLEAN — safe to push" || echo "DOCTOR: BLOCKED — fix leaks first"
exit $FAIL
