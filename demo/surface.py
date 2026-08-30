"""Two destinations with the shape of the workflow that was recorded, served locally.

    uv run python -m demo.surface            serve both, until interrupted
    uv run python -m demo.surface --check    start, assert the shape, stop

WHY A LOCAL REPLICA AND NOT THE REAL SITE. The claim under test is the FACTORY, and a claim
you cannot re-run is not evidence. A live destination changes its markup, rate-limits, costs
credits per reveal and sends real mail to real people, so a demonstration recorded against
it can never be replayed to check whether the machine that read it was right. This one is
reproducible, costs nothing, and sends nowhere.

IT LIVES OUTSIDE `factory/` FOR A REASON. `evals/agnostic.py` fails the tree if any file
under `factory/` names a host, a selector or a product. A destination is exactly that, so
the only place a destination may be written down is a file the drivers cannot see.

WHAT IT IS BUILT TO EXERCISE, each of which is a machine that would otherwise be untested
against anything but a fixture asserting its own conclusion:

  * per-row controls that SHARE a role and name, so `Act.ambiguous` is derived from what a
    page offered rather than declared by a fixture
  * the same job reachable a second way, through a control that is alone on its page, so
    the ambiguity is a finding with a remedy rather than a dead end
  * a structured body behind every act, so `compile/mine.py` has a delta to derive a
    contract from and `witness/readers/fetched.py` has records to read
  * a second origin, so a surface is a thing acts are placed on rather than a single tab
  * a write the server answers with an id it minted, so `Contract.identifies` is non-empty
    and CONFIRMED can mean caused rather than merely present
  * one act nobody can undo, so `authority/permit.py` has something to ask about
"""

from __future__ import annotations

import json
import socket
import sys
import threading
import time
import urllib.request
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

PROSPECTS, TRACKER = 8801, 8802

#: The people the prospect list offers. Two share a title and a company, which is what makes
#: a search return a set rather than a hit, and what makes the per-row control ambiguous.
PEOPLE = [
    {"id": "p1", "name": "Vinayak Suthar", "title": "Category Head",
     "company": "Material Depot", "email": "vinayak@materialdepot.example"},
    {"id": "p2", "name": "Sanjay Raut", "title": "Category Head",
     "company": "Material Depot", "email": "sanjay@materialdepot.example"},
    {"id": "p3", "name": "Amrita Rao", "title": "Head of Supply",
     "company": "ODWEN", "email": "amrita@odwen.example"},
    {"id": "p4", "name": "Ketan Joshi", "title": "Ops Lead",
     "company": "zingbus", "email": "ketan@zingbus.example"},
]

STYLE = """
body{font:15px/1.5 system-ui,sans-serif;margin:0;background:#14161a;color:#e8eaed}
header{padding:14px 22px;border-bottom:1px solid #2a2e35;display:flex;gap:14px;
align-items:center}h1{font-size:15px;margin:0;font-weight:600;letter-spacing:.02em}
main{padding:22px}input,button,select{font:inherit;border-radius:7px;padding:8px 12px}
input{background:#1c1f25;border:1px solid #343a44;color:#e8eaed;min-width:230px}
button{background:#2b6cb0;border:1px solid #2b6cb0;color:#fff;cursor:pointer}
button.ghost{background:#1c1f25;border-color:#343a44;color:#cbd2da}
table{border-collapse:collapse;width:100%;margin-top:18px}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid #262a31;font-size:14px}
th{color:#8b94a0;font-weight:500;font-size:12px;letter-spacing:.06em;text-transform:uppercase}
.mail{color:#7ee2a8;font-family:ui-monospace,monospace;font-size:13px}
a{color:#8ab4f8}.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.note{color:#7c8593;font-size:13px;margin-top:16px;max-width:64ch}
"""


def page(title: str, body: str, script: str) -> bytes:
    return (f"<!doctype html><meta charset=utf-8><title>{title}</title>"
            f"<style>{STYLE}</style>{body}<script>{script}</script>").encode()


