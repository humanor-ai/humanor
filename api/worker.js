/**
 * humanor — the whole backend. One Worker, one D1 database.
 *
 * Public:
 *   GET  /api/rounds            published rounds (answers stripped until reveal)
 *   POST /api/vote              { no, choice, voter }
 *   GET  /api/stats/:no         live tally
 *
 * Admin (header  x-humanor-key: <ADMIN_KEY> ):
 *   POST /api/admin/round       upsert a round
 *   POST /api/admin/publish     { no }
 *   POST /api/admin/reveal      { no, label, salt, source }
 *
 * The answer is NEVER sent to a client before reveal — not hidden in the
 * payload, not present at all. The only thing published early is its hash.
 */

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
      'access-control-allow-origin': '*',
      'access-control-allow-headers': 'content-type,x-humanor-key',
      'access-control-allow-methods': 'GET,POST,OPTIONS'
    }
  });

const strip = (r) => ({
  no: r.no,
  date: r.date,
  text: r.text,
  sha256: r.sha256,
  published: !!r.published,
  revealed: !!r.revealed,
  votes: { human: r.votes_human, ai: r.votes_ai },
  foolRate: foolRate(r),
  // the answer only exists in the payload once it is public
  ...(r.revealed ? { label: r.label, salt: r.salt, source: r.source } : {})
});

/** Share of players who got it wrong — the number that becomes the caption. */
function foolRate(r) {
  if (!r.revealed) return null;
  const total = r.votes_human + r.votes_ai;
  if (total < 20) return null;                 // too few to be worth publishing
  const wrong = r.label === 'HUMAN' ? r.votes_ai : r.votes_human;
  return Math.round((wrong / total) * 100);
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const path = url.pathname;

    if (req.method === 'OPTIONS') return json({});

    try {
      /* ------------------------------------------------------------ public */
      if (path === '/api/rounds' && req.method === 'GET') {
        const { results } = await env.DB.prepare(
          'SELECT * FROM rounds WHERE published = 1 ORDER BY no DESC'
        ).all();
        return json(results.map(strip));
      }

      if (path.startsWith('/api/stats/') && req.method === 'GET') {
        const no = parseInt(path.split('/').pop(), 10);
        const r = await env.DB.prepare('SELECT * FROM rounds WHERE no = ? AND published = 1')
          .bind(no).first();
        if (!r) return json({ error: 'no such round' }, 404);
        return json(strip(r));
      }

      if (path === '/api/vote' && req.method === 'POST') {
        const { no, choice, voter } = await req.json();
        if (!['HUMAN', 'AI'].includes(choice)) return json({ error: 'bad choice' }, 400);
        if (!voter || String(voter).length < 8) return json({ error: 'bad voter' }, 400);

        const r = await env.DB.prepare('SELECT * FROM rounds WHERE no = ? AND published = 1')
          .bind(no).first();
        if (!r) return json({ error: 'no such round' }, 404);

        // INSERT OR IGNORE + rowcount: one vote per voter, decided by the database
        const ins = await env.DB.prepare(
          'INSERT OR IGNORE INTO votes (round_no, voter, choice, ts) VALUES (?, ?, ?, ?)'
        ).bind(no, String(voter).slice(0, 64), choice, Date.now()).run();

        if (ins.meta.changes > 0) {
          const col = choice === 'HUMAN' ? 'votes_human' : 'votes_ai';
          await env.DB.prepare(`UPDATE rounds SET ${col} = ${col} + 1 WHERE no = ?`)
            .bind(no).run();
        }

        const after = await env.DB.prepare('SELECT * FROM rounds WHERE no = ?').bind(no).first();
        return json({ counted: ins.meta.changes > 0, ...strip(after) });
      }

      /* ------------------------------------------------------------- admin */
      if (path.startsWith('/api/admin/')) {
        if (req.headers.get('x-humanor-key') !== env.ADMIN_KEY)
          return json({ error: 'nope' }, 401);

        const body = await req.json();

        if (path.endsWith('/round')) {
          await env.DB.prepare(
            `INSERT INTO rounds (no, date, text, sha256) VALUES (?, ?, ?, ?)
             ON CONFLICT(no) DO UPDATE SET date=excluded.date, text=excluded.text,
             sha256=excluded.sha256`
          ).bind(body.no, body.date, body.text, body.sha256).run();
          return json({ ok: true });
        }

        if (path.endsWith('/publish')) {
          await env.DB.prepare('UPDATE rounds SET published = 1 WHERE no = ?')
            .bind(body.no).run();
          return json({ ok: true });
        }

        if (path.endsWith('/reveal')) {
          // The Worker verifies the seal itself before making it public.
          // A typo in the salt must never become a published lie.
          const r = await env.DB.prepare('SELECT sha256 FROM rounds WHERE no = ?')
            .bind(body.no).first();
          if (!r) return json({ error: 'no such round' }, 404);

          const msg = `${body.label}|round-${String(body.no).padStart(3, '0')}|${body.salt}`;
          const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(msg));
          const hash = [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
          if (hash !== r.sha256)
            return json({ error: 'seal does not match — refusing to reveal', computed: hash }, 409);

          await env.DB.prepare(
            'UPDATE rounds SET label=?, salt=?, source=?, revealed=1 WHERE no=?'
          ).bind(body.label, body.salt, body.source || null, body.no).run();
          return json({ ok: true, verified: true });
        }
      }

      return json({ error: 'not found' }, 404);
    } catch (e) {
      return json({ error: String(e) }, 500);
    }
  }
};
