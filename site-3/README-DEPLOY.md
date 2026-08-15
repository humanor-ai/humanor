# Deploying humanor.co

Static files. No build step. Drop them anywhere.

## Cloudflare Pages (recommended — free, already your DNS)

1. Push this `site/` folder to the repo (already done if you committed).
2. dash.cloudflare.com → **Workers & Pages** → **Create** → **Pages** →
   **Connect to Git** → authorise `humanor-ai` → pick `humanor`.
3. Build settings:
   - Framework preset: **None**
   - Build command: *(leave empty)*
   - Build output directory: **site**
4. **Save and Deploy**.
5. Once live → **Custom domains** → add `humanor.co` and `www.humanor.co`.
   Cloudflare writes the DNS records itself.

Every push to `main` redeploys. That's the whole pipeline.

## The daily loop

`rounds.json` is the entire database for v1. One object per round:

```json
{
  "no": 1,
  "date": "2026-08-20",
  "text": "The stars don't know we named them.",
  "published": true,     // shows on the site
  "revealed": false,     // truth is out
  "sha256": "...",       // from: make seal R=001 L=AI
  "label": null,         // fill at reveal
  "salt": null,          // fill at reveal
  "source": null,        // "Oscar Wilde, The Importance of Being Earnest, 1895"
  "foolRate": null       // 64
}
```

**Publish**  `make seal R=001 L=AI` → copy the sha256 into the round →
`published: true` → commit → push.

**Reveal (17:55)**  `make reveal R=001` → paste `label`, `salt`, `source`,
`foolRate` → `revealed: true` → commit → push.

## Before launch

- **Self-host the two fonts.** Google Fonts sends visitor IPs to Google, which
  contradicts the manifesto. Download Instrument Serif + IBM Plex Mono as
  woff2 into `site/fonts/`, uncomment the `@font-face` block at the top of
  `style.css`, delete the `<link>` tags in the three HTML files.
- **Analytics**, if any: Umami or Plausible, self-hosted, no cookies. Or none.
- Replace the PGP fingerprint in `proof.html` if the key ever changes.

## Later (v2)

`rounds.json` becomes a Cloudflare Worker + D1 so votes are counted live and
the community percentage appears before the reveal. The front end already
expects that shape — swap the fetch, nothing else changes.