#: A control's accessible name comes from its text or its `aria-label`. Both destinations
#: below name every control the way the page itself would report it, because that is what
#: the recorder reads off the accessibility tree and what `locate` searches for on replay.
PROSPECT_BODY = """
<header><h1>Prospects</h1></header>
<main>
  <div class=row>
    <input id=q type=search aria-label="Search people" placeholder="job title">
    <button id=go>Search</button>
  </div>
  <table><thead><tr><th>Name<th>Title<th>Company<th>Email</tr></thead>
  <tbody id=rows></tbody></table>
  <p class=note>Every row offers a control named <b>Access email</b>. That is the shape
  that makes a demonstrated press unreplayable, and the reason each name is also a link to
  a page where the same control is alone.</p>
</main>
"""

PROSPECT_SCRIPT = """
const rows = document.getElementById('rows');
async function search() {
  const r = await fetch('/api/people?q=' + encodeURIComponent(document.getElementById('q').value));
  const found = (await r.json()).people;
  rows.innerHTML = '';
  for (const p of found) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td><a href="/person?id=${p.id}">${p.name}</a></td>` +
                   `<td>${p.title}</td><td>${p.company}</td>` +
                   `<td class="mail"></td>`;
    const cell = tr.lastElementChild;
    const shown = document.createElement('span');
    shown.id = 'm-' + p.id;
    const b = document.createElement('button');
    b.textContent = 'Access email';
    b.onclick = async () => {
      const got = await (await fetch('/api/reveal?id=' + p.id)).json();
      shown.textContent = got.person.email;
    };
    cell.appendChild(b);
    cell.appendChild(shown);
    rows.appendChild(tr);
  }
}
document.getElementById('go').onclick = search;
document.getElementById('q').addEventListener('keydown', e => { if (e.key === 'Enter') search(); });
"""


def person_page(person: dict[str, str]) -> bytes:
    """One person, with the reveal control alone on the page.

    THE SAME JOB, UNAMBIGUOUSLY. The table's control cannot be replayed and this one can,
    so the compiler's refusal points somewhere instead of only saying no.
    """
    body = (f"<header><h1>Prospects</h1></header><main>"
            f"<h2 style='font-size:20px;margin:0 0 4px'>{person['name']}</h2>"
            f"<p style='color:#8b94a0;margin:0 0 18px'>{person['title']} at "
            f"{person['company']}</p><div class=row>"
            f"<button id=reveal>Access email</button>"
            f"<span class=mail id=mail></span></div>"
            f"<p class=note><a href='/'>Back to the list</a></p></main>")
    script = ("document.getElementById('reveal').onclick = async () => {"
              f"const got = await (await fetch('/api/reveal?id={person['id']}')).json();"
              "document.getElementById('mail').textContent = got.person.email; };")
    return page("Prospect", body, script)


TRACKER_BODY = """
<header><h1>Outreach</h1></header>
<main>
  <div class=row>
    <input id=name aria-label="Name" placeholder="name">
    <input id=email aria-label="Email" placeholder="email">
    <button id=add>Add to outreach</button>
    <button id=send class=ghost>Send outreach</button>
  </div>
  <table><thead><tr><th>Ref<th>Name<th>Email<th>Status</tr></thead>
  <tbody id=rows></tbody></table>
  <p class=note>Adding writes to one endpoint and the table is re-read from another. The
  second is what a witness is allowed to believe: the act did not author it.</p>
</main>
"""

TRACKER_SCRIPT = """
async function load() {
  const got = await (await fetch('/api/rows')).json();
  document.getElementById('rows').innerHTML = got.rows.map(
    r => `<tr><td>${r.id}</td><td>${r.name}</td><td>${r.email}</td><td>${r.status}</td></tr>`
  ).join('');
}
document.getElementById('add').onclick = async () => {
  await fetch('/api/rows', {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name: document.getElementById('name').value,
                          email: document.getElementById('email').value})});
  await load();
};
document.getElementById('send').onclick = async () => {
  await fetch('/api/send', {method: 'POST'});
  await load();
};
load();
"""


