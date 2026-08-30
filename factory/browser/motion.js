// Pointer path geometry, from ghost-cursor. One long-lived process, JSON lines.
//
// A subprocess per move was the alternative and is the pattern this project has already
// measured as wrong. Requests arrive on stdin, one object per line:
//     {"id": 1, "from": [x, y], "to": [x, y]}
// and answers leave on stdout the same way:
//     {"id": 1, "points": [[x, y], ...]}
const readline = require('readline');
const { path } = require('ghost-cursor');

readline.createInterface({ input: process.stdin }).on('line', (line) => {
  if (!line.trim()) return;
  let asked;
  try {
    asked = JSON.parse(line);
    const points = path({ x: asked.from[0], y: asked.from[1] },
                        { x: asked.to[0], y: asked.to[1] });
    process.stdout.write(JSON.stringify({
      id: asked.id, points: points.map((p) => [p.x, p.y]),
    }) + '\n');
  } catch (err) {
    process.stdout.write(JSON.stringify({
      id: asked ? asked.id : null, error: String(err && err.message || err),
    }) + '\n');
  }
});
