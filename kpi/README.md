# KPI — what can actually be measured, and when

Honest answer to "will it capture everything?": **it depends on API access**, and
the two tiers are very different. Nothing here pretends otherwise.

## Tier 1 — today, no API (works from day one)

| Metric | Source | How |
|---|---|---|
| Votes HUMAN / AI / other | **the site** (Worker + D1) | live, exact, already built |
| Fool rate | site votes | computed by the Worker |
| Reach, plays, likes, saves, shares | **Meta Business Suite** | export CSV weekly, `import_insights.py` |
| Comments | copy/paste or CSV export | `comments.py` classifies them |
| Follower growth | Business Suite | weekly export |

Tier 1 gives you **everything that matters for the fool rate**, because the
site's votes are exact — no parsing, no ambiguity. IG comments are a second,
noisier sample.

## Tier 2 — after Meta App Review (weeks, needs a legal entity)

| Metric | Endpoint | Note |
|---|---|---|
| All comments, live | `GET /{ig-media-id}/comments` | webhook available for real-time |
| Likes, saves, shares, plays, reach | `GET /{ig-media-id}/insights` | per post |
| Replies to comments | same | threaded |
| **DMs** | Messenger API for Instagram | separate permission, heavier review |
| Publishing | `POST /{ig-user-id}/media` | the auto-drop |

**DMs are the hardest**: a distinct permission set, an extra review, and a
webhook you must host. Not worth it before the account has traction.

## The honest hierarchy

1. **Site votes** — exact, yours, no gatekeeper. Build the funnel to send
   people there and the KPI problem largely disappears.
2. **IG comments** — a large but noisy sample. `comments.py` resolves ~90% and
   flags the rest rather than guessing.
3. **IG insights** — reach/saves/shares tell you distribution, not opinion.
   Weekly is enough; daily is noise.

## Files

- `import_insights.py` — reads a Business Suite CSV export into the same schema
- `report.py` — the weekly read: fool rate by author, by style, by family,
  and which lines travelled