class Rows:
    """What the tracker has been told, and the ids it minted for it.

    THE ID IS THE SERVER'S. A value that exists only because the write happened is what
    separates "a record with these values is there" from "this act put it there", and no
    reader can supply it -- only a destination that issues one.
    """

    def __init__(self) -> None:
        self._rows: list[dict[str, str]] = []
        self._lock = threading.Lock()

    def add(self, name: str, email: str) -> dict[str, str]:
        with self._lock:
            row = {"id": f"r-{len(self._rows) + 1}", "name": name, "email": email,
                   "status": "queued"}
            self._rows.append(row)
            return row

    def send(self) -> dict[str, Any]:
        with self._lock:
            queued = [r for r in self._rows if r["status"] == "queued"]
            for row in queued:
                row["status"] = "sent"
            return {"id": f"s-{int(time.time())}", "count": len(queued)}

    def all(self) -> list[dict[str, str]]:
        with self._lock:
            return [dict(row) for row in self._rows]

    def clear(self) -> None:
        with self._lock:
            self._rows.clear()


class Handler(BaseHTTPRequestHandler):
    """One handler for both destinations; `which` says which one it is serving."""

    protocol_version = "HTTP/1.1"

    def __init__(self, which: str, rows: Rows, *args: Any, **kwargs: Any) -> None:
        self.which, self.rows = which, rows
        super().__init__(*args, **kwargs)

    def log_message(self, *args: Any) -> None:
        """Quiet. The walk narrates; a request log underneath it is noise."""

    def _reply(self, body: bytes, kind: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: Any) -> None:
        self._reply(json.dumps(payload).encode(), "application/json")

    def do_GET(self) -> None:
        seen = urlparse(self.path)
        query = parse_qs(seen.query)
        if self.which == "prospects":
            if seen.path == "/":
                return self._reply(page("Prospects", PROSPECT_BODY, PROSPECT_SCRIPT),
                                   "text/html; charset=utf-8")
            if seen.path == "/person":
                found = next((p for p in PEOPLE if p["id"] == query.get("id", [""])[0]), None)
                return (self._reply(person_page(found), "text/html; charset=utf-8")
                        if found else self._missing())
            if seen.path == "/api/people":
                want = query.get("q", [""])[0].strip().lower()
                #: A SEARCH THAT NARROWS. Everything when nothing is asked for, so a
                #: demonstration that never typed still records a record set.
                found = [{k: v for k, v in p.items() if k != "email"} for p in PEOPLE
                         if not want or want in p["title"].lower()
                         or want in p["company"].lower()]
                return self._json({"query": want, "people": found})
            if seen.path == "/api/reveal":
                found = next((p for p in PEOPLE if p["id"] == query.get("id", [""])[0]), None)
                return self._json({"person": found}) if found else self._missing()
        else:
            if seen.path == "/":
                return self._reply(page("Outreach", TRACKER_BODY, TRACKER_SCRIPT),
                                   "text/html; charset=utf-8")
            if seen.path == "/api/rows":
                return self._json({"rows": self.rows.all()})
        self._missing()

    def do_POST(self) -> None:
        seen = urlparse(self.path)
        if self.which != "tracker":
            return self._missing()
        if seen.path == "/api/rows":
            length = int(self.headers.get("Content-Length") or 0)
            sent = json.loads(self.rfile.read(length) or b"{}")
            return self._json({"row": self.rows.add(str(sent.get("name", "")),
                                                    str(sent.get("email", "")))})
        if seen.path == "/api/send":
            return self._json({"sent": self.rows.send()})
        self._missing()

    def _missing(self) -> None:
        body = b"no such thing"
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class Serving:
    """Both destinations, up. Started on construction so a caller cannot forget to."""

    def __init__(self) -> None:
        self.rows = Rows()
        self._servers = [
            ThreadingHTTPServer(("127.0.0.1", PROSPECTS), partial(Handler, "prospects",
                                                                 self.rows)),
            ThreadingHTTPServer(("127.0.0.1", TRACKER), partial(Handler, "tracker",
                                                                self.rows)),
        ]
        for server in self._servers:
            threading.Thread(target=server.serve_forever, daemon=True).start()

    prospects = f"http://127.0.0.1:{PROSPECTS}"
    tracker = f"http://127.0.0.1:{TRACKER}"

    def stop(self) -> None:
        for server in self._servers:
            server.shutdown()
            server.server_close()

    def __enter__(self) -> Serving:
        return self

    def __exit__(self, *_: Any) -> None:
        self.stop()


