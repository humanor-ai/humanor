# humanor

One line a day. A human wrote it — or a machine did. You vote. Truth at 17:55.

## Why you can trust this

You don't have to trust anyone. You can check.

1. **Sealed answers.** Before a round is published, its answer is committed:
   `sha256("LABEL|round-id|salt")`. The hash is printed in the post itself.
   At reveal, the salt is published. Verify any round yourself:

   ```sh
   ./proof/verify.sh HUMAN 004 <salt>
   ```

   If the output matches the hash posted before the votes, the answer was
   sealed before you played. It is mathematically impossible for us to
   change an answer after seeing the votes.

2. **Verified sources.** A human quote is publishable only if it is found
   verbatim in the source e-text (`verifier/g1_verify.py`). Famous quotes
   that exist nowhere in an author's actual work are rejected, whoever
   the internet says wrote them. Every reveal cites work, year, chapter.

3. **Open everything.** This repository contains the verifier, the seal
   tool, the design tokens, and the dataset of every revealed round.
   The AI voice of this project runs on open-weight models.

## Who is behind this

No one you will ever meet. Releases are signed with the project key
(fingerprint on the site). The protocol is the identity.

## License

AGPL-3.0 — anything built from this must stay open. (Add the full text
via GitHub's license picker on first commit.)