def free(port: int) -> bool:
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def _get(url: str) -> tuple[int, str]:
    with urllib.request.urlopen(url, timeout=5) as answer:
        return answer.status, answer.read().decode()


def _post(url: str, payload: dict[str, str] | None) -> tuple[int, str]:
    data = json.dumps(payload).encode() if payload is not None else b""
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=5) as answer:
        return answer.status, answer.read().decode()


def _self_check() -> None:
    """The shape the walk depends on, asserted against the running server.

        uv run python -m demo.surface --check

    Every assertion here is one a station downstream would otherwise fail on for a reason
    that is not the factory's.
    """
    for port in (PROSPECTS, TRACKER):
        assert free(port), f"port {port} is taken; stop whatever holds it"

    with Serving() as up:
        status, body = _get(f"{up.prospects}/api/people?q=category%20head")
        found = json.loads(body)["people"]
        assert status == 200 and len(found) == 2, found
        assert all("email" not in p for p in found), "the list does not carry the email"

        #: THE AMBIGUITY IS IN THE DATA, not asserted by a fixture. Two rows agreeing on
        #: title and company is what puts two controls of the same name on one page.
        titles = [p["title"] for p in found]
        assert titles.count("Category Head") == 2, titles

        html = _get(f"{up.prospects}/")[1]
        assert "Access email" in PROSPECT_SCRIPT, "the table's control is named in the page"
        assert 'aria-label="Search people"' in html, html[:200]

        alone = _get(f"{up.prospects}/person?id=p1")[1]
        assert alone.count("Access email") == 1, "alone on its own page, exactly once"

        revealed = json.loads(_get(f"{up.prospects}/api/reveal?id=p1")[1])["person"]
        assert revealed["email"] == "vinayak@materialdepot.example", revealed

        #: THE WITNESS CHANNEL IS NOT THE ACTING CHANNEL. The write is a POST and the
        #: confirmation is a GET the page makes for itself afterwards.
        wrote = json.loads(_post(f"{up.tracker}/api/rows",
                                 {"name": "Vinayak Suthar",
                                  "email": revealed["email"]})[1])["row"]
        assert wrote["id"] == "r-1", wrote
        read_back = json.loads(_get(f"{up.tracker}/api/rows")[1])["rows"]
        assert read_back == [wrote], (read_back, wrote)
        assert wrote["status"] == "queued", "and nothing was sent by adding"

        sent = json.loads(_post(f"{up.tracker}/api/send", None)[1])["sent"]
        assert sent["count"] == 1, sent
        assert json.loads(_get(f"{up.tracker}/api/rows")[1])["rows"][0]["status"] == "sent"

        #: BOTH DIRECTIONS on the search: a query that matches nothing returns nothing,
        #: so a demonstration recording an empty result is distinguishable from one that
        #: never searched.
        none = json.loads(_get(f"{up.prospects}/api/people?q=zzzz")[1])["people"]
        assert none == [], none

    print(f"surface: {len(PEOPLE)} people on {Serving.prospects}, a tracker on "
          f"{Serving.tracker}; 2 controls share a name in the table and 1 is alone on "
          f"/person; a write is answered with an id and read back on another endpoint")


def main() -> int:
    if "--check" in sys.argv[1:]:
        _self_check()
        return 0
    with Serving() as up:
        print(f"prospects  {up.prospects}\ntracker    {up.tracker}\n\nctrl-c to stop")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print("\nstopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
